import uuid
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import (
    Itinerary, ItineraryFund, FundContribution, FundInvoice, FundPayout
)
from .services.vnpay import create_payment_url, verify_callback


def _client_ip(request):
    return request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0] or request.META.get("REMOTE_ADDR", "")


# -------- TÓM TẮT QUỸ (lấy % đã góp) --------
class FundDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        iti = get_object_or_404(Itinerary, pk=pk)
        fund, _ = ItineraryFund.objects.get_or_create(
            itinerary=iti, defaults={"target_amount_vnd": int(getattr(iti, "total_cost", 0) or 0)}
        )
        target = int(fund.target_amount_vnd) or 1
        percent = round(min(100.0, 100.0 * float(fund.contributed_amount_vnd) / float(target)), 2)
        return Response({
            "itinerary_id": iti.id,
            "target": int(fund.target_amount_vnd),
            "contributed": int(fund.contributed_amount_vnd),
            "spent": int(fund.spent_amount_vnd),
            "balance": int(fund.balance_vnd),
            "remaining_goal": int(fund.remaining_goal_vnd),
            "status": fund.status,
            "percent": percent
        })


# -------- TOPUP: góp quỹ trước chuyến đi (VNPay) --------
class FundCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        iti = get_object_or_404(Itinerary, pk=pk)
        fund, _ = ItineraryFund.objects.get_or_create(
            itinerary=iti, defaults={"target_amount_vnd": int(getattr(iti, "total_cost", 0) or 0)}
        )
        try:
            amount = int(request.data.get("amount_vnd"))
        except Exception:
            return Response({"detail": "amount_vnd không hợp lệ"}, status=400)
        if amount <= 0:
            return Response({"detail": "Số tiền phải > 0"}, status=400)
        if amount > fund.remaining_goal_vnd:
            return Response({"detail": f"Tối đa {fund.remaining_goal_vnd}đ để đạt mục tiêu"}, status=400)

        txn_ref = f"TOP-{uuid.uuid4().hex[:16].upper()}"
        contrib = FundContribution.objects.create(
            fund=fund, user=request.user, amount_vnd=amount,
            purpose=FundContribution.Purpose.TOPUP, vnp_txn_ref=txn_ref
        )
        pay_url = create_payment_url(amount, f"Gop quy TOPUP itin#{iti.id}", txn_ref, _client_ip(request), "topup")
        return Response({"pay_url": pay_url, "txn_ref": txn_ref, "contribution_id": contrib.id})


# -------- INVOICE: tạo hóa đơn tại điểm đến --------
class FundInvoiceCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        iti = get_object_or_404(Itinerary, pk=pk)
        fund, _ = ItineraryFund.objects.get_or_create(
            itinerary=iti, defaults={"target_amount_vnd": int(getattr(iti, "total_cost", 0) or 0)}
        )
        title = (request.data.get("title") or "Chi phí").strip()
        try:
            amount = int(request.data.get("amount_vnd"))
        except Exception:
            return Response({"detail": "amount_vnd không hợp lệ"}, status=400)
        if amount <= 0:
            return Response({"detail": "Số tiền phải > 0"}, status=400)
        inv = FundInvoice.objects.create(fund=fund, title=title, amount_vnd=amount)
        return Response({"invoice_id": inv.id, "title": inv.title, "amount_vnd": inv.amount_vnd, "status": inv.status})


# -------- Trả hóa đơn bằng số dư quỹ --------
class FundInvoicePayFromFundView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, invoice_id):
        inv = get_object_or_404(FundInvoice, pk=invoice_id, fund__itinerary_id=pk)
        fund = inv.fund
        if inv.status != FundInvoice.Status.UNPAID:
            return Response({"detail": "Hóa đơn đã xử lý"}, status=400)
        if fund.balance_vnd < inv.amount_vnd:
            return Response({"detail": f"Số dư không đủ. Thiếu {inv.amount_vnd - fund.balance_vnd}đ"}, status=400)
        FundPayout.objects.create(fund=fund, invoice=inv, user=request.user, amount_vnd=int(inv.amount_vnd))
        fund.spent_amount_vnd = int(fund.spent_amount_vnd) + int(inv.amount_vnd)
        fund.save(update_fields=["spent_amount_vnd"])
        inv.status = FundInvoice.Status.PAID
        inv.pay_source = FundInvoice.PaySource.FUND
        inv.paid_at = timezone.now()
        inv.save(update_fields=["status", "pay_source", "paid_at"])
        return Response({"success": True, "message": "Đã trừ từ quỹ", "balance": int(fund.balance_vnd)})


# -------- Thiếu tiền -> checkout VNPay đúng số còn thiếu (hoặc full) --------
class FundInvoiceCheckoutVNPayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, invoice_id):
        inv = get_object_or_404(FundInvoice, pk=invoice_id, fund__itinerary_id=pk)
        if inv.status != FundInvoice.Status.UNPAID:
            return Response({"detail": "Hóa đơn đã xử lý"}, status=400)
        fund = inv.fund
        amount = int(inv.amount_vnd - fund.balance_vnd) if fund.balance_vnd < inv.amount_vnd else 0
        if str(request.data.get("full")) == "1":
            amount = int(inv.amount_vnd)
        if amount <= 0:
            return Response({"detail": "Số dư đã đủ, hãy dùng pay-from-fund"}, status=400)
        txn_ref = f"INV-{inv.id}-{uuid.uuid4().hex[:8].upper()}"
        contrib = FundContribution.objects.create(
            fund=fund, user=request.user, amount_vnd=amount,
            purpose=FundContribution.Purpose.INVOICE, invoice=inv, vnp_txn_ref=txn_ref
        )
        pay_url = create_payment_url(amount, f"Thanh toan INVOICE#{inv.id} itin#{pk}", txn_ref, _client_ip(request), "billpayment")
        return Response({"pay_url": pay_url, "txn_ref": txn_ref, "contribution_id": contrib.id, "invoice_id": inv.id})


# -------- RETURN & IPN --------
class VNPayReturnView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        valid, _ = verify_callback(request.GET)
        ref = request.GET.get("vnp_TxnRef")
        ok = (request.GET.get("vnp_ResponseCode") == "00" or request.GET.get("vnp_TransactionStatus") == "00")
        if not ref:
            return Response({"success": False, "message": "Thiếu mã giao dịch"}, status=400)
        try:
            c = FundContribution.objects.select_related("fund", "invoice").get(vnp_txn_ref=ref)
        except FundContribution.DoesNotExist:
            return Response({"success": False, "message": "Không tìm thấy giao dịch"}, status=404)
        if valid and ok:
            if c.status != FundContribution.Status.PAID:
                c.vnp_bank_code = request.GET.get("vnp_BankCode")
                c.vnp_order_info = request.GET.get("vnp_OrderInfo")
                c.vnp_transaction_no = request.GET.get("vnp_TransactionNo")
                c.vnp_pay_date = request.GET.get("vnp_PayDate")
                c.mark_paid(secure_hash=request.GET.get("vnp_SecureHash"), raw=dict(request.GET))
            return Response({"success": True, "message": "Thanh toán thành công", "purpose": c.purpose, "invoice_id": c.invoice_id})
        return Response({"success": False, "message": "Thanh toán thất bại hoặc chữ ký sai"}, status=400)


class VNPayIpnView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        valid, _ = verify_callback(request.GET)
        ref = request.GET.get("vnp_TxnRef")
        if not (valid and ref):
            return Response({"RspCode": "97", "Message": "Invalid signature or TxnRef"}, status=200)
        try:
            c = FundContribution.objects.select_related("fund", "invoice").get(vnp_txn_ref=ref)
        except FundContribution.DoesNotExist:
            return Response({"RspCode": "01", "Message": "Order not found"}, status=200)
        if int(request.GET.get("vnp_Amount", "0")) != int(c.amount_vnd) * 100:
            return Response({"RspCode": "04", "Message": "Invalid amount"}, status=200)
        if request.GET.get("vnp_TransactionStatus") == "00":
            if c.status != FundContribution.Status.PAID:
                c.vnp_bank_code = request.GET.get("vnp_BankCode")
                c.vnp_order_info = request.GET.get("vnp_OrderInfo")
                c.vnp_transaction_no = request.GET.get("vnp_TransactionNo")
                c.vnp_pay_date = request.GET.get("vnp_PayDate")
                c.mark_paid(secure_hash=request.GET.get("vnp_SecureHash"), raw=dict(request.GET))
            return Response({"RspCode": "00", "Message": "Confirm Success"}, status=200)
        else:
            c.status = FundContribution.Status.FAILED
            c.vnp_raw = dict(request.GET)
            c.save(update_fields=["status", "vnp_raw"])
            return Response({"RspCode": "00", "Message": "Confirm Failed"}, status=200)