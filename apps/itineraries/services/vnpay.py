# apps/itineraries/services/vnpay.py
import hmac
import hashlib
import urllib.parse
import datetime

from django.conf import settings
from django.utils import timezone


def _pairs(params: dict):
    """Trả về danh sách (k, v) đã sort key và loại None/''."""
    return [(k, params[k]) for k in sorted(params) if params[k] not in (None, "")]


def _build_query(params: dict) -> str:
    """Encode theo đúng cách VNPay mong muốn (quote_plus, sort key)."""
    return urllib.parse.urlencode(_pairs(params), doseq=True, quote_via=urllib.parse.quote_plus)


def _require_settings():
    if not settings.VNPAY_TMN_CODE or not settings.VNPAY_HASH_SECRET:
        raise RuntimeError("VNPay settings missing: VNPAY_TMN_CODE / VNPAY_HASH_SECRET")


def sign(params: dict) -> str:
    """
    Tính chữ ký HmacSHA512 trên *tập tham số đã sort*,
    BỎ QUA vnp_SecureHash & vnp_SecureHashType (theo tài liệu VNPay).
    """
    data = {
        k: v for k, v in params.items()
        if k not in ("vnp_SecureHash", "vnp_SecureHashType") and v not in (None, "")
    }
    raw = _build_query(data)
    key = (settings.VNPAY_HASH_SECRET or "").encode("utf-8")
    return hmac.new(key, raw.encode("utf-8"), hashlib.sha512).hexdigest()


def create_payment_url(amount_vnd: int, order_info: str, txn_ref: str, ip_addr: str,
                       order_type: str = "billpayment") -> str:
    """
    - amount_vnd: số tiền VND (>= 10.000). Hàm tự *100 theo chuẩn VNPay.
    - txn_ref: 8..34 ký tự, cần duy nhất mỗi giao dịch.
    """
    _require_settings()
    now = timezone.localtime()

    base = {
        "vnp_Version": settings.VNPAY_VERSION,
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_Amount": int(amount_vnd) * 100,
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": (txn_ref or "")[:34],
        "vnp_OrderInfo": (order_info or "")[:240],
        "vnp_OrderType": order_type or "billpayment",
        "vnp_Locale": "vn",
        "vnp_IpAddr": ip_addr or "127.0.0.1",
        "vnp_CreateDate": now.strftime("%Y%m%d%H%M%S"),
        "vnp_ExpireDate": (now + datetime.timedelta(minutes=15)).strftime("%Y%m%d%H%M%S"),
        "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
        # Nhiều lúc sandbox báo code=99 khi gửi IPN ngay lúc tạo payment -> có thể bật lại khi cần
        # "vnp_IpnUrl": settings.VNPAY_IPN_URL,
    }

    # 1) ký TRƯỚC (không có SecureHashType)
    secure = sign(base)

    # 2) thêm loại hash + chữ ký rồi build URL cuối
    base["vnp_SecureHashType"] = "HmacSHA512"
    base["vnp_SecureHash"] = secure
    return f"{settings.VNPAY_PAYMENT_URL}?{_build_query(base)}"


def verify_callback(query_params: dict) -> (bool, str):
    """
    Dùng ở trang return/IPN: so sánh chữ ký VNPay gửi về.
    """
    data = dict(query_params)
    # lấy SecureHash
    secure = data.pop("vnp_SecureHash", "") or data.pop("vnp_SecureHash", [""])
    if isinstance(secure, list):
        secure = secure[0]
    # bỏ SecureHashType khi tính lại
    data.pop("vnp_SecureHashType", None)
    calc = sign(data)
    ok = calc.lower() == str(secure).lower()
    return ok, ("OK" if ok else "INVALID_SIGNATURE")
