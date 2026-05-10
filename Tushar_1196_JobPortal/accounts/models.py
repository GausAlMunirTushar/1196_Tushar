from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    JOB_SEEKER = "job_seeker"
    EMPLOYER = "employer"

    USER_TYPE_CHOICES = [
        (JOB_SEEKER, "Job Seeker"),
        (EMPLOYER, "Employer"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=150)
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default=JOB_SEEKER,
    )

    def __str__(self):
        return f"{self.display_name} ({self.get_user_type_display()})"

