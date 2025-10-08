"""
worktable_system URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_admin(request):
    return redirect('admin:index')

# Override admin site settings
admin.site.site_header = "نظام إدارة الجداول التشغيلية"
admin.site.site_title = "إدارة الجداول"
admin.site.index_title = "لوحة التحكم"

# Override admin login URL
admin.site.login_url = '/login/'

def redirect_accounts_login(request):
    return redirect('/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', redirect_accounts_login, name='accounts_login'),
    path('', redirect_to_admin, name='home'),
    
    # Dashboard URLs - سيتم إنشاؤها لاحقاً
    # path('dashboard/', include('apps.dashboard.urls')),
    
    # Auth URLs are now handled by users app
    
    # Users URLs
    path('', include('apps.users.urls')),
    
    # Employees URLs
    path('employees/', include('apps.employees.urls')),
    
    # Branches URLs
    path('branches/', include('apps.branches.urls')),
    
    # Leaves URLs
    path('leaves/', include('apps.leaves.urls')),
    
    # Schedules URLs
    path('schedules/', include('apps.schedules.urls')),
    
    # Approvals URLs
    path('approvals/', include('apps.approvals.urls')),
    
    # Employees API URLs
    path('api/employees/', include('apps.employees.urls')),
    path('api/', include('apps.violations.urls')),
    path('api/', include('apps.reports.urls')),
    path('api/', include('apps.integrations.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
