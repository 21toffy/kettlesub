# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'mobile', 'is_staff_custom', 'is_superuser_custom')
    search_fields = ('email', 'username', 'mobile')
    ordering = ('email',)

    def is_staff_custom(self, obj):
        return obj.is_staff

    def is_superuser_custom(self, obj):
        return obj.is_superuser

    is_staff_custom.boolean = True
    is_staff_custom.short_description = 'Is Staff'

    is_superuser_custom.boolean = True
    is_superuser_custom.short_description = 'Is Superuser'

    list_filter = ('is_superuser', 'status')


admin.site.register(User, CustomUserAdmin)
