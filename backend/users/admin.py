from django.contrib import admin

from users.models import User


class UserAdmin(admin.ModelAdmin):
    search_fields = ['email', 'username']
    list_display = ('username', 'email', 'first_name', 'last_name')


admin.site.register(User, UserAdmin)
