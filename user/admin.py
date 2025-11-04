from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from user.models import User, Notification


# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'role')
    search_fields = ('username', 'email')
    list_filter = ('role',)
admin.site.register(Notification)