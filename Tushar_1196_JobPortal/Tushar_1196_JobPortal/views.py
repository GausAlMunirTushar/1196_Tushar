import re

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import JobPostForm, LoginForm, ProfileForm, RegistrationForm
from .models import JobApplication, JobPost, UserProfile


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "display_name": user.get_username(),
            "user_type": UserProfile.JOB_SEEKER,
        },
    )
    return profile


def split_skills(value):
    return {
        skill.strip().lower()
        for skill in re.split(r"[,;\n]+", value or "")
        if skill.strip()
    }


def build_match(job, seeker_profile):
    job_skills = split_skills(job.skills_set)
    seeker_skills = split_skills(seeker_profile.skills_set)
    matched_skills = sorted(job_skills & seeker_skills)
    score = round((len(matched_skills) / len(job_skills)) * 100) if job_skills else 0

    return {
        "job": job,
        "seeker": seeker_profile,
        "score": score,
        "matched_skills": matched_skills,
    }


def csrf_failure(request, reason=""):
    messages.error(request, "Your form expired. Please reload the page and try again.")

    if request.path.startswith("/register"):
        return redirect("register")
    if request.path.startswith("/profile"):
        return redirect("profile")
    if request.path.startswith("/jobs/post"):
        return redirect("job_post")
    if request.path.startswith("/jobs/apply") or "/apply/" in request.path:
        return redirect("apply_jobs")
    if request.path.startswith("/matches"):
        return redirect("matches")
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


@never_cache
@ensure_csrf_cookie
def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("profile")
    else:
        form = RegistrationForm()

    return render(request, "jobportal/register.html", {"form": form})


@never_cache
@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Login successful.")
            return redirect("dashboard")
    else:
        form = LoginForm()

    return render(request, "jobportal/login.html", {"form": form})


@login_required
@never_cache
def dashboard_view(request):
    profile = get_or_create_profile(request.user)
    context = {
        "profile": profile,
        "jobs_count": JobPost.objects.filter(recruiter=request.user).count(),
        "applications_count": JobApplication.objects.filter(jobseeker=request.user).count(),
    }
    return render(request, "jobportal/dashboard.html", context)


@login_required
@never_cache
@ensure_csrf_cookie
def profile_view(request):
    profile = get_or_create_profile(request.user)

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
            user_type=profile.user_type,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Profile saved successfully.")
            return redirect("dashboard")
    else:
        form = ProfileForm(instance=profile, user_type=profile.user_type)

    return render(
        request,
        "jobportal/profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )


@login_required
@never_cache
@ensure_csrf_cookie
def job_post_view(request):
    profile = get_or_create_profile(request.user)
    if profile.user_type != UserProfile.RECRUITER:
        messages.error(request, "Only recruiters can post jobs.")
        return redirect("dashboard")

    if request.method == "POST":
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.save()
            messages.success(request, "Job posted successfully.")
            return redirect("matches")
    else:
        form = JobPostForm()

    return render(request, "jobportal/job_post.html", {"form": form, "profile": profile})


@login_required
@never_cache
@ensure_csrf_cookie
def job_apply_view(request):
    profile = get_or_create_profile(request.user)
    if profile.user_type != UserProfile.JOB_SEEKER:
        messages.error(request, "Only jobseekers can apply for jobs.")
        return redirect("dashboard")

    search_query = request.GET.get("q", "").strip()
    jobs = JobPost.objects.select_related("recruiter")

    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query)
            | Q(category__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(skills_set__icontains=search_query)
        )

    applied_job_ids = set(
        JobApplication.objects.filter(jobseeker=request.user).values_list("job_id", flat=True)
    )

    for job in jobs:
        job.already_applied = job.id in applied_job_ids

    return render(
        request,
        "jobportal/apply_jobs.html",
        {
            "jobs": jobs,
            "profile": profile,
            "search_query": search_query,
        },
    )


@login_required
@require_POST
def apply_to_job_view(request, job_id):
    profile = get_or_create_profile(request.user)
    if profile.user_type != UserProfile.JOB_SEEKER:
        messages.error(request, "Only jobseekers can apply for jobs.")
        return redirect("dashboard")

    job = get_object_or_404(JobPost, id=job_id)
    _, created = JobApplication.objects.get_or_create(job=job, jobseeker=request.user)

    if created:
        messages.success(request, "Application submitted successfully.")
    else:
        messages.info(request, "You have already applied for this job.")

    return redirect("apply_jobs")


@login_required
@never_cache
@ensure_csrf_cookie
def match_dashboard_view(request):
    profile = get_or_create_profile(request.user)

    if profile.user_type == UserProfile.RECRUITER:
        jobs = JobPost.objects.filter(recruiter=request.user)
        seekers = UserProfile.objects.filter(
            user_type=UserProfile.JOB_SEEKER,
        ).exclude(skills_set="").select_related("user")
        matches = []

        for job in jobs:
            for seeker in seekers:
                match = build_match(job, seeker)
                if match["score"] > 0:
                    matches.append(match)
    else:
        jobs = JobPost.objects.select_related("recruiter")
        applied_job_ids = set(
            JobApplication.objects.filter(jobseeker=request.user).values_list("job_id", flat=True)
        )
        matches = []

        for job in jobs:
            match = build_match(job, profile)
            match["already_applied"] = job.id in applied_job_ids
            if match["score"] > 0:
                matches.append(match)

    matches.sort(key=lambda item: item["score"], reverse=True)

    return render(
        request,
        "jobportal/matches.html",
        {
            "matches": matches,
            "profile": profile,
        },
    )


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")
