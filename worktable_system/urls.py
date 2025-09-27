"""
worktable_system URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_dashboard(request):
    return redirect('dashboard:index')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_dashboard, name='home'),
    
    # Dashboard URLs
    path('dashboard/', include('apps.dashboard.urls')),
    
    # Auth URLs are now handled by users app
    
    # API URLs
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.employees.urls')),
    path('api/', include('apps.branches.urls')),
    path('api/', include('apps.schedules.urls')),
    path('api/', include('apps.leaves.urls')),
    path('api/', include('apps.approvals.urls')),
    path('api/', include('apps.violations.urls')),
    path('api/', include('apps.reports.urls')),
    path('api/', include('apps.integrations.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
