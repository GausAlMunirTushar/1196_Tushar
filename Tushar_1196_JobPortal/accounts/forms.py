from django import forms
from django.contrib.auth import authenticate, get_user_model

from .models import UserProfile


User = get_user_model()


class RegistrationForm(forms.ModelForm):
    display_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    user_type = forms.ChoiceField(choices=UserProfile.USER_TYPE_CHOICES)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "display_name", "email", "password", "confirm_password", "user_type"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "Enter username",
            "display_name": "Enter display name",
            "email": "Enter email address",
            "password": "Enter password",
            "confirm_password": "Confirm password",
        }

        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-select" if field_name == "user_type" else "form-control"
            if field_name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[field_name]

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        display_name = self.cleaned_data["display_name"]
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])

        if hasattr(user, "first_name"):
            user.first_name = display_name

        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                display_name=display_name,
                user_type=self.cleaned_data["user_type"],
            )

        return user


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter password"}
        )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            self.user = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user is None:
                raise forms.ValidationError("Invalid username or password.")

        return cleaned_data

    def get_user(self):
        return getattr(self, "user", None)
