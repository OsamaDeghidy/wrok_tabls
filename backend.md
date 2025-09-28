# خطة تفصيلية لمطور الباك إند (Django Backend) — **نظام إدارة الجداول التشغيلية**

## **تحديث شامل بناءً على مراجعة ملفات الفرونت**

بعد مراجعة شاملة لملفات الفرونت (`templates/`)، تم تحديد الميزات المطلوبة وتحديث الخطة لضمان التوافق الكامل بين الفرونت والباك إند.

---

## 1. المبادئ العامة

* **إطار العمل:** Django 5.x مع استخدام `django.contrib.auth.models.User` كنموذج أساسي
* **قاعدة البيانات:** SQLite للتطوير، PostgreSQL للإنتاج
* **تنظيم الكود:** كل **App** مستقل مع موديلات + Views + Forms + Templates + Static + Tests
* **الأمان:** Django Security (CSRF, XSS, SQL injection) + صلاحيات متدرجة
* **الأداء:** QuerySets محسنة، Indexes للحقول المهمة، Caching
* **التكامل:** استيراد/تصدير Excel، APIs للواجهات التفاعلية
* **إدارة الصلاحيات:** نظام صلاحيات متدرج (7 مستويات)
* **الأرشفة والتدقيق:** Audit Log + History لكل تغيير
* **الرسائل/التنبيهات:** نظام إشعارات داخلي + تذكيرات الموافقات

---

## 2. نظام الصلاحيات المتدرج (بناءً على الفرونت)

### مستويات الصلاحيات:
1. **موظف (employee)** - عرض الجداول وطلبات الإجازات
2. **مدير معرض (branch_manager)** - إدارة فرع واحد فقط
3. **منسق (coordinator)** - تنسيق بين الفروع
4. **مدير منطقة (region_manager)** - إدارة منطقة كاملة
5. **مدير عمليات (operations_manager)** - إدارة العمليات
6. **مدير إدارة (admin_manager)** - صلاحيات إدارية كاملة
7. **مدير عام (super_admin)** - صلاحيات النظام الكاملة

### مسار الموافقات:
```
مدير المعرض → منسق → مدير المنطقة → مدير العمليات → مدير الإدارة → الموظفين
```

---

## 3. خطة قواعد البيانات (Models + علاقات)

### users (بناءً على django.contrib.auth.models.User)

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    job_id = models.CharField(max_length=50, blank=True)
    work_hours = models.PositiveIntegerField(choices=WORK_HOURS_CHOICES, default=8)
    work_days = models.PositiveIntegerField(default=6)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Choices
    ROLE_CHOICES = [
        ('employee', 'موظف'),
        ('branch_manager', 'مدير معرض'),
        ('coordinator', 'منسق'),
        ('region_manager', 'مدير منطقة'),
        ('operations_manager', 'مدير عمليات'),
        ('admin_manager', 'مدير إدارة'),
        ('super_admin', 'مدير عام'),
    ]
    
    WORK_HOURS_CHOICES = [
        (8, '8 ساعات (6 أيام عمل)'),
        (9, '9 ساعات (5 أيام عمل)'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('suspended', 'معلق'),
        ('terminated', 'منتهي الخدمة'),
    ]
```

### branches (بناءً على الفرونت)

```python
class Branch(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=50, choices=REGION_CHOICES)
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    capacity = models.PositiveIntegerField(default=1)
    opening_date = models.DateField(null=True, blank=True)
    working_days = models.JSONField(default=list)  # ['saturday', 'sunday', ...]
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class BranchShift(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='shifts')
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

### schedules (بناءً على الفرونت المتقدم)

```python
class Schedule(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    schedule_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='weekly')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ScheduleEntry(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='entries')
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.ForeignKey('branches.BranchShift', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    is_cover = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
```

### leaves (بناءً على الفرونت)

```python
class LeaveRequest(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    days_count = models.PositiveIntegerField()
    reason = models.TextField()
    emergency_contact = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    manager_notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    attachments = models.JSONField(default=list)  # Store file paths
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### violations (بناءً على الفرونت)

```python
class Violation(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    violation_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date = models.DateField()
    time = models.TimeField()
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='low')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    action_taken = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_violations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### approvals (نظام الموافقات المتدرج)

```python
class ApprovalFlow(models.Model):
    related_object_type = models.CharField(max_length=50)  # 'schedule', 'leave', etc.
    related_object_id = models.PositiveIntegerField()
    current_step = models.PositiveIntegerField(default=1)
    total_steps = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class ApprovalStep(models.Model):
    approval_flow = models.ForeignKey(ApprovalFlow, on_delete=models.CASCADE, related_name='steps')
    step_order = models.PositiveIntegerField()
    required_role = models.CharField(max_length=50)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True)
    acted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 4. خطة الـ Views / APIs (بناءً على الفرونت)

### users
- `LoginView` - تسجيل الدخول مع حسابات تجريبية
- `RegisterView` - إنشاء حساب جديد مع اختيار الدور والفرع
- `UserListView` - قائمة المستخدمين مع فلترة وبحث
- `UserDetailView` - تفاصيل المستخدم
- `UserCreateView` - إنشاء مستخدم جديد
- `UserEditView` - تعديل المستخدم
- `UserDeleteView` - حذف المستخدم
- `UserProfileView` - ملف المستخدم الشخصي
- `UserEditProfileView` - تعديل الملف الشخصي
- `UserChangePasswordView` - تغيير كلمة المرور

### employees (دمج مع users)
- نفس views المستخدمين مع إضافة حقول الموظفين
- `EmployeeImportView` - استيراد من Excel
- `EmployeeExportView` - تصدير إلى Excel

### branches
- `BranchListView` - قائمة الفروع مع فلترة
- `BranchDetailView` - تفاصيل الفرع
- `BranchCreateView` - إنشاء فرع جديد مع إعدادات الشفتات
- `BranchEditView` - تعديل الفرع
- `BranchDeleteView` - حذف الفرع
- `BranchManagersAPI` - API للحصول على مدراء الفروع

### schedules
- `ScheduleCreateView` - إنشاء جدول متعدد الخطوات (Wizard)
- `ScheduleListView` - قائمة الجداول مع فلترة
- `ScheduleDetailView` - تفاصيل الجدول
- `ScheduleEditView` - تعديل الجدول
- `ScheduleApproveView` - موافقة على الجدول
- `ScheduleRejectView` - رفض الجدول
- `ScheduleCopyView` - نسخ الجدول
- `ScheduleValidationAPI` - API للتحقق من التضارب

### leaves
- `LeaveCreateView` - طلب إجازة جديد
- `LeaveListView` - قائمة طلبات الإجازات
- `LeaveDetailView` - تفاصيل طلب الإجازة
- `LeaveEditView` - تعديل طلب الإجازة
- `LeaveApproveView` - موافقة على الإجازة
- `LeaveRejectView` - رفض الإجازة
- `LeaveBalanceAPI` - API لرصيد الإجازات

### violations
- `ViolationCreateView` - إضافة مخالفة جديدة
- `ViolationListView` - قائمة المخالفات
- `ViolationDetailView` - تفاصيل المخالفة
- `ViolationEditView` - تعديل المخالفة
- `ViolationStatsAPI` - API لإحصائيات المخالفات

### approvals
- `ApprovalListView` - قائمة الموافقات المعلقة
- `ApprovalActionView` - تنفيذ إجراء الموافقة
- `ApprovalHistoryView` - تاريخ الموافقات

---

## 5. الفاليديشن (Business Rules) - بناءً على الملاحظات

### قواعد العمل الأساسية:
1. **ساعات العمل:**
   - 8 ساعات = 6 أيام عمل في الأسبوع
   - 9 ساعات = 5 أيام عمل في الأسبوع
   - الموظفون الخارجيون (رقم يبدأ بـ 98979) = 60 ساعة أسبوعياً

2. **الجدولة:**
   - منع جدولة موظف في إجازة معتمدة
   - التحقق من التغطية الكاملة للمعرض
   - منع التداخل في أوقات العمل
   - توزيع تلقائي إذا كان موظف واحد فقط

3. **الشفتات:**
   - يمكن للمعرض أن يحتوي على عدة شفتات
   - تحديد ساعات العمل والاستراحات لكل شفت
   - التحقق من التغطية على مدار الساعة

4. **الصلاحيات:**
   - مدير المعرض يرى فقط موظفي فرعه
   - منع مدير المعرض من إنشاء جداول لفرع آخر
   - مسار الموافقات المتدرج

5. **أنواع الجداول:**
   - أسبوعية، شهرية، ربع سنوية، سنوية
   - مراعاة نوع الجدول في الواجهة والتحقق

---

## 6. خطة الملفات (Backend) - محدثة

```
apps/
├─ users/
│  ├─ models.py          # UserProfile model
│  ├─ views.py           # All user views
│  ├─ forms.py           # User forms
│  ├─ admin.py           # Django admin
│  ├─ urls.py            # URL patterns
│  └─ tests/
├─ branches/
│  ├─ models.py          # Branch, BranchShift models
│  ├─ views.py           # Branch views
│  ├─ forms.py           # Branch forms
│  ├─ admin.py           # Django admin
│  ├─ urls.py            # URL patterns
│  └─ tests/
├─ schedules/
│  ├─ models.py          # Schedule, ScheduleEntry models
│  ├─ views.py           # Schedule views (including wizard)
│  ├─ forms.py           # Schedule forms
│  ├─ validators.py      # Business rules validation
│  ├─ services.py        # Auto-assign logic
│  ├─ admin.py           # Django admin
│  ├─ urls.py            # URL patterns
│  └─ tests/
├─ leaves/
│  ├─ models.py          # LeaveRequest model
│  ├─ views.py           # Leave views
│  ├─ forms.py           # Leave forms
│  ├─ admin.py           # Django admin
│  ├─ urls.py            # URL patterns
│  └─ tests/
├─ violations/
│  ├─ models.py          # Violation model
│  ├─ views.py           # Violation views
│  ├─ forms.py           # Violation forms
│  ├─ admin.py           # Django admin
│  ├─ urls.py            # URL patterns
│  └─ tests/
├─ approvals/
│  ├─ models.py          # ApprovalFlow, ApprovalStep models
│  ├─ views.py           # Approval views
│  ├─ forms.py           # Approval forms
│  ├─ admin.py           # Django admin
│  ├─ urls.py            # URL patterns
│  └─ tests/
├─ reports/
│  ├─ views.py           # Report views
│  ├─ forms.py           # Report forms
│  ├─ urls.py            # URL patterns
│  └─ tests/
├─ integrations/
│  ├─ models.py          # ImportJob model
│  ├─ views.py           # Import/Export views
│  ├─ forms.py           # Import forms
│  ├─ admin.py           # Django admin
│  ├─ urls.py            # URL patterns
│  └─ tests/
└─ auditlog/
    ├─ models.py          # AuditLog model
    ├─ views.py           # Audit views
    ├─ signals.py         # Django signals
    ├─ admin.py           # Django admin
    ├─ urls.py            # URL patterns
    └─ tests/
```

---

## 7. قائمة مهام مطور الباك إند (محدثة)

### المرحلة الأولى: الأساسيات
- [x] تنظيف النظام وإعادة البداية
- [ ] إنشاء UserProfile model مع جميع الحقول
- [ ] إنشاء Branch و BranchShift models
- [ ] إنشاء Schedule و ScheduleEntry models
- [ ] إنشاء LeaveRequest model
- [ ] إنشاء Violation model
- [ ] إنشاء ApprovalFlow و ApprovalStep models

### المرحلة الثانية: الـ Views الأساسية
- [ ] إنشاء views المستخدمين (login, register, list, create, edit, delete)
- [ ] إنشاء views الفروع (list, create, edit, delete)
- [ ] إنشاء views الجداول (create wizard, list, edit, approve/reject)
- [ ] إنشاء views الإجازات (create, list, edit, approve/reject)
- [ ] إنشاء views المخالفات (create, list, edit)

### المرحلة الثالثة: نظام الموافقات
- [ ] إنشاء نظام الموافقات المتدرج
- [ ] ربط الموافقات بالجداول والإجازات
- [ ] إنشاء views الموافقات

### المرحلة الرابعة: الفاليديشن والخدمات
- [ ] إنشاء validators للقواعد التجارية
- [ ] إنشاء services للجدولة التلقائية
- [ ] إنشاء APIs للواجهات التفاعلية

### المرحلة الخامسة: الإضافات
- [ ] إنشاء نظام التقارير
- [ ] إنشاء نظام الاستيراد/التصدير
- [ ] إنشاء نظام Audit Log
- [ ] إنشاء Django Admin

### المرحلة السادسة: الاختبارات والتحسين
- [ ] كتابة Unit Tests
- [ ] كتابة Integration Tests
- [ ] تحسين الأداء
- [ ] اختبار الأمان

---

## 8. ملاحظات مهمة من الفرونت

1. **حسابات تجريبية:** يجب إنشاء حسابات تجريبية للاختبار
2. **الفلترة:** تغيير كلمة "فلترة" إلى "تطبيق" في جميع الصفحات
3. **المدراء:** عند اختيار الفرع، عرض المدراء التابعين له
4. **الرقم الوظيفي:** بدلاً من رقم الموظف، استخدام الرقم الوظيفي
5. **ساعات العمل:** 8 أو 9 ساعات مع تحديد أيام العمل
6. **الشفتات المتعددة:** المعرض يمكن أن يحتوي على عدة شفتات
7. **التغطية:** ضمان وجود موظف في المعرض في جميع الأوقات
8. **التداخل:** السماح بالتداخل في الأوقات
9. **الصلاحيات:** كل دور له صلاحيات محددة
10. **مسار الموافقات:** نظام موافقات متدرج واضح

---

## 9. تسليمات مطور الباك إند

* كود Django كامل مع apps مستقلة
* جميع الموديلات مع العلاقات الصحيحة
* جميع الـ Views مع التوافق مع الفرونت
* نظام الموافقات المتدرج
* الفاليديشن والقواعد التجارية
* Django Admin مكتمل
* APIs للواجهات التفاعلية
* نظام التقارير
* نظام الاستيراد/التصدير
* نظام Audit Log
* Unit Tests و Integration Tests
* دليل الإعداد والاستخدام

---

**ملاحظة:** هذه الخطة مبنية على مراجعة شاملة لملفات الفرونت وتضمن التوافق الكامل بين الفرونت والباك إند.