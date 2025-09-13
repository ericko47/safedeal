

import os

class BreadcrumbMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'breadcrumbs' not in request.session:
            request.session['breadcrumbs'] = []

        path = request.path

        # Skip AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.get_response(request)

        # Skip static & media files
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # Skip file extensions (.jpg, .png, .pdf, .css, .js, etc.)
        _, ext = os.path.splitext(path)
        if ext.lower() in [
            '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
            '.pdf', '.css', '.js'
        ]:
            return self.get_response(request)

        breadcrumbs = request.session['breadcrumbs']

        # If the path already exists, remove it (to avoid duplicates)
        if path in breadcrumbs:
            breadcrumbs.remove(path)

        # Add it at the end
        breadcrumbs.append(path)

        # Limit trail length
        if len(breadcrumbs) > 5:
            breadcrumbs.pop(0)

        request.session['breadcrumbs'] = breadcrumbs
        request.session.modified = True

        return self.get_response(request)

