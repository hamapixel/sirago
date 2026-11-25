from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Company
@admin.register(User)
class SiraGoUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("SiraGo", {"fields": ("role", "phone")}),)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "owner", "status", "created_at")
    list_filter = ("status", "city")
    search_fields = ("name", "owner__phone", "owner__email")
    readonly_fields = ("created_at", "owner")
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
