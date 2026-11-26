from django.contrib.admin.apps import AdminConfig


class SiraGoAdminConfig(AdminConfig):
    default_site = "config.admin_site.SiraGoAdminSite"
