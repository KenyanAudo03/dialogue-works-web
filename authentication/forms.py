from django import forms
from django.contrib.auth.hashers import make_password
from .models import UserProfile


class RegistrationStepOneForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "password", "id": "password"})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "confirm_password", "id": "confirm_password"}
        )
    )

    class Meta:
        model = UserProfile
        fields = [
            "first_name",
            "last_name",
            "email",
            "course",
            "reg_number",
            "phone_number",
            "password",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "first_name", "id": "first_name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "last_name", "id": "last_name"}
            ),
            "email": forms.EmailInput(attrs={"class": "email", "id": "email"}),
            "course": forms.TextInput(attrs={"class": "course", "id": "course"}),
            "reg_number": forms.TextInput(
                attrs={"class": "reg_number", "id": "reg_number"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "phone_number", "id": "phone_number"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        return cleaned_data


class PhoneVerificationForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone_number"]
