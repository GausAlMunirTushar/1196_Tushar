from django import forms
from django.contrib.auth import authenticate, get_user_model

from .models import JobPost, UserProfile


User = get_user_model()


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class RegistrationForm(BootstrapFormMixin, forms.ModelForm):
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
        self.apply_bootstrap()
        placeholders = {
            "username": "Enter username",
            "display_name": "Enter display name",
            "email": "Enter email address",
            "password": "Enter password",
            "confirm_password": "Confirm password",
        }

        for field_name, field in self.fields.items():
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


class LoginForm(BootstrapFormMixin, forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

        self.fields["username"].widget.attrs.update({"placeholder": "Enter username"})
        self.fields["password"].widget.attrs.update({"placeholder": "Enter password"})

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


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "display_name",
            "company_name",
            "company_information",
            "skills_set",
            "resume",
        ]
        widgets = {
            "company_information": forms.Textarea(attrs={"rows": 4}),
            "skills_set": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "skills_set": "Skills set",
        }

    def __init__(self, *args, **kwargs):
        user_type = kwargs.pop("user_type", None)
        super().__init__(*args, **kwargs)

        if user_type == UserProfile.RECRUITER:
            self.fields.pop("skills_set")
            self.fields.pop("resume")
        else:
            self.fields.pop("company_name")
            self.fields.pop("company_information")

        self.apply_bootstrap()
        if "resume" in self.fields:
            self.fields["resume"].widget.attrs["accept"] = ".pdf,.doc,.docx"


class JobPostForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = JobPost
        fields = [
            "title",
            "number_of_openings",
            "category",
            "description",
            "skills_set",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "skills_set": forms.Textarea(attrs={"rows": 3}),
            "number_of_openings": forms.NumberInput(attrs={"min": 1}),
        }
        labels = {
            "number_of_openings": "Number of openings",
            "skills_set": "Skills set",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

