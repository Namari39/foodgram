from django.contrib import admin
from django.db.models import Count

from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    """Поле отображения ингредиентов в редактировании рецепта."""

    model = RecipeIngredient
    extra = 1
    fields = ('ingredient', 'amount',)
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


class RecipeAdmin(admin.ModelAdmin):
    """Админ панель рецептов."""

    search_fields = ['name', 'author__username']
    list_filter = ('tags',)
    list_select_related = ('author',)
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'author', 'cooking_time', 'favorite_count')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(favorite_count=Count('favoriterecipe'))
        return queryset

    def favorite_count(self, obj):
        return obj.favorite_count
    favorite_count.short_description = 'Количество в избранных'


class IngredientAdmin(admin.ModelAdmin):
    """Админ панель ингредиентов."""

    search_fields = ['name']
    list_display = ('name', 'measurement_unit')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
