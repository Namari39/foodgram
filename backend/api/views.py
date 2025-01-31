import os
from dotenv import load_dotenv
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipesFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeCreateSerializer,
    FavoriteRecipeSerializer,
    ShoppingCartSerializer,
    ShortRecipesSerializer,
    TagSerializer,
)
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
)


load_dotenv()


class RecipesViewSet(viewsets.ModelViewSet):
    """Вью функция для рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    http_method_names = ['get', 'post', 'delete', 'patch']

    @staticmethod
    def add_to_list(
        request,
        recipe,
        model_class,
        serializer_class,
        success_message
    ):
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            if not model_class.objects.filter(
                user=request.user,
                recipe=recipe
            ).exists():
                serializer.save()
                recipe_serializer = ShortRecipesSerializer(recipe)
                return Response(
                    recipe_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'detail': success_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def remove_from_list(request, recipe, model_class):
        try:
            item = model_class.objects.get(user=request.user, recipe=recipe)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except model_class.DoesNotExist:
            return Response(
                {'detail': 'Рецепт не найден в списке.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        try:
            recipe = self.get_object()
            if request.method == 'POST':
                return self.add_to_list(
                    request,
                    recipe,
                    FavoriteRecipe,
                    FavoriteRecipeSerializer,
                    'Рецепт уже в избранном!'
                )
            return self.remove_from_list(request, recipe, FavoriteRecipe)
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Рецепт не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        try:
            recipe = self.get_object()
            if request.method == 'POST':
                return self.add_to_list(
                    request,
                    recipe,
                    ShoppingCart,
                    ShoppingCartSerializer,
                    'Рецепт уже в списке покупок!'
                )
            return self.remove_from_list(request, recipe, ShoppingCart)
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Рецепт не найден.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        try:
            recipe = self.get_object()
            link_suffix = recipe.short_link
            full_short_link = (
                f'''http://{os.getenv('DOMAIN_NAME')}/s/{link_suffix}'''
            )
            return Response(
                {'short-link': full_short_link},
                status=status.HTTP_200_OK
            )
        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """
        Скачивание списка покупок.
        """
        shopping_cart_recipes = request.user.recipes.all()
        ingredients = {}
        for recipe in shopping_cart_recipes:
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient_name = recipe_ingredient.ingredient.name
                measurement_unit = (
                    recipe_ingredient.ingredient.measurement_unit
                )
                amount = recipe_ingredient.amount
                key = f"{ingredient_name} ({measurement_unit})"
                if key in ingredients:
                    ingredients[key] += amount
                else:
                    ingredients[key] = amount
        response_content = "Список покупок:\n\n"
        for ingredient, amount in ingredients.items():
            response_content += f"{ingredient} — {amount}\n"
        response = HttpResponse(response_content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вью для тегов."""

    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вью для ингредиентов."""

    queryset = Ingredient.objects.all()
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
