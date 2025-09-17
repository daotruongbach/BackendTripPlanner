from django.db import models
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.places.models import Place

User = get_user_model()


class Itinerary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="itineraries")
    name = models.CharField(max_length=255)
    is_public = models.BooleanField(default=False)

    # tổng thời gian DI CHUYỂN (giây) & tổng chi phí (vé + di chuyển)
    total_duration_s = models.PositiveIntegerField(default=0)
    total_cost = models.PositiveIntegerField(default=0)

    share_code = models.CharField(max_length=16, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def ensure_share_code(self):
        if not self.share_code:
            self.share_code = get_random_string(12)

    def __str__(self):
        return f"{self.name} ({self.user})"


class ItineraryItem(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="items")
    place = models.ForeignKey(Place, on_delete=models.PROTECT)

    # chỉ lưu NGÀY tham quan
    visit_date = models.DateField(null=True, blank=True, db_index=True)

    transport_mode = models.CharField(max_length=16, default="walk")
    order = models.PositiveIntegerField(default=0, db_index=True)

    # breakdown
    ticket_cost_vnd = models.PositiveIntegerField(default=0)
    leg_distance_m = models.PositiveIntegerField(default=0)
    leg_duration_s = models.PositiveIntegerField(default=0)
    leg_cost_vnd = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("visit_date", "order", "id")

    def __str__(self):
        return f"{self.itinerary_id}#{self.order}: {self.place.name}"


# ==========================
# QUỸ LỊCH TRÌNH & THANH TOÁN
# ==========================

class ItineraryFund(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN"; CLOSED = "CLOSED"

    itinerary = models.OneToOneField(Itinerary, on_delete=models.CASCADE, related_name="fund")
    target_amount_vnd = models.PositiveBigIntegerField(default=0)         # mục tiêu góp trước chuyến đi
    contributed_amount_vnd = models.PositiveBigIntegerField(default=0)    # đã góp
    spent_amount_vnd = models.PositiveBigIntegerField(default=0)          # đã chi

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def balance_vnd(self):
        return max(0, int(self.contributed_amount_vnd) - int(self.spent_amount_vnd))

    @property
    def remaining_goal_vnd(self):
        return max(0, int(self.target_amount_vnd) - int(self.contributed_amount_vnd))

    def __str__(self):
        return f"Fund#{self.id} for Itinerary#{self.itinerary_id}"


class FundInvoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = "UNPAID"; PAID = "PAID"; CANCELED = "CANCELED"
    class PaySource(models.TextChoices):
        FUND = "FUND"; VNPAY = "VNPAY"

    fund = models.ForeignKey(ItineraryFund, on_delete=models.CASCADE, related_name="invoices")
    title = models.CharField(max_length=120)
    amount_vnd = models.PositiveBigIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)
    pay_source = models.CharField(max_length=10, choices=PaySource.choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["fund", "status"]), models.Index(fields=["created_at"])]

    def __str__(self):
        return f"Invoice#{self.id} {self.title} {self.amount_vnd}đ"


class FundPayout(models.Model):
    fund = models.ForeignKey(ItineraryFund, on_delete=models.CASCADE, related_name="payouts")
    invoice = models.OneToOneField(FundInvoice, on_delete=models.CASCADE, related_name="payout")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    amount_vnd = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["fund", "created_at"])]

    def __str__(self):
        return f"Payout#{self.id} {self.amount_vnd}đ for Invoice#{self.invoice_id}"


class FundContribution(models.Model):
    class Status(models.TextChoices):
        PENDING="PENDING"; PAID="PAID"; FAILED="FAILED"; CANCELED="CANCELED"
    class Purpose(models.TextChoices):
        TOPUP = "TOPUP"      # góp quỹ trước chuyến đi
        INVOICE = "INVOICE"  # góp cho đúng hóa đơn

    fund = models.ForeignKey(ItineraryFund, on_delete=models.CASCADE, related_name="contributions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fund_contributions")
    amount_vnd = models.PositiveBigIntegerField()
    purpose = models.CharField(max_length=10, choices=Purpose.choices, default=Purpose.TOPUP)
    invoice = models.ForeignKey(FundInvoice, null=True, blank=True, on_delete=models.SET_NULL, related_name="contributions")

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # VNPay
    vnp_txn_ref = models.CharField(max_length=64, unique=True, db_index=True)
    vnp_bank_code = models.CharField(max_length=32, null=True, blank=True)
    vnp_order_info = models.CharField(max_length=255, null=True, blank=True)
    vnp_transaction_no = models.CharField(max_length=64, null=True, blank=True)
    vnp_pay_date = models.CharField(max_length=20, null=True, blank=True)
    vnp_secure_hash = models.CharField(max_length=128, null=True, blank=True)
    vnp_raw = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["fund", "status"]),
            models.Index(fields=["purpose", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def mark_paid(self, secure_hash=None, raw=None):
        if self.status == self.Status.PAID:
            return
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        if secure_hash:
            self.vnp_secure_hash = secure_hash
        if raw is not None:
            self.vnp_raw = raw
        self.save(update_fields=["status", "paid_at", "vnp_secure_hash", "vnp_raw"])

        # 1) cộng tiền vào quỹ
        f = self.fund
        f.contributed_amount_vnd = int(f.contributed_amount_vnd) + int(self.amount_vnd)

        # 2) nếu là góp cho hóa đơn -> tự động trừ hóa đơn
        if self.purpose == self.Purpose.INVOICE and self.invoice and self.invoice.status != FundInvoice.Status.PAID:
            payout_amount = int(self.invoice.amount_vnd)
            FundPayout.objects.create(fund=f, invoice=self.invoice, user=self.user, amount_vnd=payout_amount)
            f.spent_amount_vnd = int(f.spent_amount_vnd) + payout_amount
            self.invoice.status = FundInvoice.Status.PAID
            self.invoice.pay_source = FundInvoice.PaySource.VNPAY
            self.invoice.paid_at = timezone.now()
            self.invoice.save(update_fields=["status", "pay_source", "paid_at"])

        # 3) đóng quỹ nếu đạt mục tiêu
        if f.contributed_amount_vnd >= f.target_amount_vnd:
            f.status = ItineraryFund.Status.CLOSED
        f.save(update_fields=["contributed_amount_vnd", "spent_amount_vnd", "status"])