
from django import template
from django.urls import resolve, reverse

register = template.Library()

@register.inclusion_tag('partials/breadcrumbs.html', takes_context=True)
def render_breadcrumbs(context):
    request = context['request']
    breadcrumbs = []
    for path in request.session.get('breadcrumbs', []):
        try:
            match = resolve(path)
            name = match.url_name.replace('_', ' ').title() if match.url_name else path
            breadcrumbs.append({'name': name, 'url': path})
        except:
            pass
    return {'breadcrumbs': breadcrumbs}
