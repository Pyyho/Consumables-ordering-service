"""Формы списка и отдельных заявок."""

from django import forms
from django.utils import timezone

from inventory.models import Material
from staff.models import Employee

from .models import RequestStatus, SupplyRequest


SORT_OPTIONS = {
    "date": ("created", "По дате"),
    "newest": ("-created", "Сначала новые"),
    "material": ("material__name", "По материалу"),
    "employee": ("employee__name", "По сотруднику"),
    "status": ("status", "По статусу"),
}


class RequestFilterForm(forms.Form):
    q = forms.CharField(
        label="Поиск материала или сотрудника", required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    date = forms.DateField(
        label="Дата создания", required=False, input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "form-control"},
        ),
        error_messages={"invalid": "Введите дату в формате ГГГГ-ММ-ДД."},
    )
    material = forms.ModelChoiceField(
        label="Материал", queryset=Material.objects.all(), required=False,
        empty_label="Все материалы",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    employee = forms.ModelChoiceField(
        label="Сотрудник", queryset=Employee.objects.all(), required=False,
        empty_label="Все сотрудники",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    status = forms.ChoiceField(
        label="Статус", choices=[("", "Все статусы"), *RequestStatus.choices],
        required=False, widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={"invalid_choice": "Выберите допустимый статус."},
    )
    sort = forms.ChoiceField(
        label="Сортировка", required=False, initial="date",
        choices=[(key, value[1]) for key, value in SORT_OPTIONS.items()],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = data.copy()
            if data.get("sort") not in SORT_OPTIONS:
                data["sort"] = "date"
        super().__init__(data, *args, **kwargs)

    def clean_date(self):
        value = self.cleaned_data["date"]
        if value and value.isoformat() != self.data["date"].strip():
            raise forms.ValidationError("Введите дату в формате ГГГГ-ММ-ДД.")
        return value


class SupplyRequestForm(forms.ModelForm):
    class Meta:
        model = SupplyRequest
        fields = ("employee", "material", "quantity", "created")
        widgets = {
            "employee": forms.Select(attrs={"class": "form-select"}),
            "material": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "min": 1},
            ),
            "created": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"},
            ),
        }

    def clean_created(self):
        created = self.cleaned_data["created"]
        unchanged = self.instance.pk and created == self.instance.created
        if created < timezone.localdate() and not unchanged:
            raise forms.ValidationError("Дата заявки не может быть в прошлом.")
        return created

    def clean(self):
        data = super().clean()
        material = data.get("material")
        quantity = data.get("quantity")
        if material and quantity and not material.has_stock(quantity):
            self.add_error("quantity", "На складе недостаточно материала.")
        return data

    def save(self, commit=True):
        if not commit or self.instance.pk:
            return super().save(commit=commit)
        self.instance = SupplyRequest.create_for(**self.cleaned_data)
        return self.instance
