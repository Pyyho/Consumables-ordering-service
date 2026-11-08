from django.contrib import admin

from supply_requests.admin import RelatedRequestsInline

from .models import Employee


class EmployeeRequestsInline(RelatedRequestsInline):
    fk_name = "employee"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "email")
    search_fields = ("name", "email", "department")
    list_filter = ("department",)
    ordering = ("department", "name", "pk")
    list_per_page = 20
    inlines = (EmployeeRequestsInline,)
