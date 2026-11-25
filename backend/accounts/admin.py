from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
@admin.register(User)
class SiraGoUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("SiraGo", {"fields": ("role", "phone")}),)
