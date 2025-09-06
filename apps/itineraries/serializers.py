from rest_framework import serializers
from apps.places.models import Place
from .models import Itinerary, ItineraryItem
from .utils import estimate_leg  # hàm ước tính quãng đường/thời gian/chi phí

def _ticket_of(place: Place) -> int:
    return int(getattr(place, "ticket_price", 0) or 0)

class ItineraryItemInSerializer(serializers.ModelSerializer):
    place = serializers.PrimaryKeyRelatedField(queryset=Place.objects.all())
    class Meta:
        model = ItineraryItem
        fields = ("place", "visit_start", "visit_end", "transport_mode", "order")

class ItineraryItemOutSerializer(serializers.ModelSerializer):
    place_name = serializers.CharField(source="place.name", read_only=True)
    class Meta:
        model = ItineraryItem
        fields = (
            "id","place","place_name","visit_start","visit_end",
            "transport_mode","order",
            "ticket_cost_vnd","leg_distance_m","leg_duration_s","leg_cost_vnd",
        )

class ItinerarySerializer(serializers.ModelSerializer):
    items = ItineraryItemInSerializer(many=True, write_only=True)
    items_detail = ItineraryItemOutSerializer(source="items", many=True, read_only=True)

    cost_breakdown = serializers.SerializerMethodField()
    transport_breakdown = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Itinerary
        fields = (
            "id","name","is_public",
            "total_cost","total_duration_s","share_code",
            "items","items_detail",
            "cost_breakdown","transport_breakdown","summary",
        )
        read_only_fields = ("total_cost","total_duration_s","share_code")

    def create(self, validated_data):
        # Sắp xếp theo 'order' để đảm bảo đúng thứ tự hành trình
        items_data = sorted(validated_data.pop("items", []), key=lambda x: x.get("order") or 0)
        user = self.context["request"].user
        it = Itinerary.objects.create(user=user, **validated_data)

        ticket_total = 0
        transport_total = 0
        duration_total = 0

        prev_coords = None  # (lat, lng) của điểm trước

        for idx, d in enumerate(items_data, start=1):
            place: Place = d["place"]
            mode_from_prev = (d.get("transport_mode") or "walk").lower().strip()

            item = ItineraryItem.objects.create(
                itinerary=it,
                place=place,
                visit_start=d["visit_start"],
                visit_end=d["visit_end"],
                transport_mode=mode_from_prev,  # NGỮ NGHĨA: mode áp dụng cho CHẶNG từ điểm trước -> điểm này
                order=d.get("order", 0),
            )

            # vé tham quan của chính điểm này
            item.ticket_cost_vnd = _ticket_of(place)
            ticket_total += item.ticket_cost_vnd

            # Tính chặng nếu TỪ điểm thứ 2 trở đi (điểm đầu không có chặng đi kèm)
            if prev_coords and place.latitude is not None and place.longitude is not None:
                leg = estimate_leg(prev_coords[0], prev_coords[1], place.latitude, place.longitude,
                                   mode=mode_from_prev)
                item.leg_distance_m = int(leg["distance_m"])
                item.leg_duration_s = int(leg["duration_s"])
                item.leg_cost_vnd   = int(leg["cost_vnd"])

                transport_total += item.leg_cost_vnd
                duration_total  += item.leg_duration_s
            else:
                # điểm đầu: không có quãng đường/chi phí di chuyển
                item.leg_distance_m = 0
                item.leg_duration_s = 0
                item.leg_cost_vnd   = 0

            item.save(update_fields=["ticket_cost_vnd","leg_distance_m","leg_duration_s","leg_cost_vnd"])
            prev_coords = (place.latitude, place.longitude)

        it.total_cost = int(ticket_total + transport_total)
        it.total_duration_s = int(duration_total)  # tổng thời gian DI CHUYỂN
        it.ensure_share_code()
        it.save(update_fields=["total_cost","total_duration_s","share_code"])
        return it

    # ======= helpers xuất ra UI =======

    def get_cost_breakdown(self, obj):
        return [
            {"place_id": i.place_id, "place_name": i.place.name, "ticket_cost_vnd": i.ticket_cost_vnd}
            for i in obj.items.all()
        ]

    def get_transport_breakdown(self, obj):
        """Mỗi hàng: chặng (prev -> current). Mode lấy từ 'current.transport_mode'."""
        rows = []
        items = list(obj.items.all().order_by("order", "id"))
        for idx in range(1, len(items)):
            prev = items[idx-1]
            curr = items[idx]
            rows.append({
                "from_place_id": prev.place_id, "from_place_name": prev.place.name,
                "to_place_id": curr.place_id,   "to_place_name": curr.place.name,
                "mode": (curr.transport_mode or "walk"),
                "distance_km": round(curr.leg_distance_m/1000.0, 3),
                "duration_min": round(curr.leg_duration_s/60.0, 1),
                "leg_cost_vnd": curr.leg_cost_vnd,
            })
        return rows

    def get_summary(self, obj):
        ticket_total = sum(i.ticket_cost_vnd for i in obj.items.all())
        transport_total = sum(i.leg_cost_vnd   for i in obj.items.all())
        return {
            "ticket_total_vnd": int(ticket_total),
            "transport_total_vnd": int(transport_total),
            "travel_duration_min": round(obj.total_duration_s/60.0, 1),
        }
