from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User


class SubscriptionCountFilter(admin.SimpleListFilter):
    title = 'Подписки на'
    parameter_name = 'has_subscription'

    def lookups(self, request, model_admin):
        return (
            (True, 'Есть подписка'),
            (False, 'Нет подписки'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(subscriptions__isnull=False).distinct()
        if self.value() == 'False':
            return queryset.filter(subscriptions__isnull=True).distinct()
        return queryset


class UserAdmin(BaseUserAdmin):
    """Админ панель для пользователей."""

    search_fields = ['email', 'username']
    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = (SubscriptionCountFilter,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('subscriptions')


admin.site.register(User, UserAdmin)
