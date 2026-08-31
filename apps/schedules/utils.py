"""
Utility functions for schedules app
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


def send_schedule_approval_emails(schedule):
    """
    إرسال إشعار بريد إلكتروني لكل موظف مدرج في الجدول بعد اعتماده نهائياً
    مع ملخص لوردياته وساعات عمله المعتمدة.
    """
    try:
        entries = schedule.entries.select_related('employee', 'shift').order_by('date', 'start_time')
        unique_employee_ids = entries.values_list('employee_id', flat=True).distinct()
        
        if not unique_employee_ids:
            logger.info(f"Schedule {schedule.id} has no employees to notify.")
            return

        from django.contrib.auth.models import User
        from apps.notifications.models import Notification
        from django.urls import reverse

        employees = User.objects.filter(id__in=unique_employee_ids).select_related('profile')
        schedule_url = reverse('schedules:detail', kwargs={'schedule_id': schedule.id})

        for employee in employees:
            emp_entries = [e for e in entries if e.employee_id == employee.id]
            total_hours = sum(float(e.hours) for e in emp_entries)
            
            # 1. إنشاء إشعار داخل البرنامج في "تنبيهاتي"
            try:
                Notification.objects.create(
                    recipient=employee,
                    title=f"اعتماد الجدول التشغيلي - فرع {schedule.branch.name}",
                    message=f"تم اعتماد جدول العمل للفترة من {schedule.start_date} إلى {schedule.end_date}. إجمالي ساعاتك المعتمدة: {total_hours:.1f} ساعة عبر {len(emp_entries)} يوم عمل.",
                    link=schedule_url,
                    is_read=False
                )
                logger.info(f"Created in-app notification for {employee.username}")
            except Exception as notif_err:
                logger.error(f"Error creating in-app notification for {employee.username}: {notif_err}")

            # 2. إرسال بريد إلكتروني إذا كان البريد متاحاً
            if not employee.email:
                logger.warning(f"Employee {employee.username} (ID: {employee.id}) has no email address.")
                continue

            subject = f"اعتماد الجدول التشغيلي - فرع {schedule.branch.name} ({schedule.start_date} إلى {schedule.end_date})"
            
            # بناء محتوى HTML للبريد
            shifts_html_rows = ""
            for entry in emp_entries:
                day_name = entry.date.strftime('%A')
                arabic_days = {
                    'Monday': 'الإثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء',
                    'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'
                }
                ar_day = arabic_days.get(day_name, day_name)
                
                shifts_html_rows += f"""
                <tr style="border-bottom: 1px solid #e0e0e0;">
                    <td style="padding: 8px; text-align: center;">{entry.date.strftime('%Y-%m-%d')}</td>
                    <td style="padding: 8px; text-align: center;">{ar_day}</td>
                    <td style="padding: 8px; text-align: center;">{entry.shift.name if entry.shift else '-'}</td>
                    <td style="padding: 8px; text-align: center;">{entry.start_time.strftime('%H:%M') if entry.start_time else '-'}</td>
                    <td style="padding: 8px; text-align: center;">{entry.end_time.strftime('%H:%M') if entry.end_time else '-'}</td>
                    <td style="padding: 8px; text-align: center; font-weight: bold;">{entry.hours} س</td>
                </tr>
                """

            html_content = f"""
            <div dir="rtl" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; max-width: 650px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #0d6efd; color: #ffffff; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">نظام الجداول التشغيلية - الخزف السعودي</h2>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">إشعار اعتماد جدول العمل</p>
                </div>
                <div style="padding: 25px;">
                    <p>مرحباً <strong>{employee.get_full_name() or employee.username}</strong>،</p>
                    <p>نود إعلامك بأنه تم <strong>اعتماد الجدول التشغيلي النهائي</strong> لفرع <strong>{schedule.branch.name}</strong> للفترة من <strong>{schedule.start_date}</strong> إلى <strong>{schedule.end_date}</strong>.</p>
                    
                    <div style="background-color: #f8f9fa; border-radius: 6px; padding: 15px; margin: 20px 0;">
                        <h4 style="margin-top: 0; color: #0d6efd;">ملخص ساعات العمل المعتمدة:</h4>
                        <ul style="list-style: none; padding-right: 0; margin-bottom: 0;">
                            <li><strong>إجمالي الساعات المجدولة:</strong> {total_hours:.1f} ساعة</li>
                            <li><strong>عدد أيام العمل:</strong> {len(emp_entries)} يوم</li>
                            <li><strong>حالة الجدول:</strong> <span style="color: #198754; font-weight: bold;">معتمد نهائياً</span></li>
                        </ul>
                    </div>

                    <h4 style="color: #333; margin-bottom: 10px;">جدول الورديات والشفتات الخاصة بك:</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px;">
                        <thead>
                            <tr style="background-color: #0d6efd; color: #ffffff;">
                                <th style="padding: 8px;">التاريخ</th>
                                <th style="padding: 8px;">اليوم</th>
                                <th style="padding: 8px;">الشفت</th>
                                <th style="padding: 8px;">الحضور</th>
                                <th style="padding: 8px;">الانصراف</th>
                                <th style="padding: 8px;">الساعات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {shifts_html_rows}
                        </tbody>
                    </table>

                    <p style="font-size: 13px; color: #6c757d;">يرجى الالتزام بمواعيد الحضور والانصراف المحددة أعلاه.</p>
                </div>
                <div style="background-color: #f1f5f9; padding: 15px; text-align: center; font-size: 12px; color: #64748b;">
                    تم إرسال هذا البريد تلقائياً من نظام الجداول التشغيلية.
                </div>
            </div>
            """

            text_content = strip_tags(html_content)
            
            try:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@worktable.com'),
                    to=[employee.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=True)
                logger.info(f"Sent schedule approval email to {employee.email}")
            except Exception as mail_err:
                logger.error(f"Error sending email to {employee.email}: {mail_err}")

        # 3. إشعار مديري الفرع والمنسق
        try:
            branch_managers = User.objects.filter(
                profile__branch=schedule.branch, 
                profile__role__in=['branch_manager', 'coordinator']
            ).exclude(id__in=unique_employee_ids)
            for bm in branch_managers:
                Notification.objects.create(
                    recipient=bm,
                    title=f"اعتماد الجدول التشغيلي - فرع {schedule.branch.name}",
                    message=f"تم اعتماد الجدول التشغيلي لفرع {schedule.branch.name} للفترة من {schedule.start_date} إلى {schedule.end_date} بنجاح.",
                    link=schedule_url,
                    is_read=False
                )
        except Exception as bm_err:
            logger.error(f"Error notifying branch managers: {bm_err}")

    except Exception as e:
        logger.error(f"Error in send_schedule_approval_emails for schedule {schedule.id}: {e}", exc_info=True)
