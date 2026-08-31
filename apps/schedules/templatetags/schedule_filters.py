from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def decimal_format(value):
    """تنسيق الأرقام العشرية باستخدام النقطة كفاصل"""
    if value is None:
        return "0.0"
    
    try:
        # تحويل إلى float ثم تنسيق
        float_value = float(value)
        return f"{float_value:.1f}"
    except (ValueError, TypeError):
        return "0.0"

@register.filter
def safe_decimal(value):
    """تنسيق آمن للأرقام العشرية"""
    if value is None or value == '':
        return "0.0"
    
    # إزالة الفواصل واستبدالها بنقاط
    if isinstance(value, str):
        value = value.replace(',', '.')
    
    try:
        float_value = float(value)
        return f"{float_value:.1f}"
    except (ValueError, TypeError):
        return "0.0"

@register.filter
def sum_entries_hours(entries):
    """حساب إجمالي الساعات لقائمة من الإدخالات"""
    if not entries:
        return 0
    try:
        return sum(float(entry.hours) for entry in entries)
    except (ValueError, TypeError, AttributeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """الحصول على قيمة من قاموس باستخدام المفتاح"""
    if dictionary is None:
        return None
    return dictionary.get(key)
