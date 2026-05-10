from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    RECRUITER = "recruiter"
    JOB_SEEKER = "job_seeker"

    USER_TYPE_CHOICES = [
        (RECRUITER, "Recruiter"),
        (JOB_SEEKER, "Job Seeker"),
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
    company_name = models.CharField(max_length=150, blank=True)
    company_information = models.TextField(blank=True)
    skills_set = models.TextField(blank=True)
    resume = models.FileField(upload_to="resumes/", blank=True, null=True)

    def __str__(self):
        return f"{self.display_name} ({self.get_user_type_display()})"


class JobPost(models.Model):
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_posts",
    )
    title = models.CharField(max_length=200)
    number_of_openings = models.PositiveIntegerField()
    category = models.CharField(max_length=120)
    description = models.TextField()
    skills_set = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    job = models.ForeignKey(
        JobPost,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    jobseeker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "jobseeker")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.jobseeker} applied for {self.job}"

