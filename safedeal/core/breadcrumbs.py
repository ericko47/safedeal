from django.urls import reverse, resolve

class NavigationTrailMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if hasattr(request, "_navigation_trail"):
            request.session["navigation_trail"] = request._navigation_trail
        else:
            # Default: just keep the last visited view
            resolver_match = resolve(request.path_info)
            trail = request.session.get("navigation_trail", [])
            url_name = resolver_match.url_name
            if url_name:
                trail.append({"name": url_name, "url": request.path})
                request.session["navigation_trail"] = trail[-5:]  # keep last 5 only

        return response

def set_breadcrumbs(request, crumbs):
    """
    Set explicit breadcrumbs on the request.
    Example crumbs:
    [
        ("Home", "index"),
        ("Items", "items_list"),
        ("Item Title", None),   # last item has no URL
    ]
    """
    breadcrumb_list = []
    for name, url_name in crumbs:
        if url_name:
            breadcrumb_list.append({
                "name": name,
                "url": reverse(url_name),
            })
        else:
            breadcrumb_list.append({
                "name": name,
                "url": "",
            })

    request._explicit_breadcrumbs = breadcrumb_list
    
class BreadcrumbMixin:
    """
    Add to a CBV to set breadcrumbs easily.
    Define `breadcrumbs` on the view as a list of (name, url_name).
    Example:
        breadcrumbs = [
            ("Home", "index"),
            ("Dashboard", "dashboard"),
            ("Profile", None),
        ]
    """
    breadcrumbs = []

    def dispatch(self, request, *args, **kwargs):
        if self.breadcrumbs:
            from django.urls import reverse
            breadcrumb_list = []
            for name, url_name in self.breadcrumbs:
                if url_name:
                    breadcrumb_list.append({"name": name, "url": reverse(url_name)})
                else:
                    breadcrumb_list.append({"name": name, "url": ""})
            request._explicit_breadcrumbs = breadcrumb_list
        return super().dispatch(request, *args, **kwargs)