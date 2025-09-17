# apps/itineraries/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ItineraryViewSet
from .views_pay import (
    FundDetailView, FundCheckoutView,
    FundInvoiceCreateView, FundInvoicePayFromFundView, FundInvoiceCheckoutVNPayView,
    VNPayReturnView, VNPayIpnView,
)
from .views_auto_plan import AutoPlanFromRecoView

app_name = "itineraries"

router = DefaultRouter()
router.register("", ItineraryViewSet, basename="itinerary")

urlpatterns = [
    # ---- endpoints tuỳ chỉnh: đặt TRƯỚC router để không bị router “nuốt” ----
    path("auto-plan/", AutoPlanFromRecoView.as_view(), name="itinerary-auto-plan"),

    path("<int:pk>/fund/", FundDetailView.as_view(), name="fund-detail"),
    path("<int:pk>/fund/checkout/", FundCheckoutView.as_view(), name="fund-checkout"),

    path("<int:pk>/fund/invoices/", FundInvoiceCreateView.as_view(), name="fund-invoice-create"),
    path("<int:pk>/fund/invoices/<int:invoice_id>/pay-from-fund/",
         FundInvoicePayFromFundView.as_view(), name="fund-invoice-pay-fund"),
    path("<int:pk>/fund/invoices/<int:invoice_id>/checkout/",
         FundInvoiceCheckoutVNPayView.as_view(), name="fund-invoice-checkout"),

    path("payments/vnpay/return/", VNPayReturnView.as_view(), name="vnpay-return"),
    path("payments/vnpay/ipn/", VNPayIpnView.as_view(), name="vnpay-ipn"),

    # ---- router (list/create/retrieve/...) ----
    path("", include(router.urls)),
]
