from django.contrib import admin

from .models import RequestHistory, SupplyRequest


@admin.register(SupplyRequest)
class SupplyRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "material", "employee", "quantity",
                    "created", "status")
    list_filter = ("status", "created")
    search_fields = ("material__name", "employee__name")
    list_select_related = ("material", "employee")


admin.site.register(RequestHistory)
