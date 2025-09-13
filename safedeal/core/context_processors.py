
# def build_breadcrumbs(request):
#     path = request.path.strip("/")
#     parts = path.split("/") if path else []
#     breadcrumbs = []
#     url = "/"

#     for part in parts:
#         url += part + "/"
#         breadcrumbs.append({
#             "name": part.replace("-", " ").capitalize(),
#             "url": url
#         })

#     return breadcrumbs


# def breadcrumbs(request):
#     """
#     Default breadcrumb builder (URL-based).
#     Can be overridden in views by passing `breadcrumbs` in context.
#     """
#     # if a view explicitly set breadcrumbs, respect that
#     if hasattr(request, "_explicit_breadcrumbs"):
#         return {"breadcrumbs": request._explicit_breadcrumbs}

#     return {"breadcrumbs": build_breadcrumbs(request)}

from django.urls import resolve

IGNORED_PATHS = ["/static/", "/media/"]

def prettify_name(name: str) -> str:
    """
    Convert a url_name like 'item_detail' → 'Item',
    'items_list' → 'Items', 'checkout' → 'Checkout'.
    """
    if not name:
        return "Home"
    # Special cleanup rules
    if name.endswith("_detail"):
        name = name.replace("_detail", "")
    if name.endswith("_list"):
        name = name.replace("_list", "s")
    return name.replace("_", " ").title()


def breadcrumbs(request):
    if "breadcrumbs" not in request.session:
        request.session["breadcrumbs"] = []

    breadcrumbs = request.session["breadcrumbs"]

    path = request.path
    # Skip static/media/ajax
    if any(path.startswith(p) for p in IGNORED_PATHS):
        return {"breadcrumbs": breadcrumbs}
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return {"breadcrumbs": breadcrumbs}

    # Resolve URL name
    try:
        match = resolve(path)
        url_name = match.url_name
    except:
        url_name = None

    crumb_name = prettify_name(url_name or path.strip("/"))

    # Avoid duplicates if last entry is same page
    if not breadcrumbs or breadcrumbs[-1]["url"] != path:
        breadcrumbs.append({"name": crumb_name, "url": path})

    # Limit length (keep last 5)
    if len(breadcrumbs) > 5:
        breadcrumbs.pop(0)

    request.session["breadcrumbs"] = breadcrumbs
    return {"breadcrumbs": breadcrumbs}

def navigation_trail(request):
    return {
        "navigation_trail": request.session.get("navigation_trail", [])
    }