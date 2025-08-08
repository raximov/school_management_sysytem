from django import template

register = template.Library()

@register.filter
def total_score(queryset, field):
    return round(sum(getattr(obj, field, 0) for obj in queryset), 2)
