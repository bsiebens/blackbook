from django import template
from django.urls import resolve

register = template.Library()


@register.simple_tag(takes_context=True)
def is_active(context, value):
    url = context.request.path
    url_name = resolve(url)

    if url_name.url_name == value:
        return "is-active"
    return None