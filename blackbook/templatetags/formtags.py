from django import template

register = template.Library()


@register.inclusion_tag("blackbook/templatetags/form_field.html")
def form_field(field, alt_label=None):
    if alt_label is not None:
        field.label = alt_label

    upload = False
    if field.field.widget.__class__.__name__ == "ClearableFileInput":
        upload = True

    return {"field": field, "upload": upload}


@register.filter
def add_class(field):
    css_class = []
    data_type = []

    if field.errors:
        css_class.append("is-danger")

    if field.widget_type in ("tag", "text", "email", "password", "number", "date"):
        css_class.append("input")

        if field.name == "tags":
            data_type.append("tags")

    return field.as_widget(attrs={"class": " ".join(css_class), "data-type": " ".join(data_type)})