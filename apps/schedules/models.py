from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Schedule(models.Model):
    """نموذج الجدول التشغيلي"""
    
    TYPE_CHOICES = [
        ('weekly', 'أسبوعي'),
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('yearly', 'سنوي'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('pending_coordinator', 'في انتظار موافقة المنسق'),
        ('pending_region_manager', 'في انتظار موافقة مدير المنطقة'),
        ('pending_operations_manager', 'في انتظار موافقة مدير العمليات'),
        ('pending_admin_manager', 'في انتظار موافقة مدير الإدارة'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
        ('active', 'نشط'),
        ('completed', 'مكتمل'),
    ]
    
    # Fields
    branch = models.ForeignKey(
        'branches.Branch', 
        on_delete=models.CASCADE,
        verbose_name='الفرع'
    )
    
    schedule_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='weekly',
        verbose_name='نوع الجدول'
    )
    
    start_date = models.DateField(
        verbose_name='تاريخ البداية'
    )
    
    end_date = models.DateField(
        verbose_name='تاريخ النهاية'
    )
    
    status = models.CharField(
        max_length=30, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name='الحالة'
    )
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='أنشأ بواسطة'
    )
    
    version = models.PositiveIntegerField(
        default=1,
        verbose_name='الإصدار'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        verbose_name = 'الجدول التشغيلي'
        verbose_name_plural = 'الجداول التشغيلية'
        ordering = ['-created_at']
        # تم إزالة unique_together للسماح بجداول متعددة لنفس الفترة
    
    def __str__(self):
        return f"{self.branch.name} - {self.get_schedule_type_display()} ({self.start_date} إلى {self.end_date})"
    
    def get_entries_count(self):
        """عدد الإدخالات في الجدول"""
        return self.entries.count()
    
    def get_employees_count(self):
        """عدد الموظفين في الجدول"""
        return self.entries.values('employee').distinct().count()
    
    def get_total_hours(self):
        """إجمالي الساعات في الجدول"""
        from django.db.models import Sum
        total = self.entries.aggregate(total=Sum('hours'))['total']
        return total or 0
    
    def get_duration_days(self):
        """حساب مدة الجدول بالأيام"""
        from datetime import timedelta
        return (self.end_date - self.start_date).days + 1
    
    def get_duration_display(self):
        """عرض مدة الجدول بشكل مقروء"""
        days = self.get_duration_days()
        if days == 1:
            return "يوم واحد"
        elif days < 7:
            return f"{days} أيام"
        elif days < 30:
            weeks = days // 7
            remaining_days = days % 7
            if remaining_days == 0:
                return f"{weeks} أسبوع" if weeks == 1 else f"{weeks} أسابيع"
            else:
                return f"{weeks} أسبوع و {remaining_days} أيام"
        else:
            months = days // 30
            remaining_days = days % 30
            if remaining_days == 0:
                return f"{months} شهر" if months == 1 else f"{months} أشهر"
            else:
                return f"{months} شهر و {remaining_days} أيام"
    
    def get_coverage_percentage(self):
        """نسبة التغطية"""
        # حساب عدد الساعات المطلوبة للتغطية الكاملة
        required_hours = self.calculate_required_hours()
        actual_hours = self.get_total_hours()
        
        if required_hours > 0:
            # تحويل القيم إلى float لتجنب خطأ القسمة بين Decimal و float
            required_hours = float(required_hours)
            actual_hours = float(actual_hours)
            coverage = (actual_hours / required_hours) * 100
            return min(100, max(0, coverage))
        return 0
    
    def get_coverage_percentage_alternative(self):
        """نسبة التغطية البديلة بناءً على عدد الأيام والموظفين"""
        from datetime import timedelta
        
        # حساب عدد الأيام
        days_count = self.get_duration_days()
        
        # حساب عدد الموظفين الفريدين
        unique_employees = self.entries.values('employee').distinct().count()
        
        # حساب إجمالي الساعات الفعلية
        actual_hours = self.get_total_hours()
        
        # حساب الساعات المطلوبة (8 ساعات × عدد الأيام × عدد الموظفين)
        required_hours = 8 * days_count * unique_employees if unique_employees > 0 else 0
        
        if required_hours > 0:
            coverage = (float(actual_hours) / required_hours) * 100
            return min(100, max(0, coverage))
        return 0
    
    def calculate_required_hours(self):
        """حساب الساعات المطلوبة للتغطية الكاملة"""
        from datetime import timedelta
        from apps.branches.models import BranchShift
        
        total_hours = 0
        current_date = self.start_date
        
        # الحصول على الشفتات النشطة للفرع
        shifts = BranchShift.objects.filter(branch=self.branch, is_active=True)
        if not shifts.exists():
            return 0
        
        # حساب إجمالي ساعات الشفتات في اليوم الواحد
        daily_hours = sum(shift.get_duration() for shift in shifts)
        
        while current_date <= self.end_date:
            # التحقق من أن اليوم في أيام عمل الفرع
            day_name = current_date.strftime('%A').lower()
            day_mapping = {
                'monday': 'monday',
                'tuesday': 'tuesday', 
                'wednesday': 'wednesday',
                'thursday': 'thursday',
                'friday': 'friday',
                'saturday': 'saturday',
                'sunday': 'sunday'
            }
            
            arabic_day = day_mapping.get(day_name)
            # إذا لم تكن أيام العمل محددة، نعتبر كل الأيام أيام عمل
            if not hasattr(self.branch, 'working_days') or not self.branch.working_days or arabic_day in self.branch.working_days:
                total_hours += daily_hours
            
            current_date += timedelta(days=1)
        
        return total_hours
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError({
                    'end_date': 'تاريخ النهاية يجب أن يكون بعد تاريخ البداية'
                })


class ScheduleEntry(models.Model):
    """نموذج إدخال الجدول التشغيلي"""
    
    schedule = models.ForeignKey(
        Schedule, 
        on_delete=models.CASCADE, 
        related_name='entries',
        verbose_name='الجدول'
    )
    
    employee = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='الموظف'
    )
    
    date = models.DateField(
        verbose_name='التاريخ'
    )
    
    shift = models.ForeignKey(
        'branches.BranchShift', 
        on_delete=models.CASCADE,
        verbose_name='الشفت'
    )
    
    start_time = models.TimeField(
        verbose_name='ساعة البداية'
    )
    
    end_time = models.TimeField(
        verbose_name='ساعة النهاية'
    )
    
    hours = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        verbose_name='عدد الساعات'
    )
    
    is_cover = models.BooleanField(
        default=False,
        verbose_name='تغطية'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='ملاحظات'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )
    
    class Meta:
        verbose_name = 'إدخال الجدول التشغيلي'
        verbose_name_plural = 'إدخالات الجداول التشغيلية'
        ordering = ['date', 'start_time']
        unique_together = ['schedule', 'employee', 'date', 'shift']
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} ({self.start_time} - {self.end_time})"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        # التحقق من أن الموظف مرتبط بالفرع الصحيح
        if self.employee and hasattr(self.employee, 'profile'):
            if self.employee.profile.branch != self.schedule.branch:
                raise ValidationError({
                    'employee': 'الموظف يجب أن يكون مرتبط بنفس فرع الجدول'
                })
        
        # التحقق من أن التاريخ في نطاق الجدول
        if self.date:
            if self.date < self.schedule.start_date or self.date > self.schedule.end_date:
                raise ValidationError({
                    'date': 'التاريخ يجب أن يكون في نطاق الجدول'
                })
        
        # التحقق من أن الشفت ينتمي لنفس الفرع
        if self.shift and self.shift.branch != self.schedule.branch:
            raise ValidationError({
                'shift': 'الشفت يجب أن ينتمي لنفس فرع الجدول'
            })
        
        # التحقق من أن الموظف ليس في إجازة في هذا التاريخ
        if self.employee and self.date:
            from apps.leaves.models import LeaveRequest
            overlapping_leaves = LeaveRequest.objects.filter(
                employee=self.employee,
                start_date__lte=self.date,
                end_date__gte=self.date,
                status='approved'
            )
            if overlapping_leaves.exists():
                raise ValidationError({
                    'employee': 'الموظف في إجازة معتمدة في هذا التاريخ'
                })
    
    def save(self, *args, **kwargs):
        # حساب الساعات تلقائياً
        if not self.hours and self.start_time and self.end_time:
            from datetime import datetime, timedelta
            
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            
            # إذا كان وقت النهاية أقل من وقت البداية، فهذا يعني أنه نوبة ليلية
            if end <= start:
                end += timedelta(days=1)
            
            duration = end - start
            self.hours = duration.total_seconds() / 3600  # تحويل إلى ساعات
        
        super().save(*args, **kwargs)