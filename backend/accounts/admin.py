from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Company, SupportRequest
from .notifications import notify
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


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ("__str__", "subject", "category", "status", "requester", "created_at")
    list_filter = ("status", "category", "created_at")
    search_fields = ("subject", "message", "requester__email", "requester__phone", "reference")
    readonly_fields = ("reference", "requester", "category", "subject", "message", "created_at", "updated_at")
    fields = readonly_fields + ("status", "reply")
    list_per_page = 25
    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def save_model(self, request, obj, form, change):
        super().save_model(request,obj,form,change)
        if change and {"reply","status"}.intersection(form.changed_data):
            notify(obj.requester_id,"SUPPORT","Votre demande d’assistance a été mise à jour",f"{obj} · {obj.get_status_display()}. Consultez votre centre d’assistance.")
