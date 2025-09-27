# نظام إدارة الجداول التشغيلية

نظام ويب متكامل لإدارة النوبات والجداول التشغيلية لعدة معارض وفروع، مبني باستخدام Django 5.2.

## الميزات الرئيسية

- **إدارة الموظفين والمعارض**: تصنيف المعارض (A/B/C) وإدارة بيانات الموظفين
- **نظام الجداول الذكي**: إنشاء جداول مرنة مع منع التداخلات
- **نظام الموافقات المتقدم**: مسارات موافقات قابلة للتخصيص
- **التقارير والتحليلات**: لوحة تحكم تفاعلية مع KPIs
- **الاستيراد والتصدير**: استيراد بيانات من Excel/CSV
- **نظام الإشعارات**: تنبيهات فورية للطلبات المعلقة

## التقنيات المستخدمة

- **Backend**: Django 5.2, Django REST Framework
- **Frontend**: Django Templates, Bootstrap 5
- **Database**: PostgreSQL (SQLite للتطوير)
- **Cache**: Redis
- **Background Tasks**: Celery
- **Authentication**: Django Guardian

## التثبيت

### المتطلبات

- Python 3.8+
- PostgreSQL 12+
- Redis 6+

### خطوات التثبيت

1. **استنساخ المشروع**
```bash
python manage.py runserver 0.0.0.0:5000
git clone <repository-url>
cd worktable_system
```

2. **إنشاء بيئة افتراضية**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows
```

3. **تثبيت المتطلبات**
```bash
pip install -r requirements.txt
```

4. **إعداد متغيرات البيئة**
```bash
cp env.sample .env
# قم بتعديل ملف .env حسب احتياجاتك
```

5. **تشغيل Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **إنشاء مستخدم إداري**
```bash
python manage.py createsuperuser
```

7. **تشغيل الخادم**
```bash
python manage.py runserver
```

## هيكل المشروع

```
worktable_system/
├── apps/                    # التطبيقات
│   ├── users/              # إدارة المستخدمين
│   ├── employees/          # إدارة الموظفين
│   ├── branches/           # إدارة المعارض
│   ├── schedules/          # الجداول التشغيلية
│   ├── leaves/             # الإجازات
│   ├── approvals/          # الموافقات
│   ├── violations/         # المخالفات
│   ├── reports/            # التقارير
│   ├── integrations/       # الاستيراد والتصدير
│   └── auditlog/           # سجل التدقيق
├── config/                 # إعدادات المشروع
│   └── settings/
├── templates/              # قوالب HTML
├── static/                 # الملفات الثابتة
├── requirements.txt        # متطلبات Python
└── manage.py              # إدارة Django
```

## التطوير

### تشغيل في وضع التطوير

```bash
python manage.py runserver --settings=config.settings.dev
```

### تشغيل الاختبارات

```bash
python manage.py test
```

### تشغيل Celery

```bash
celery -A worktable_system worker -l info
celery -A worktable_system beat -l info
```

## النشر

### إعدادات الإنتاج

```bash
python manage.py runserver --settings=config.settings.prod
```

### متغيرات البيئة المطلوبة

- `SECRET_KEY`: مفتاح Django السري
- `DEBUG`: وضع التطوير (False للإنتاج)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: إعدادات قاعدة البيانات
- `REDIS_URL`: رابط Redis
- `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`: إعدادات البريد

## المساهمة

1. Fork المشروع
2. إنشاء فرع للميزة الجديدة
3. Commit التغييرات
4. Push إلى الفرع
5. إنشاء Pull Request

## الترخيص

هذا المشروع مرخص تحت رخصة MIT.

## الصفحات والواجهات

### الصفحات الرئيسية
- **لوحة التحكم**: `/dashboard/` - الصفحة الرئيسية مع KPIs والإحصائيات
- **تسجيل الدخول**: `/login/` - صفحة تسجيل الدخول مع حسابات تجريبية

### إدارة الموظفين
- **قائمة الموظفين**: `/employees/` - عرض وإدارة جميع الموظفين
- **إضافة موظف**: `/employees/create/` - نموذج إضافة موظف جديد
- **تفاصيل الموظف**: `/employees/<id>/` - عرض تفاصيل موظف محدد
- **تعديل الموظف**: `/employees/<id>/edit/` - تعديل بيانات الموظف

### إدارة المعارض
- **قائمة المعارض**: `/branches/` - عرض جميع المعارض والفروع
- **إضافة فرع**: `/branches/create/` - إضافة فرع جديد
- **تفاصيل الفرع**: `/branches/<id>/` - تفاصيل الفرع مع الإحصائيات
- **تعديل الفرع**: `/branches/<id>/edit/` - تعديل بيانات الفرع

### الجداول التشغيلية
- **قائمة الجداول**: `/schedules/` - عرض جميع الجداول التشغيلية
- **إنشاء جدول**: `/schedules/create/` - معالج إنشاء جدول جديد (4 خطوات)
- **تفاصيل الجدول**: `/schedules/<id>/` - عرض تفاصيل الجدول
- **تعديل الجدول**: `/schedules/<id>/edit/` - تعديل الجدول

### إدارة الإجازات
- **قائمة الإجازات**: `/leaves/` - عرض جميع طلبات الإجازات
- **طلب إجازة**: `/leaves/create/` - نموذج طلب إجازة جديد
- **تفاصيل الإجازة**: `/leaves/<id>/` - تفاصيل طلب الإجازة

### نظام الموافقات
- **الموافقات المعلقة**: `/approvals/` - عرض الموافقات المعلقة
- **تفاصيل الموافقة**: `/approvals/<id>/` - تفاصيل طلب الموافقة

### التقارير والتحليلات
- **التقارير**: `/reports/` - مولد التقارير والإحصائيات
- **إنشاء تقرير**: `/reports/create/` - إنشاء تقرير مخصص

### إدارة المستخدمين
- **قائمة المستخدمين**: `/users/` - عرض وإدارة جميع المستخدمين
- **إضافة مستخدم**: `/users/create/` - إضافة مستخدم جديد
- **تفاصيل المستخدم**: `/users/<id>/` - عرض تفاصيل مستخدم محدد
- **تعديل المستخدم**: `/users/<id>/edit/` - تعديل بيانات مستخدم
- **حذف المستخدم**: `/users/<id>/delete/` - حذف مستخدم

### الملف الشخصي
- **الملف الشخصي**: `/profile/` - عرض الملف الشخصي
- **تعديل الملف**: `/profile/edit/` - تعديل البيانات الشخصية
- **تغيير كلمة المرور**: `/profile/change-password/` - تغيير كلمة المرور

### الحسابات التجريبية
- **مدير عام**: `admin` / `admin123`
- **مدير فرع**: `manager1` / `password123`
- **منسق**: `coordinator1` / `password123`
- **موظف**: `employee1` / `password123`

## الدعم

للحصول على الدعم، يرجى فتح issue في GitHub أو التواصل مع فريق التطوير.