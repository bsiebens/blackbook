from django import template

from ..utilities import format_iban

register = template.Library()

@register.filter 
def iban(value):
    return format_iban(value)