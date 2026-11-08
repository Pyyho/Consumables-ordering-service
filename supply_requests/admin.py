from django import forms
from django.contrib import admin, messages
from django.db import transaction

from .models import RequestHistory, SupplyRequest


class RelatedRequestsInline(admin.TabularInline):
    model = SupplyRequest
    fields = ("id", "material", "employee", "quantity", "created", "status")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).with_details()

    def has_add_permission(self, request, obj=None):
        return False


class SupplyRequestForm(forms.ModelForm):
    class Meta:
        model = SupplyRequest
        fields = "__all__"

    def clean(self):
        data = super().clean()
        material = data.get("material")
        quantity = data.get("quantity")
        updates_stock_check = (
            not self.instance.pk
            or {"material", "quantity"}.intersection(self.changed_data)
        )
        if material and quantity and updates_stock_check:
            if not material.has_stock(quantity):
                self.add_error("quantity", "На складе недостаточно материала.")
        return data


@admin.register(SupplyRequest)
class SupplyRequestAdmin(admin.ModelAdmin):
    form = SupplyRequestForm
    list_display = ("id", "material", "employee", "quantity",
                    "created", "status")
    list_display_links = ("id", "material")
    list_filter = ("status", "created", "material", "employee")
    search_fields = ("material__name", "employee__name", "employee__email")
    list_select_related = ("material", "employee")
    autocomplete_fields = ("material", "employee")
    date_hierarchy = "created"
    ordering = ("-created", "-pk")
    list_per_page = 20
    actions = ("cancel_selected",)

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            obj.status_events.create(position=0, status=obj.status)
            return

        # The admin change form wraps this operation in a transaction.
        status = obj.status
        obj.status = SupplyRequest.objects.select_for_update().get(
            pk=obj.pk
        ).status
        super().save_model(request, obj, form, change)
        if "status" in form.changed_data:
            obj.change_status(status)

    @admin.action(description="Отменить выбранные активные заявки",
                  permissions=["change"])
    @transaction.atomic
    def cancel_selected(self, request, queryset):
        count = 0
        for item in queryset.active().select_for_update():
            item.cancel()
            self.log_change(request, item, "Массовая отмена заявки.")
            count += 1
        self.message_user(
            request, f"Отменено заявок: {count}.", messages.SUCCESS
        )


@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ("request", "position", "status")
    list_select_related = ("request", "request__material")
    list_filter = ("status",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
