from django import forms

from .models import Material


class MaterialImageForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ("image",)
        widgets = {
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
