from django.contrib import admin

from supply_requests.admin import RelatedRequestsInline

from .models import Material


class MaterialRequestsInline(RelatedRequestsInline):
    fk_name = "material"


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "stock", "available")
    list_display_links = ("name",)
    list_editable = ("stock",)
    list_filter = ("unit", "in_stock")
    search_fields = ("name", "slug")
    readonly_fields = ("slug", "available")
    ordering = ("name", "pk")
    list_per_page = 20
    inlines = (MaterialRequestsInline,)

    @admin.display(boolean=True, description="В наличии", ordering="in_stock")
    def available(self, obj):
        return obj.in_stock if obj and obj.pk else None
