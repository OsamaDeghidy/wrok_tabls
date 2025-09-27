from django.shortcuts import render
from django.http import HttpResponse

def IntegrationListView(request):
    # Mock data for integrations
    external_integrations = [
        {
            'name': 'نظام الموارد البشرية',
            'description': 'تكامل مع نظام إدارة الموارد البشرية',
            'icon': 'users',
            'color': 'primary',
            'status': 'active',
            'status_display': 'نشط',
            'status_color': 'success'
        },
        {
            'name': 'نظام الرواتب',
            'description': 'تكامل مع نظام إدارة الرواتب',
            'icon': 'money-bill-wave',
            'color': 'success',
            'status': 'active',
            'status_display': 'نشط',
            'status_color': 'success'
        },
        {
            'name': 'نظام الحضور',
            'description': 'تكامل مع نظام تسجيل الحضور والانصراف',
            'icon': 'clock',
            'color': 'info',
            'status': 'pending',
            'status_display': 'معلق',
            'status_color': 'warning'
        },
        {
            'name': 'نظام المحاسبة',
            'description': 'تكامل مع نظام المحاسبة المالية',
            'icon': 'calculator',
            'color': 'warning',
            'status': 'failed',
            'status_display': 'فاشل',
            'status_color': 'danger'
        }
    ]
    
    api_services = [
        {
            'name': 'API الموظفين',
            'description': 'خدمة API لإدارة بيانات الموظفين',
            'icon': 'api',
            'color': 'primary',
            'status': 'active',
            'status_display': 'نشط',
            'status_color': 'success'
        },
        {
            'name': 'API الجداول',
            'description': 'خدمة API لإدارة الجداول التشغيلية',
            'icon': 'calendar',
            'color': 'info',
            'status': 'active',
            'status_display': 'نشط',
            'status_color': 'success'
        },
        {
            'name': 'API التقارير',
            'description': 'خدمة API لاستخراج التقارير',
            'icon': 'chart-bar',
            'color': 'success',
            'status': 'pending',
            'status_display': 'معلق',
            'status_color': 'warning'
        }
    ]
    
    recent_activities = [
        {
            'id': 1,
            'type_display': 'استيراد',
            'icon': 'upload',
            'color': 'primary',
            'description': 'استيراد بيانات الموظفين من ملف Excel',
            'status': 'completed',
            'status_display': 'مكتمل',
            'status_color': 'success',
            'date': '2024-01-15 10:30',
            'duration': '2 دقيقة'
        },
        {
            'id': 2,
            'type_display': 'تصدير',
            'icon': 'download',
            'color': 'success',
            'description': 'تصدير تقرير الجداول التشغيلية',
            'status': 'completed',
            'status_display': 'مكتمل',
            'status_color': 'success',
            'date': '2024-01-15 09:15',
            'duration': '1 دقيقة'
        },
        {
            'id': 3,
            'type_display': 'مزامنة',
            'icon': 'sync',
            'color': 'info',
            'description': 'مزامنة بيانات الحضور مع نظام الرواتب',
            'status': 'failed',
            'status_display': 'فاشل',
            'status_color': 'danger',
            'date': '2024-01-15 08:45',
            'duration': '5 دقائق'
        },
        {
            'id': 4,
            'type_display': 'نسخ احتياطي',
            'icon': 'database',
            'color': 'warning',
            'description': 'إنشاء نسخة احتياطية من قاعدة البيانات',
            'status': 'running',
            'status_display': 'قيد التشغيل',
            'status_color': 'info',
            'date': '2024-01-15 08:00',
            'duration': 'جاري...'
        }
    ]
    
    context = {
        'external_integrations': external_integrations,
        'api_services': api_services,
        'recent_activities': recent_activities,
        'total_integrations': len(external_integrations) + len(api_services),
        'active_integrations': len([i for i in external_integrations + api_services if i['status'] == 'active']),
        'pending_integrations': len([i for i in external_integrations + api_services if i['status'] == 'pending']),
        'failed_integrations': len([i for i in external_integrations + api_services if i['status'] == 'failed'])
    }
    return render(request, 'integrations/list.html', context)

def ImportView(request):
    return HttpResponse("Import")

def ExportView(request):
    return HttpResponse("Export")

def JobListView(request):
    # Mock data for jobs
    jobs = [
        {
            'id': 1,
            'name': 'مزامنة بيانات الموظفين',
            'description': 'مزامنة بيانات الموظفين مع نظام الموارد البشرية',
            'type': 'sync',
            'type_display': 'مزامنة',
            'type_color': 'primary',
            'status': 'active',
            'status_display': 'نشط',
            'status_color': 'success',
            'schedule_display': 'كل ساعة',
            'last_run': '2024-01-15 10:30',
            'last_run_duration': '2 دقيقة',
            'next_run': '2024-01-15 11:30'
        },
        {
            'id': 2,
            'name': 'نسخ احتياطي يومي',
            'description': 'إنشاء نسخة احتياطية من قاعدة البيانات',
            'type': 'backup',
            'type_display': 'نسخ احتياطي',
            'type_color': 'warning',
            'status': 'active',
            'status_display': 'نشط',
            'status_color': 'success',
            'schedule_display': 'يومياً في 2:00 صباحاً',
            'last_run': '2024-01-15 02:00',
            'last_run_duration': '15 دقيقة',
            'next_run': '2024-01-16 02:00'
        },
        {
            'id': 3,
            'name': 'تقرير شهري',
            'description': 'إنشاء تقرير شهري شامل',
            'type': 'report',
            'type_display': 'تقرير',
            'type_color': 'info',
            'status': 'paused',
            'status_display': 'معلق',
            'status_color': 'warning',
            'schedule_display': 'شهرياً في اليوم الأول',
            'last_run': '2024-01-01 00:00',
            'last_run_duration': '30 دقيقة',
            'next_run': '2024-02-01 00:00'
        },
        {
            'id': 4,
            'name': 'تنظيف السجلات القديمة',
            'description': 'حذف السجلات القديمة من قاعدة البيانات',
            'type': 'maintenance',
            'type_display': 'صيانة',
            'type_color': 'secondary',
            'status': 'failed',
            'status_display': 'فاشل',
            'status_color': 'danger',
            'schedule_display': 'أسبوعياً',
            'last_run': '2024-01-14 03:00',
            'last_run_duration': '5 دقائق',
            'next_run': '2024-01-21 03:00'
        }
    ]
    
    job_history = [
        {
            'job_id': 1,
            'job_name': 'مزامنة بيانات الموظفين',
            'status': 'completed',
            'status_display': 'مكتمل',
            'status_color': 'success',
            'start_time': '2024-01-15 10:30',
            'end_time': '2024-01-15 10:32',
            'duration': '2 دقيقة',
            'records_processed': 150,
            'error_message': None
        },
        {
            'job_id': 2,
            'job_name': 'نسخ احتياطي يومي',
            'status': 'completed',
            'status_display': 'مكتمل',
            'status_color': 'success',
            'start_time': '2024-01-15 02:00',
            'end_time': '2024-01-15 02:15',
            'duration': '15 دقيقة',
            'records_processed': 5000,
            'error_message': None
        },
        {
            'job_id': 4,
            'job_name': 'تنظيف السجلات القديمة',
            'status': 'failed',
            'status_display': 'فاشل',
            'status_color': 'danger',
            'start_time': '2024-01-14 03:00',
            'end_time': '2024-01-14 03:05',
            'duration': '5 دقائق',
            'records_processed': 0,
            'error_message': 'خطأ في الاتصال بقاعدة البيانات'
        }
    ]
    
    context = {
        'jobs': jobs,
        'job_history': job_history,
        'total_jobs': len(jobs),
        'completed_jobs': len([j for j in jobs if j['status'] == 'active']),
        'running_jobs': 1,  # Currently running
        'failed_jobs': len([j for j in jobs if j['status'] == 'failed'])
    }
    return render(request, 'integrations/jobs.html', context)

def JobDetailView(request, pk):
    # Mock job data
    job = {
        'id': pk,
        'name': 'مزامنة بيانات الموظفين',
        'description': 'مزامنة بيانات الموظفين مع نظام الموارد البشرية الخارجي. تقوم هذه المهمة بجلب أحدث بيانات الموظفين وتحديثها في النظام المحلي.',
        'type': 'sync',
        'type_display': 'مزامنة',
        'type_color': 'primary',
        'status': 'active',
        'status_display': 'نشط',
        'status_color': 'success',
        'schedule_display': 'كل ساعة',
        'schedule_type': 'مكرر',
        'frequency': 'كل 60 دقيقة',
        'timezone': 'Asia/Riyadh',
        'max_retries': 3,
        'last_run': '2024-01-15 10:30',
        'last_run_duration': '2 دقيقة',
        'next_run': '2024-01-15 11:30',
        'configuration': '{\n  "source": "hr_system",\n  "endpoint": "/api/employees",\n  "method": "GET",\n  "headers": {\n    "Authorization": "Bearer token"\n  },\n  "mapping": {\n    "id": "employee_id",\n    "name": "full_name",\n    "email": "email_address"\n  }\n}',
        'total_executions': 150,
        'successful_executions': 145,
        'failed_executions': 5,
        'avg_duration': '2.5 دقيقة',
        'execution_history': [
            {
                'id': 1,
                'start_time': '2024-01-15 10:30',
                'end_time': '2024-01-15 10:32',
                'duration': '2 دقيقة',
                'status': 'completed',
                'status_display': 'مكتمل',
                'status_color': 'success',
                'records_processed': 150,
                'error_message': None
            },
            {
                'id': 2,
                'start_time': '2024-01-15 09:30',
                'end_time': '2024-01-15 09:32',
                'duration': '2 دقيقة',
                'status': 'completed',
                'status_display': 'مكتمل',
                'status_color': 'success',
                'records_processed': 148,
                'error_message': None
            },
            {
                'id': 3,
                'start_time': '2024-01-15 08:30',
                'end_time': '2024-01-15 08:35',
                'duration': '5 دقائق',
                'status': 'failed',
                'status_display': 'فاشل',
                'status_color': 'danger',
                'records_processed': 0,
                'error_message': 'خطأ في الاتصال بالخادم الخارجي'
            }
        ]
    }
    return render(request, 'integrations/job_detail.html', {'job': job})