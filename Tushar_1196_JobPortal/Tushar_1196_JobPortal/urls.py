from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('jobs/post/', views.job_post_view, name='job_post'),
    path('jobs/apply/', views.job_apply_view, name='apply_jobs'),
    path('jobs/<int:job_id>/apply/', views.apply_to_job_view, name='apply_to_job'),
    path('matches/', views.match_dashboard_view, name='matches'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
