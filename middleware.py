
from django.shortcuts import redirect
from django.urls import resolve


class AttendEaseAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Static files ko allow karo
        if path.startswith(("/static/", "/media/")):
            return self.get_response(request)

        try:
            url_name = resolve(path).url_name
        except Exception:
            url_name = None

        # Login, registration aur logout routes
        public_urls = {"login", "student_register"}

        if url_name in public_urls:
            return self.get_response(request)

        # Login nahi hai to login page par bhejo
        if not request.user.is_authenticated:
            return redirect("login")

        # Student ko sirf apna profile aur logout allow hai
        if not (request.user.is_staff or request.user.is_superuser):
            if url_name not in {"student_profile", "logout"}:
                return redirect("student_profile")

        return self.get_response(request)
