from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()

@register.filter
def call_with(obj, arg):
    """Вызывает метод obj.method(arg)"""
    if hasattr(obj, 'get_image'):
        return obj.get_image(arg)
    return None


@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))