from django.contrib import admin

from .models import JobApplication, JobPost, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "user_type", "company_name")
    search_fields = ("display_name", "user__username", "company_name", "skills_set")
    list_filter = ("user_type",)


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ("title", "recruiter", "category", "number_of_openings", "created_at")
    search_fields = ("title", "category", "description", "skills_set")
    list_filter = ("category", "created_at")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "jobseeker", "created_at")
    search_fields = ("job__title", "jobseeker__username")

