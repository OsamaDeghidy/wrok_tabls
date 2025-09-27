# خطة تفصيلية لمطور الباك إند (Django Backend) — **نظام إدارة الجداول التشغيلية**

(هذه الخطة مكملة لخطة الـ Frontend بحيث يعمل المطوران بالتوازي، مع تحديد المسئوليات، المهام، الموديلات، الفاليديشن، والـ APIs/Views اللازمة.)

---

## 1. المبادئ العامة

* **إطار العمل:** Django LTS (4.x أو 5.x عند توفر LTS).
* **قاعدة البيانات:** PostgreSQL (SQLite فقط للتجارب المحلية).
* **تنظيم الكود:** كل **App** مستقل يحتوي على موديلات + Views + Forms + Templates + Static + Tests.
* **الأمان:** الالتزام بمعايير Django Security (CSRF, XSS, SQL injection).
* **الأداء:** استخدام QuerySets محسنة، Indexes للحقول المهمة، Caching (Redis).
* **التكامل:** استيراد/تصدير Excel (openpyxl, pandas)، تكامل مع SAP/SuccessFactors لاحقًا عبر APIs.
* **إدارة الصلاحيات:** Django Permissions + Django Guardian (لـ Object-level permissions).
* **الأرشفة والتدقيق:** Audit Log + History لكل تغيير.
* **الرسائل/التنبيهات:** Celery + Redis للمهام الخلفية (إشعارات، Auto-archive، تذكيرات approvals).

---

## 2. تقسيم الـ Apps (Modules)

### Apps أساسية:

1. **users** → إدارة الحسابات والصلاحيات.
2. **employees** → الموظفين، بياناتهم الأساسية.
3. **branches** → المعارض، الفئات (A/B/C)، إعدادات التشغيل.
4. **schedules** → الجداول التشغيلية والنوبات.
5. **leaves** → الإجازات والغياب.
6. **approvals** → مسارات الموافقات متعددة المستويات.
7. **violations** → المخالفات والإجراءات الجزائية.
8. **reports** → التقارير والتحليلات.
9. **integrations** → استيراد/تصدير البيانات، التكامل مع SAP/SuccessFactors.
10. **auditlog** → سجل التعديلات والأرشفة.

---

## 3. خطة قواعد البيانات (Models + علاقات)

### users

* يعتمد على `AbstractUser` مع إضافة role (SuperAdmin, RegionManager, OpsManager, BranchManager, Coordinator, Employee).
* Permissions: جاهزة من Django + custom per model.

### employees

* `Employee(id, employee_number, first_name, last_name, branch(FK), job_title, join_date, employment_type, max_weekly_hours, active)`
* قواعد خاصة: إذا كان رقم الموظف يبدأ بـ `98979` → max\_weekly\_hours = 60.

### branches

* `Branch(id, name, category(A/B/C), region, open_time, close_time, working_days, default_hours_per_day, min_staff, max_staff)`

### schedules

* `Schedule(id, branch(FK), start_date, end_date, status(Draft/Pending/Approved/Rejected), created_by, version)`
* `ScheduleEntry(id, schedule(FK), employee(FK), date, start_time, end_time, hours, is_cover, notes)`

### leaves

* `LeaveRequest(id, employee(FK), type(annual/sick), from_date, to_date, status(Pending/Approved/Rejected), approved_by, approved_at)`

### approvals

* `ApprovalFlow(id, related_object(GenericFK), step_order, role/user, status, acted_by, acted_at, comment)`

### violations

* `Violation(id, employee(FK), date, type(behavior/attendance/sales), description, action(warning/notice), archived_at)`
* قاعدة: المخالفة تسقط أوتوماتيكياً بعد 6 أشهر (Celery task).

### reports

* Query models (لا تحتاج DB غالباً).
* يتم إنشاء ReportsView تستخدم filters لإرجاع DataFrames/CSV.

### integrations

* `ImportJob(id, file_name, created_at, status, errors, mapped_fields, processed_count)`
* يقرأ بيانات من Excel/CSV ويحولها إلى موديلات الموظفين والجداول.

### auditlog

* `AuditLog(id, entity_type, entity_id, action, old_value, new_value, changed_by, timestamp)`
* يعتمد signals (post\_save, post\_delete).

---

## 4. خطة الـ Views / APIs

لكل App → Views مقسمة:

### users

* Login/Logout/Register/ResetPassword.
* User Management: Create/Edit/Delete (Admins only).

### employees

* List / Detail / Create / Update / Import (Excel).
* API: `/api/employees/` (للاستخدام في واجهات الـ wizard).

### branches

* List / Detail / Settings.
* API: `/api/branches/` (للتقارير + UI filters).

### schedules

* Wizard Create (multi-step form).
* Validate Schedule → Endpoint لإرجاع conflicts.
* Approve/Reject Schedule (trigger ApprovalFlow).

### leaves

* Request Leave, Approve/Reject Leave.
* API: `/api/leaves/?employee_id=...` للـ validation أثناء الجدولة.

### approvals

* List Pending Approvals for user role.
* Action endpoints (Approve, Reject, Request Changes).

### violations

* Create Violation, Archive Violation.
* Chart Data API: `/api/violations/stats?month=...`

### reports

* Generate reports (filter params).
* Export Excel/PDF.
* API endpoint للـ Power BI.

### integrations

* Import Excel (upload → parse → validate → insert).
* Export Schedules/Employees as CSV/Excel.

### auditlog

* Timeline endpoint: `/api/auditlog/<entity>/<id>/`

---

## 5. الفاليديشن (Business Rules)

* منع إدخال جدول لموظف إذا عنده إجازة Approved بنفس التاريخ.
* تحقق من الحد الأقصى للساعات الأسبوعية (خاصة العامل الخارجي).
* تحقق من تكرار نفس يوم الراحة → يصدر تنبيه.
* تحقق من تكرار نفس ساعات العمل لنفس الفترة → تنبيه.
* إذا لا يوجد سوى موظفين في الفرع → يوزع النظام افتراضياً (6 أيام × 8 ساعات).
* تعديل بعد الاعتماد → إنشاء نسخة جديدة + ApprovalFlow جديد.

---

## 6. الخدمات الخلفية (Background Tasks)

* Celery beat jobs:

  * Auto-archive Violations older than 6 months.
  * Daily report: uncovered hours, overtime alerts.
  * Reminders for pending approvals (escalation).

---

## 7. الأمن (Security)

* صلاحيات دقيقة (object-level) باستخدام Django Guardian.
* حماية CSRF على جميع POST.
* استخدام SSL + HSTS.
* Logging محمي لكل العمليات.
* Rate limiting (django-ratelimit) على Endpoints حساسة.

---

## 8. تكامل مع الـ Frontend

* كل View يعيد **context واضح** للـ template.
* Validation errors → تعرض في الفورم (Django messages framework).
* APIs (JSON) لواجهات تفاعلية (wizard, charts, imports).
* استخدام نفس **theme context** (تمرير الألوان عبر CSS فقط).

---

## 9. خطة الملفات (Backend)

```
apps/
├─ employees/
│  ├─ models.py
│  ├─ views.py
│  ├─ serializers.py   # إذا احتجت API
│  ├─ forms.py
│  ├─ urls.py
│  └─ tests/
├─ schedules/
│  ├─ models.py
│  ├─ views.py
│  ├─ validators.py   # business rules
│  ├─ services.py     # logic مثل auto-assign
│  ├─ urls.py
│  └─ tests/
...
```

---

## 10. خطة الاختبارات (QA Backend)

* **Unit Tests:** كل model, service, validator.
* **Integration Tests:** إنشاء جدول + تمريره عبر مسار الموافقات.
* **API Tests:** استدعاء endpoints (REST).
* **Performance Tests:** Querysets الكبيرة (reports).
* **Security Tests:** محاولات صلاحيات خاطئة.

---

## 11. قائمة مهام مطور الباك إند (Sprint Checklist)

* [ ] إعداد المشروع (Django, settings, PostgreSQL, Redis, Celery).
* [ ] بناء users app (roles, permissions).
* [ ] إنشاء models الأساسية (employees, branches, schedules, leaves, approvals, violations).
* [ ] بناء validators (قواعد العمل).
* [ ] إعداد ApprovalFlow engine.
* [ ] إنشاء import/export jobs (Excel/CSV).
* [ ] بناء AuditLog عبر signals.
* [ ] إعداد API endpoints (DRF أو JSONResponse).
* [ ] ربط Celery بالمهام الخلفية (auto-archive, reminders).
* [ ] كتابة Unit tests وIntegration tests.
* [ ] إعداد CI pipeline للتأكد من التغطية والاختبارات.

---

## 12. تسليمات مطور الباك إند

* كود Django كامل مع apps مستقلة.
* سكريبت migrations لقاعدة البيانات.
* API Docs (Swagger أو DRF schema).
* دليل إعداد (README).
* تقارير اختبارات (pytest).
* إعداد Celery/Redis وملفات Docker.

---

