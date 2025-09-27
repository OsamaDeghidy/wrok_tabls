# خطة مفصّلة لمطور الواجهة الأمامية (Frontend) — **Django Templates + Bootstrap**

(مبنية على الخطة العامة للنظام — نظام إدارة الجداول التشغيلية)

ممتاز — سأعطيك خطة تنفيذية عملية ومفصّلة لمهام مطور الواجهة الأمامية باستخدام **Django Templates و Bootstrap**، مع هيكلة تجعل كل تطبيق (app) يحتوي على باك و فرونت خاص به قابل للنقل، وملف مركزي للألوان لتسهيل التغيير مستقبلاً. الخطة تغطي: صفحات المشروع، محتوياتها، الأذونات (permissions) المطلوبة لكل صفحة، مخطط الملفات (per-app & global)، مكونات (components) قابلة لإعادة الاستخدام، سلوكيات جافاسكربت، اختبارات واجهة، قائمة مهام تفصيلية، ونصائح أداء و accessibility.

---

# 1. مبادئ وقيود العمل (Ground rules)

* استخدام **Bootstrap 5** (CSS + JS) كأساس، مع تخصيص عبر CSS variables أو SASS لتغيير theme بسهولة.
* Templates مكتوبة بطريقة **قابلة لإعادة الاستخدام**: `base.html` يحتوي على البنية العامة، وكل app يملك مجلد templates و static خاص به.
* كل app يكون self-contained بحيث ينقل مع ملفاته (models, views, templates, static).
* الدعم الكامل للـ RTL (للعربية) — نسخ CSS خاصة بالـ RTL سيتم تضمينها تلقائياً عند لغة الموقع عربية.
* التركيز على تباين الألوان (contrast) للوصول إلى Accessibility AA على الأقل.
* كل صفحة تحدد أذونات الوصول (Django permission names) لظهور/إخفاء عناصر الواجهة.

---

# 2. ملف ألوان مركزي (Theme variables) — قابل للتغيير بسهولة

أنشئ ملف CSS مركزي يستخدم CSS variables أو ملف SASS لو أردت مزيد تحكم. سأعرض مثالًا باستخدام CSS variables (ملف: `static/css/theme.css`).

```css
/* static/css/theme.css */
:root{
  /* Primary colors (based on logo violet) */
  --primary-50: #f6f3fb;
  --primary-100: #ece7f7;
  --primary-200: #d8cfee;
  --primary-300: #bfa7df;
  --primary-400: #a67ecf;
  --primary-500: #7f4fb8; /* main primary (used for buttons / headers) */
  --primary-600: #6b3f95;
  --primary-700: #572f73;

  /* Secondary / accent */
  --accent-500: #2aa27e; /* optional green accent */

  /* Neutral */
  --bg: #ffffff;
  --surface: #f8f9fb;
  --muted: #6c6c6c;
  --text: #222222;

  /* Status */
  --success: #198754;
  --danger: #dc3545;
  --warning: #ffc107;
  --info: #0dcaf0;

  /* Shadows / radius */
  --card-radius: 12px;
  --card-shadow: 0 6px 18px rgba(38, 40, 55, 0.06);
}

/* Small helpers */
.btn-primary{
  background-color: var(--primary-500);
  border-color: var(--primary-600);
  color: #fff;
}
.btn-primary:hover{ background-color: var(--primary-600); border-color: var(--primary-700); }
.bg-primary-light { background-color: var(--primary-50); }

/* RTL support class (if needed) */
.rtl { direction: rtl; }
```

> للتغيير مستقبلاً: يكفي تعديل القيم في `:root` أو استبدال الملف عبر CI لتطبيق theme جديد.

---

# 3. هيكلة المشروع (اقتراح) — كل app مع فرونت و باك خاص

نقترح الاحتفاظ بهيكل يساعد على نقل التطبيق كاملاً:

```
project_root/
├─ apps/
│  ├─ employees/
│  │  ├─ models.py
│  │  ├─ views.py
│  │  ├─ urls.py
│  │  ├─ templates/
│  │  │  └─ employees/
│  │  │     ├─ list.html
│  │  │     └─ detail.html
│  │  ├─ static/
│  │  │  └─ employees/
│  │  │     ├─ css/
│  │  │     │  └─ employees.css
│  │  │     └─ js/
│  │  │        └─ employees.js
│  │  └─ forms.py
│  ├─ schedules/
│  │  ├─ models.py
│  │  ├─ views.py
│  │  ├─ templates/schedules/...
│  │  └─ static/schedules/...
│  └─ ...
├─ templates/             # global templates
│  ├─ base.html
│  ├─ includes/
│  │  ├─ header.html
│  │  ├─ sidebar.html
│  │  └─ footer.html
├─ static/
│  ├─ css/
│  │  └─ theme.css
│  └─ js/
│     └─ global.js
```

> بهذا الشكل: نقل مجلد `apps/schedules` إلى مشروع آخر سيحافظ على الواجهات وملفات static الخاصة به.

---

# 4. قائمة الصفحات الأساسية (لكل صفحة: محتوى، عناصر UI، الأذونات)

سأعطي جدولًا مختصرًا لكل صفحة رئيسية، الحقول، الأزرار، وpermission المطلوب.

## 4.1. Dashboard — `/dashboard/`

* **محتوى:** KPIs (عدد الموظفين، طلبات الاعتماد المعلقة، نوبات غير مغطاة)، رسومات صغيرة (violations/month, coverage heatmap)، آخر الإشعارات.
* **UI:** Cards, Charts (Plotly/ChartJS)، Filters (region, period).
* **Permissions:** `can_view_dashboard` (عموم المستخدمين لديهم وصول للاطلاع، لكن البعض قد يرى بيانات منطقته فقط).
* **Actions:** تصدير تقرير، فتح صفحة Approvals/Reports.

## 4.2. Branches List / Detail — `/branches/` `/branches/<id>/`

* **List:** جدول مع Search + Filters (category A/B/C, working days).
* **Detail:** إعدادات الفرع، جدول الموظفين، أزرار: Edit, Configure Shifts.
* **Permissions:** `branches.view_branch`, `branches.change_branch`.

## 4.3. Employees List / Detail / Import — `/employees/`

* **List:** جدول مع أعمدة: emp\_number, name, branch, job\_title, status, actions (view/edit).
* **Import:** Upload CSV/Excel → Preview mapping modal → Start import job → show errors.
* **Detail:** Profile, assigned shifts, leaves, violations.
* **Permissions:** `employees.view_employee`, `employees.add_employee`, `employees.change_employee`.

## 4.4. Create Schedule (Wizard) — `/schedules/create/`

* **Steps:** 1) Select scope & dates, 2) Choose template or manual, 3) Assign staff for each slot (drag/drop or select), 4) Validate (show conflicts/warnings), 5) Preview & Submit.
* **UI Components:** Stepper, calendar grid/heatmap, drag-and-drop list (optional: use SortableJS), bulk-assign modal.
* **Permissions:** `schedules.add_schedule`, `schedules.change_schedule` (for editing drafts).
* **Client validation:** check date ranges, required fields.
* **Server validation:** rules (leave conflicts, hours limit).

## 4.5. Approvals — `/approvals/`

* **List:** Items awaiting approval for current user’s role.
* **Detail:** Approval timeline, Approve/Reject/Request Changes (modal for comment).
* **Permissions:** depends on role; e.g., `approvals.can_approve_region`, etc.

## 4.6. Leaves Management — `/leaves/`

* **List:** pending/approved/rejected, filter by employee/period.
* **Create:** form (type, dates, note, attach file).
* **Permissions:** employees can request leave (`leaves.add_leave`), managers can approve (`leaves.can_approve`).

## 4.7. Violations / Disciplinary — `/violations/`

* **Create:** form with type, date, description, action (warning/fine).
* **Dashboard panel:** monthly chart, archival auto-scheduler checkbox.
* **Permissions:** `violations.add_violation`, HR roles for archive.

## 4.8. Reports Generator — `/reports/`

* **UI:** filter panel (date range, branch category, employee, hours type), results table, Export (Excel/PDF).
* **Permissions:** `reports.view_reports`.

## 4.9. Integrations / Import Jobs — `/integrations/imports/`

* **List:** status, file, errors, replay.
* **Detail:** mapping preview, rows preview, error lines.
* **Permissions:** `integrations.manage_imports`.

---

# 5. مكونات واجهة قابلة لإعادة الاستخدام (Components)

* `Topbar` (header with notifications badge, user menu).
* `Sidebar` (collapsible, highlights active route).
* `Card` component (consistent look for KPI).
* `DataTable` wrapper (uses django-tables2 or custom table with server-side pagination + sorting).
* `Modal` standard (confirm, form modal).
* `Stepper` (wizard steps).
* `HeatmapCalendar` (custom component for coverage visualization).
* `ChartWrapper` (component لتغليف Plotly/ChartJS data).
* `BulkAssignPanel` (drag-drop staff to slots).
* `ImportPreviewTable` (show excel mapping).
* `AuditTrail` component (timeline view).

---

# 6. Navigation & Permissions UI Logic

* Sidebar shows items depending on user roles (use Django template tags or context processor).
* Example (in `templates/includes/sidebar.html`):

  ```django
  {% if perms.branches.view_branch %}
    <li class="{% if request.path startswith '/branches' %}active{% endif %}"><a href="{% url 'branches:list' %}">المعارض</a></li>
  {% endif %}
  ```
* Use a context processor `user_permissions` لجلب الأذونات الرئيسية لتسريع rendering.
* Active link highlighting via template tag `active` أو مقارنة `request.path`.

---

# 7. ملفات القوالب الأساسية (templates) — توصيف `base.html`

* `base.html` يحتوي على:

  * تحميل `theme.css`, `bootstrap.css`, `global.js`.
  * Blocks: `title`, `head_extra`, `page_header`, `content`, `scripts`.
* مثال مقتطف `base.html`:

```django
<!doctype html>
<html lang="{{ request.LANGUAGE_CODE }}" class="{% if LANGUAGE_CODE == 'ar' %}rtl{% endif %}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}نظام الجداول التشغيلية{% endblock %}</title>
  <link rel="stylesheet" href="{% static 'css/bootstrap.min.css' %}">
  <link rel="stylesheet" href="{% static 'css/theme.css' %}">
  {% block head_extra %}{% endblock %}
</head>
<body>
  {% include 'includes/header.html' %}
  <div class="container-fluid">
    <div class="row">
      {% include 'includes/sidebar.html' %}
      <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
        {% block page_header %}{% endblock %}
        {% block content %}{% endblock %}
      </main>
    </div>
  </div>
  <script src="{% static 'js/bootstrap.bundle.min.js' %}"></script>
  <script src="{% static 'js/global.js' %}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

---

# 8. استراتيجيات JavaScript & Progressive Enhancement

* اعتمد على **Progressive Enhancement**: الصفحات تعمل بدون JS (الأمور الأساسية) ثم أضف التحسينات عبر JS (AJAX, modals, drag-drop).
* استخدم Vanilla JS أو مكتبة خفيفة (Alpine.js) بدلاً من jQuery لتخفيف التحميل، لكن Bootstrap JS يعتمد على Vanilla. إذا تحتاج drag & drop استخدم `SortableJS` أو `dragula`.
* نقاط تفاعل JS شائعة:

  * Submit forms عبر AJAX مع feedback (success/error).
  * Live validation أثناء ملء الـwizard.
  * Bulk-assign modal: استدعاء endpoint لإحضار قائمة الموظفين (AJAX) ثم حفظ التعيينات.
  * Polling أو websocket (اختياري) لتحديث حالة Import jobs أو Approval queue (Django Channels إذا أردت realtime).

---

# 9. نمط وأسماء الملفات الثابتة (Naming Conventions)

* CSS: `appname.css` (مثال: `schedules.css`) داخل `apps/schedules/static/schedules/css/`.
* JS: `appname.js` داخل `apps/schedules/static/schedules/js/`.
* Templates: `apps/schedules/templates/schedules/<template>.html`.
* Template blocks consistent: `block page_header`, `block content`, `block scripts`.
* URL namespaces: كل app يملك `app_name = 'schedules'` و urls مع `name='create'` => `{% url 'schedules:create' %}`.

---

# 10. الأداء وملفات static

* اجمع و minify ملفات CSS/JS في production (use `django-compressor` أو build pipeline مع webpack / Vite).
* استخدم `preload` و `prefetch` للـfonts/critical assets.
* استخدم CDN للـ Bootstrap و مكتبات العامة (أو استضافة داخلية اعتماداً على سياسة الأمان).
* Images: استخدم WebP و lazy-loading (`loading="lazy"`).

---

# 11. اختبارات واجهة (Frontend QA)

* Unit tests للـtemplates: تأكد من وجود عناصر رئيسية على صفحتين/ثلاثة حالات (with/without perms).
* Integration (Selenium / Playwright): تدفقات حرجة:

  * تسجيل دخول → إنشاء جدول → Submit → مراجعة approval.
  * Upload Excel import → معالجة الأخطاء.
* Visual regression: Percy أو backstop.js لمقارنة screenshots بعد تغييرات CSS.
* Accessibility checks: axe-core (automated) + manual keyboard navigation.

---

# 12. قائمة مهام تفصيلية للمطور (Sprint-ready checklist)

* [ ] إعداد بيئة محلية ونسخة من `theme.css` وملف variables.
* [ ] إعداد `base.html` و includes (header, sidebar, footer).
* [ ] تنفيذ Sidebar + logic permission-based display.
* [ ] صفحة Dashboard: تصميم layout و3 KPIs + placeholder charts.
* [ ] Employees List & Detail: templates, table, filters, import UI.
* [ ] Branches List & Detail.
* [ ] Create Schedule Wizard (UI stepper) — 3 خطوات أولية + preview.
* [ ] Implement client-side validation + server validation messages display.
* [ ] Approvals list & detail (timeline UI).
* [ ] Leaves forms + interactions (modal attachments).
* [ ] Violations UI + monthly chart.
* [ ] Reports UI: filters + export buttons.
* [ ] Integrations: Import job UI + mapping modal.
* [ ] Implement reusable components (card, modal, table).
* [ ] Implement responsive breakpoints, test mobile/tablet.
* [ ] Add accessibility attributes (aria-\*, focus states).
* [ ] Add unit tests & integration tests for the above flows.
* [ ] Performance: minify & test Lighthouse.

---

# 13. مراقبة جودة التصميم (Design QA)

* اجعل لكل صفحة Style guide مختصر (typography, spacing, colors for headings/buttons).
* استخدم واحدة من إنظمة أيقونات: `lucide` أو `feather` بدلًا من صور أيقونات متعددة.
* اجعل كل زر ذو دور مهم `aria-label`، كل modal قابل للإغلاق عبر Escape، وإعطاء التركيز (focus) للحقل الأول عند الفتح.

---

# 14. أمثلة عملية سريعة (Template snippet + loadperms)

**Context processor** لتمرير permissions للمظهر:

```python
# project/context_processors.py
def user_permissions(request):
    if not request.user.is_authenticated:
        return {}
    perms = {
      'can_view_dashboard': request.user.has_perm('dashboard.view_dashboard'),
      'can_manage_branches': request.user.has_perm('branches.change_branch'),
      # add as needed
    }
    return {'user_perms': perms}
```

**Sidebar snippet**:

```django
<!-- templates/includes/sidebar.html -->
<nav id="sidebarMenu" class="col-md-3 col-lg-2 d-md-block bg-light sidebar collapse">
  <div class="position-sticky pt-3">
    <ul class="nav flex-column">
      {% if user_perms.can_view_dashboard %}
      <li class="nav-item">
        <a class="nav-link {% if request.path == '/dashboard/' %}active{% endif %}" href="{% url 'dashboard:index' %}">
          <span data-feather="home"></span> لوحة التحكم
        </a>
      </li>
      {% endif %}
      {% if perms.employees.view_employee %}
      <li class="nav-item">
        <a class="nav-link" href="{% url 'employees:list' %}">
          <span data-feather="users"></span> الموظفين
        </a>
      </li>
      {% endif %}
      <!-- more items -->
    </ul>
  </div>
</nav>
```

---

# 15. تسليمات الواجهة (Deliverables)

* مجلد `apps/*/templates/*` لكل app جاهز للانتقال.
* مجلد `apps/*/static/*` يحوي CSS و JS وAssets لكل app.
* `templates/base.html` و `templates/includes/*`.
* `static/css/theme.css` (ملف الألوان المركزي).
* Documentation: README front-end dev guide (how to run, how to change colors, how to add a template).
* اختبارين أو ثلاث end-to-end scripts (Playwright).

---

# 16. ملاحظات ختامية مهمة

* التزام واضح بفصل المسئوليات: من الأفضل أن يعمل الـFrontend Dev بالتنسيق مع Backend Dev لتحديد الjson endpoints التي يحتاجها (API للـwizard, approve actions, import status). لكن كل ما قدمناه يمكن تنفيذه باستخدام forms وviews على نمط Django التقليدي.
* عند الطلب أقدملك الآن:

