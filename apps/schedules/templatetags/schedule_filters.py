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
