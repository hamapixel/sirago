"""Django administration is reserved for active SiraGo superusers."""
from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError


class SiraGoAdminAuthenticationForm(AdminAuthenticationForm):
    def clean(self):
        # Import at request time to avoid app-loading dependencies.
        from accounts.views import limited
        if self.request is not None and limited(self.request, "django-admin-login", 10):
            raise ValidationError(
                "Trop de tentatives. Réessayez dans quelques minutes.",
                code="rate_limited",
            )
        return super().clean()

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise self.get_invalid_login_error()


class SiraGoAdminSite(AdminSite):
    login_form = SiraGoAdminAuthenticationForm

    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser

