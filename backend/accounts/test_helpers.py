"""Fixtures for tests of business endpoints after successful administrator MFA."""
from accounts.models import AdminMFA
from accounts.mfa import VERIFIED


def force_mfa_login(client, user):
    """Model a verified session in tests; actual MFA is covered in test_mfa."""
    if not user.is_superuser:
        raise ValueError("Expected a superuser")
    state, _ = AdminMFA.objects.get_or_create(user=user, defaults={"enabled": True})
    if not state.enabled:
        raise ValueError("Expected an enabled MFA state")
    client.force_login(user)
    session = client.session
    session[VERIFIED] = str(state.version)
    session.save()
