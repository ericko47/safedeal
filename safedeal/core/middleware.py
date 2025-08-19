
# class BreadcrumbMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         if 'breadcrumbs' not in request.session:
#             request.session['breadcrumbs'] = []

#         path = request.path
#         if not request.is_ajax() and path not in request.session['breadcrumbs']:
#             # Avoid duplicate consecutive paths
#             if not request.session['breadcrumbs'] or request.session['breadcrumbs'][-1] != path:
#                 request.session['breadcrumbs'].append(path)

#             # Limit history length
#             if len(request.session['breadcrumbs']) > 5:
#                 request.session['breadcrumbs'].pop(0)

#             request.session.modified = True

#         return self.get_response(request)
# core/middleware.py

# class BreadcrumbMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         if 'breadcrumbs' not in request.session:
#             request.session['breadcrumbs'] = []

#         path = request.path

#         # Check if it's NOT an AJAX request
#         is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
#         if not is_ajax and path not in request.session['breadcrumbs']:
#             # Avoid duplicate consecutive paths
#             if not request.session['breadcrumbs'] or request.session['breadcrumbs'][-1] != path:
#                 request.session['breadcrumbs'].append(path)

#             # Limit history length
#             if len(request.session['breadcrumbs']) > 5:
#                 request.session['breadcrumbs'].pop(0)

#             request.session.modified = True

#         return self.get_response(request)
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

# import os
# import re

# class BreadcrumbMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         if 'breadcrumbs' not in request.session:
#             request.session['breadcrumbs'] = []

#         path = request.path

#         # Skip AJAX requests
#         is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
#         if is_ajax:
#             return self.get_response(request)

#         # Skip static & media files
#         if path.startswith('/static/') or path.startswith('/media/'):
#             return self.get_response(request)

#         # Skip file extensions
#         _, ext = os.path.splitext(path)
#         if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.pdf', '.css', '.js']:
#             return self.get_response(request)

#         # Only include public-facing routes
#         public_patterns = [
#             r'^/$',                # Home
#             r'^/dashboard/?$',     # Dashboard
#             r'^/items/',           # Item details/listing
#             r'^/services/',        # Service listings
#             r'^/transactions/',    # Transactions page
#             r'^/cart/',            # Cart
#             r'^/checkout/',        # Checkout
#             r'^/contact/',         # Contact page
#             r'^/about/',           # About page
#             r'^/faq/',             # FAQ
#         ]
#         if not any(re.match(pattern, path) for pattern in public_patterns):
#             return self.get_response(request)

#         # Avoid duplicate consecutive paths
#         if not request.session['breadcrumbs'] or request.session['breadcrumbs'][-1] != path:
#             request.session['breadcrumbs'].append(path)

#         # Limit history length
#         if len(request.session['breadcrumbs']) > 5:
#             request.session['breadcrumbs'].pop(0)

#         request.session.modified = True

#         return self.get_response(request)
