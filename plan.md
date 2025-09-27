# خطة كاملة ومهنية لنظام **إدارة الجداول التشغيلية** (نسخة مُحسّنة وشاملة بالمهام الجديدة وبنية الملفات)

هذه الخطة توحّد **الفرونت-إند (Django Templates + Bootstrap)** و**الباك-إند (Django)** بحيث يعمل الفريقان بالتوازي. تتضمن: رؤية عامة، أهداف، مخرجات، تفصيل الموديلات، قواعد العمل، واجهات (Views/API)، بنية الملفات المفصّلة، استراتيجيات النشر/الأمان/الاختبارات، مهام Sprint-ready، وقائمة تسليمات نهائية. أضفت مهام جديدة مهمة للإنتاجية والجودة: CI/CD، مراقبة، نسخ احتياطي، اختبارات حمل، seed data، وثائق API/UX، تدريب المستخدم، وخطة صيانة.

> اللون البنفسجي من الشعار يُستخدم كـ primary color: ملف مركزي `theme.css` مذكور في قسم Frontend.

---

# 1. ملخّص المشروع & أهدافه (مرة واحدة مختصرة)

نظام ويب لإدارة النوبات والجداول التشغيلية لعدة معارض وفروع، يدعم: إنشاء جداول مرنة، مسارات موافقات قابلة للتخصيص، إدارة الإجازات، التقارير والتحليلات، استيراد/تصدير ملفات، لوحة تحكم للإدارة، سجلات تدقيق، وإشعارات. الهدف: تقليل التداخلات، ضمان التغطية، وتعزيز اتخاذ القرار عبر تقارير موثوقة.

---

# 2. مخرجات المشروع النهائية

* تطبيق ويب متكامل (Django + Django Templates + Bootstrap) قابل للنشر.
* واجهات CRUD لكل من: الموظفين، المعارض، الجداول، الإجازات، المخالفات، الموافقات، التكاملات.
* Approval engine مرن وقابل للتعديل من واجهة الإعدادات.
* Import/Export Excel/CSV مع history وretry.
* Dashboard تفاعلي + تقارير قابلة للتصدير.
* ملفات code مبوبة per-app (قابلة للنقل كحزمة مستقلة).
* CI/CD pipeline، Dockerized deployment، مراقبة Errors & Metrics.
* دليل مستخدم عربي، دليل نشر، وثائق API (Swagger/OpenAPI).
* اختبارات: Unit, Integration, E2E, Load tests.
* خطة صيانة & SLA مقترح.

---

# 3. الهيكل العام للمشروع — مع قواعد فصل الـ Frontend/Backend per app

نَبْني كل app بحيث يحتوي على كل ما يحتاجه (models, views, templates, static, forms, services, tests) لتسهيل النقل:

```
project_root/
├─ .github/workflows/           # CI
├─ docker-compose.yml
├─ Dockerfile
├─ manage.py
├─ requirements.txt
├─ README.md
├─ docs/                       # user guides, API docs (generated)
├─ config/                      # project settings (production/staging/local)
│  ├─ settings/
│  │  ├─ base.py
│  │  ├─ dev.py
│  │  └─ prod.py
│  └─ uwsgi/nginx templates
├─ apps/
│  ├─ users/
│  │  ├─ models.py
│  │  ├─ admin.py
│  │  ├─ views.py
│  │  ├─ urls.py
│  │  ├─ templates/users/...
│  │  ├─ static/users/...
│  │  ├─ serializers.py
│  │  └─ tests/
│  ├─ employees/
│  ├─ branches/
│  ├─ schedules/
│  ├─ leaves/
│  ├─ approvals/
│  ├─ violations/
│  ├─ integrations/
│  ├─ reports/
│  └─ auditlog/
├─ templates/
│  ├─ base.html
│  └─ includes/ (header, sidebar, modals)
├─ static/
│  ├─ css/
│  │  └─ theme.css       # ملف الألوان المركزي
│  ├─ js/
│  └─ images/
└─ scripts/                # db seed, migrations helpers, backup scripts
```

---

# 4. نماذج (Models) رئيسية — مخطط ER وصفي (Entities & Key fields)

> سطر واحد عن العلاقات: Employee ↔ Branch (FK) ; Branch ↔ Schedule (FK) ; Schedule ↔ ScheduleEntry (N) ; Schedule ↔ ApprovalFlow (1..N) ; Employee ↔ LeaveRequest (N) ; Employee ↔ Violation (N).

**users.User** (extends AbstractUser)

* roles (choices), region (FK optional), employee (OneToOne optional).

**employees.Employee**

* employee\_number, first\_name, last\_name, branch(FK), job\_title, join\_date, employment\_type, max\_weekly\_hours (auto if prefix 98979 => 60), is\_active, metadata(JSON).

**branches.Branch**

* name, code, category (A/B/C), region, open\_time, close\_time, working\_days (JSON), default\_shift\_length, min\_staff\_per\_shift, max\_staff\_per\_shift, special\_flags.

**schedules.Schedule**

* branch(FK), start\_date, end\_date, created\_by, status (Draft/Pending/Approved/Rejected), version, notes.

**schedules.ScheduleEntry**

* schedule(FK), employee(FK nullable), date, shift\_code, start\_time, end\_time, hours, is\_cover, assigned\_by, conflict\_flags(JSON).

**leaves.LeaveRequest**

* employee(FK), type, from\_date, to\_date, reason, status, approved\_by, approved\_at, attachment(file).

**approvals.ApprovalFlow**

* content\_object(GenericFK to Schedule/Leave/... ), step\_order, role\_or\_user (nullable), status, acted\_by, acted\_at, comment.

**violations.Violation**

* employee(FK), date, type, description, action, status, archived\_at.

**integrations.ImportJob**

* file\_name, uploaded\_by, status, mapping\_spec(JSON), errors(JSON), processed\_rows\_count.

**auditlog.AuditLog**

* entity\_type, entity\_id, action, payload\_diff, changed\_by, timestamp.

---

# 5. قواعد العمل الأساسية (Business Rules + Validations — Engine)

1. **No-Schedule-On-Approved-Leave:** يمنع System حفظ ScheduleEntry لموظف إن تقاطع مع LeaveRequest status=Approved.
2. **MaxWeeklyHours:** إن employee.employee\_number.startswith('98979') → max\_weekly\_hours = 60. يتم احتساب ساعات الأسبوع والتحذير/منع.
3. **DuplicateRestDay:** إذا تم تكرار نفس يوم الراحة لموظف داخل الفترة → توليد تحذير وإرسال تنبيهات لجميع مسارات الموافقة.
4. **DuplicateShiftForPeriod:** إذا ظهر تكرار نفس ساعات العمل لعدة موظفين للفترة نفسها → توليد alert لمراجعة الموافقات.
5. **AutoDistributionDefault:** لو لم تُدخل تغطية الفرع ويحتوي فقط على موظفين داخليين → توزيع افتراضي 6 أيام عمل + 1 راحة × 8 ساعات.
6. **ImmutableApprovedVersioning:** التعديل على جدول Approved يؤدي إلى إنشاء نسخة جديدة (version++) مع ApprovalFlow جديد.
7. **Approval Escalation:** إن تعطل طلب موافقة لأكثر من 48 ساعة → reminder escalation (Celery).
8. **Violation Expiry:** تُسقط المخالفات آلياً بعد 6 أشهر (تبقى محفوظة كـ archived record).

تحقّق هذه القواعد يتم على مستويين: client-side (UX warnings) و server-side (validators/services).

---

# 6. واجهات (Views / APIs) مفصلة — Endpoints أساسية

> نوصي ببناء كل View كـ class-based view (Django CBV) وتهيئة JSON endpoints عبر DRF حيث يلزم.

### Auth & Users

* `POST /auth/login/`, `POST /auth/logout/`, `POST /auth/password-reset/`
* `GET /users/` (admin), `GET /users/<id>/`, `POST /users/`, `PUT /users/<id>/`.

### Employees

* `GET /employees/` (search, filters), pagination.
* `GET /employees/<id>/`, `POST /employees/`, `PUT /employees/<id>/`.
* `POST /employees/import/` (upload file → returns import\_job\_id).
* `GET /employees/{id}/shifts?range=...` (assigned shifts).

### Branches

* `GET /branches/`, `GET /branches/<id>/`, `PUT /branches/<id>/settings`.

### Schedules (core)

* `GET /schedules/` (filter by branch, period)
* `GET /schedules/<id>/` (detail + entries + approval trail)
* `POST /schedules/create/` (wizard submit)
* `POST /schedules/<id>/validate/` (returns conflicts/warnings)
* `POST /schedules/<id>/submit_for_approval/`
* `POST /schedules/<id>/approve/` & `POST /schedules/<id>/reject/` (requires permission)

### ScheduleEntries (bulk)

* `POST /schedules/<id>/entries/bulk_assign/` (payload: assignments)
* `DELETE /schedules/<id>/entries/<entry_id>/` (perms)

### Leaves

* `POST /leaves/request/`, `GET /leaves/`, `POST /leaves/<id>/approve/`, `POST /leaves/<id>/reject/`.

### Approvals

* `GET /approvals/pending/` (for current user)
* `POST /approvals/<id>/action/` (approve/reject/comment)

### Reports & Analytics

* `GET /reports/summary?branch=&from=&to=&type=` → JSON/DataFrame.
* `GET /reports/export?format=excel|pdf` → file stream.

### Integrations

* `POST /integrations/import/` (upload)
* `GET /integrations/imports/<id>/status/`
* `POST /integrations/sap/sync/` (admin task trigger)

### AuditLog

* `GET /auditlog/<entity>/<id>/` (timeline)

---

# 7. الأذونات (RBAC & Object-level)

* Roles: SuperAdmin, RegionManager, OpsManager, BranchManager, Coordinator, HR, Employee (viewer limited).
* Permissions examples:

  * `schedules.add_schedule`, `schedules.change_schedule`, `schedules.approve_schedule`.
  * `employees.add_employee`, `employees.change_employee`.
  * Approval roles: mapping role → permission to act on step.
* Use `django-guardian`/`django-rules` لتمكين object-level permissions (مثلاً: BranchManager فقط على Branches التابعة لحيه).

---

# 8. الخدمات الخلفية والمهام المجدولة

* **Celery (with Redis broker)** للمهمات:

  * `task_send_pending_approval_reminders()` كل 12 ساعة.
  * `task_auto_archive_violations()` يومي.
  * `task_check_uncovered_hours()` يومي/عند إنشاء جدول.
  * `task_process_import_job(import_id)` background processing للـ Excel.
* Celery-beat لتشغيل المهام المجدولة.

---

# 9. Logging — Audit — Monitoring

* **Audit:** `auditlog` Model + signals؛ كل تغير CRUD يُسجل تفصيلياً.
* **Errors:** Sentry integration (production).
* **Metrics:** Prometheus + Grafana (CPU, DB latency, Celery queue lengths).
* **Access logs:** Nginx + rotate logs.
* **Alerts:** Slack/email alerts عند أخطاء حرجة أو فشل مهام Celery.

---

# 10. النسخ الاحتياطي والتعافي (Backup & DR)

* DB nightly backups (logical dumps / pg\_dump) مع retention 30 يوم.
* File storage backup (uploads) يومي incremental.
* Restore playbook في docs/scripts مع اختبار restore ربع سنوي.

---

# 11. CI/CD & Release workflow

* Git flow: feature branches → PR → code review → merge to develop → CI runs tests → merge to main triggers deploy to staging → manual approval → deploy to production.
* **CI (GitHub Actions):**

  * Linting (flake8/isort), type checks (mypy), unit tests (pytest), static analysis, build docker image.
* **CD:**

  * Deploy to staging (automatic), to prod (after manual approve). Use Docker + docker-compose or Kubernetes (depending infra).
* Blue/Green or Canary recommended for zero-downtime.

---

# 12. الأمان والتوافق

* HTTPS mandatory, HSTS, Content Security Policy (CSP) basic.
* Hashing passwords (Django defaults), rotation tokens.
* Rate limiting endpoints حساسة (django-ratelimit).
* Input sanitization و validation.
* جلسات قصيرة أو session storage مؤمّن.
* ملفات حساسة في env vars، لا تُخزن في repo.

---

# 13. الأداء وقياس التحمل

* DB Indexes: على employee\_number, branch\_id, date fields, status fields.
* Use select\_related / prefetch\_related في الاستعلامات كثيفة الانضمام.
* Caching: Redis cache for heavy reports & dashboard widgets (ttl قصيرة).
* Load testing: استخدم Locust أو k6 للتحقق من 500-2000 concurrent users حسب SLA.
* Pagination server-side لجميع القوائم الكبيرة.

---

# 14. اختبار الجودة (Testing Strategy)

* **Unit tests**: models, services, validators.
* **Integration tests**: workflows (create schedule → submit → approve).
* **E2E tests**: Playwright/Selenium لتغطية critical flows (wizard).
* **API contract tests**: DRF schema & contract.
* **Security scans**: bandit, dependency scans.
* **Performance tests**: k6/Locust scripts.
* **Visual regression**: Percy/backstop (optionally).

---

# 15. خطة عمل تفصيلية للـ Backend (Sprint-ready tasks)

(مقسمة لمراحل—يمكن تحويلها لجداول سبرينت، مع تقديرات وقت مبدئية إن احتجت)

## Phase 0 — إعداد البيئة (Day 0–3)

* إعداد repo, flake8, pre-commit hooks, docker compose (postgres, redis, web, celery).
* إعداد settings structure (dev/prod), env management (.env.sample).

## Phase 1 — Core Models & Auth (Day 4–12)

* Implement `users`, `employees`, `branches` models + admin.
* Implement base permissions and groups.
* Seed fixtures (sample branches, roles, admin user).

## Phase 2 — Scheduling Core (Day 13–26)

* Implement `schedules`, `schedule_entries`, validators (no-schedule-on-approved-leave, max hours).
* Implement basic create schedule view + DB migration.
* Unit tests for validators/services.

## Phase 3 — Approval Engine (Day 27–36)

* Implement `approvals.ApprovalFlow`, config UI/backend to set chain.
* Endpoints for approve/reject with audit log.
* Celery reminders skeleton.

## Phase 4 — Import/Export & Integrations (Day 37–46)

* Implement `integrations.ImportJob` (upload + background processing).
* Implement mapping UI API and error reporting.
* Export reports as Excel/PDF.

## Phase 5 — Leaves & Violations (Day 47–56)

* Implement `leaves` flows, `violations` model + auto-archive task.
* Reports endpoints for violations trends.

## Phase 6 — Reports & Dashboard (Day 57–68)

* Aggregation queries, endpoints for charts, CSV generator.
* Cache results via Redis.

## Phase 7 — QA, Tests, Load & Docs (Day 69–80)

* Full test coverage (unit+integration).
* E2E scripts.
* Load tests.
* Generate API docs (Swagger) & user guides.

## Phase 8 — Deployment & Handover (Day 81–90)

* CI/CD finalize, infra (NGINX + Gunicorn), DB backups, SSL.
* Run staging → production.
* Handover: docs, runbook, training session.

> (الأيام مجرد تقدير يمكن التعديل حسب فريقك).

---

# 16. بنية الملفات Backend مفصّلة (per-app template)

كل app تتبع نفس النمط:

```
apps/schedules/
├─ __init__.py
├─ admin.py
├─ apps.py
├─ models.py
├─ forms.py
├─ validators.py      # business rules
├─ services.py        # complex logic (assigners, conflict detectors)
├─ views.py
├─ urls.py
├─ serializers.py     # DRF serializers if needed
├─ tasks.py           # celery tasks
├─ templates/schedules/
│  ├─ create_wizard.html
│  ├─ detail.html
│  └─ list.html
├─ static/schedules/
│  ├─ css/schedules.css
│  └─ js/schedules.js
└─ tests/
   ├─ test_models.py
   ├─ test_validators.py
   └─ test_views.py
```

---

# 17. Frontend brief (للتنسيق مع Backend)

* **theme.css** في `static/css/theme.css` (CSS variables لتغيير الألوان المركزي).
* `base.html` مع blocks جاهزة لـ header/sidebar/content/scripts.
* Frontend Dev يعتمد على endpoints المحددة أعلاه (validation endpoints, import status, approval actions).
* Use progressive enhancement: كل form يعمل بدون JS ثم نعزّز UX بـ AJAX.

> سأرفق مثال ملف `theme.css` لنسخه بسرعة (مذكور في الخطة السابقة).

---

# 18. تسليمات للـ Devs (Checklist نهائي)

* [ ] Repo مُنظّم حسب البنية أعلاه.
* [ ] Models + migrations جاهزة.
* [ ] Endpoints الأساسية تعمل (auth, employees, schedules).
* [ ] Approval engine يعمل على بيئة dev.
* [ ] Import job background processing (Celery) يعمل.
* [ ] Dashboard basic widgets.
* [ ] Tests (unit & integration) مغطّاة.
* [ ] CI pipeline يُشغّل اختبارات.
* [ ] Docker compose & prod deploy scripts جاهزة.
* [ ] Docs: README, API docs, Admin guide, User guide.
* [ ] Monitoring (Sentry) و metrics basic setup.
* [ ] Backup scripts موجودة ومجربة محلياً.

---

# 19. خطة الصيانة وعمليات ما بعد التسليم

* إصدار شهري لصيانة security patches.
* مراجعة شهري لـ logs & alerts الأسبوعي.
* اختبار restore شهري للـ backups.
* تحسينات performance ربع سنوية.
* Support window وSLA: مثال (24/7 alerting; 8×5 support).

---

# 20. ملاحظات عملية ونقاط قرار يجب تحديدها الآن (لكي تصبح الخطة تنفيذية)

1. هل النشر على AWS / Azure / On-prem؟ (يؤثر على CD/backup).
2. هل تفضّل استخدام REST فقط أم GraphQL لبعض الاستعلامات المعقدة؟
3. هل تريد realtime (WebSocket/Django Channels) لتحديثات الموافقات/حالة الاستيراد؟
   4.هل تود أن تكون التقارير التفاعلية داخل التطبيق أم تُصدّر لPower BI فقط؟
4. ملف الـ theme (الألوان) جاهز لتعديله من واجهة لاحقاً أم عبر تغيير CSS فقط؟

---

# خاتمة وماذا سأقدّم لك لاحقاً فور طلبك

أستطيع فوراً توليد أي مما يلي بناءً على اختيارك:

* ملف `models.py` كامل للموديلات الأساسية (employees, branches, schedules, entries, leaves, approvals, violations).
* ملف `theme.css` كامل وجاهز للاستخدام.
* `base.html` template و `sidebar/header` includes.
* سيناريو Migration seed script (fixtures) مع بيانات تجريبية.
* ملف PlantUML / ERD لتصديره كصورة أو ملف قابل للطباعة.

