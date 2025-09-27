from django.db import models
from apps.users.models import User

# هذا الملف أصبح فارغاً لأن نموذج الموظف تم دمجه في نموذج المستخدم
# يمكن استخدام هذا الملف لإضافة نماذج أخرى متعلقة بالموظفين إذا لزم الأمر

class EmployeeProfile(models.Model):
    """نموذج إضافي لمعلومات الموظف (اختياري)"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    national_id = models.CharField(max_length=20, unique=True, blank=True, verbose_name='رقم الهوية')
    birth_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الميلاد')
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name='صورة الموظف')
    
    # معلومات إضافية
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name='جهة الاتصال في الطوارئ')
    emergency_phone = models.CharField(max_length=20, blank=True, verbose_name='رقم الطوارئ')
    
    class Meta:
        verbose_name = 'ملف الموظف'
        verbose_name_plural = 'ملفات الموظفين'
    
    def __str__(self):
        return f"ملف {self.user.get_full_name()}"