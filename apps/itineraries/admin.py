from django.contrib import admin
from .models import ItineraryFund, FundContribution, FundInvoice, FundPayout

@admin.register(ItineraryFund)
class ItineraryFundAdmin(admin.ModelAdmin):
    list_display = ("id", "itinerary", "target_amount_vnd", "contributed_amount_vnd", "spent_amount_vnd", "status", "created_at")
    search_fields = ("itinerary__name",)

@admin.register(FundContribution)
class FundContributionAdmin(admin.ModelAdmin):
    list_display = ("id", "fund", "user", "amount_vnd", "purpose", "status", "vnp_txn_ref", "paid_at")
    list_filter = ("purpose", "status")
    search_fields = ("vnp_txn_ref", "user__username")

@admin.register(FundInvoice)
class FundInvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "fund", "title", "amount_vnd", "status", "pay_source", "created_at", "paid_at")
    list_filter = ("status", "pay_source")

@admin.register(FundPayout)
class FundPayoutAdmin(admin.ModelAdmin):
    list_display = ("id", "fund", "invoice", "user", "amount_vnd", "created_at")
