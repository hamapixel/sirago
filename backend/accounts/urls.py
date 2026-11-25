from django.urls import path
from . import views, agent_views
urlpatterns = [
    path("csrf/", views.csrf),
    path("register/traveler/", views.register_traveler),
    path("register/company/", views.register_company),
    path("login/", views.sign_in),
    path("logout/", views.sign_out),
    path("me/", views.me),
    path("profile/", views.update_traveler_profile),
    path("password/", views.change_traveler_password),
    path("company/", views.company_account),
    path("company/profile/", views.update_company_profile),
    path("company/password/", views.change_company_password),
    path("company/agents/", agent_views.agents),
    path("company/agents/<int:pk>/", agent_views.agent_update),
]
