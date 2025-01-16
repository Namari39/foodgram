import os
from dotenv import load_dotenv
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipesFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeSerializer,
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
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
                created = FavoriteRecipe.objects.get_or_create(
                    user=request.user,
                    recipe=recipe
                )
                if created[1]:
                    serializer = ShortRecipesSerializer(recipe)
                    return Response(
                        serializer.data, status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        {'message': 'Рецепт уже в избранном!'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif request.method == 'DELETE':
                favorite_recipe = FavoriteRecipe.objects.get(
                    user=request.user,
                    recipe=recipe
                )
                favorite_recipe.delete()
                return Response(
                    {'message': 'Рецепт удален из избранного!'},
                    status=status.HTTP_204_NO_CONTENT
                )
        except FavoriteRecipe.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
                created = ShoppingCart.objects.get_or_create(
                    user=request.user,
                    recipe=recipe
                )
                if created[1]:
                    serializer = ShortRecipesSerializer(recipe)
                    return Response(
                        serializer.data, status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        {'message': 'Рецепт уже в списке покупок!'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif request.method == 'DELETE':
                shopping_cart_item = ShoppingCart.objects.get(
                    user=request.user,
                    recipe=recipe
                )
                shopping_cart_item.delete()
                return Response(
                    {'message': 'Рецепт удален из списка покупок!'},
                    status=status.HTTP_204_NO_CONTENT
                )
        except ShoppingCart.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
                f"http://{os.getenv('DOMAIN_NAME', 'localhost')}/s/{link_suffix}"
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
        user_recipes = request.user.recipes.all()
        ingredients = {}

        for recipe in user_recipes:
            for recipe_ingredient in recipe.ingredients.all():
                ingredient_name = recipe_ingredient.ingredient.name
                amount = recipe_ingredient.amount
                if ingredient_name in ingredients:
                    ingredients[ingredient_name] += amount
                else:
                    ingredients[ingredient_name] = amount
        response_content = ""
        for ingredient, amount in ingredients.items():
            measurement_unit = recipe_ingredient.ingredient.measurement_unit
            response_content += (
                f"{ingredient} ({measurement_unit}) — {amount}\n"
            )
        response = HttpResponse(response_content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


class TagViewSet(viewsets.ModelViewSet):
    """Вью для тегов."""

    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = TagSerializer
    http_method_names = ['get']


class IngredientViewSet(viewsets.ModelViewSet):
    """Вью для ингредиентов."""

    queryset = Ingredient.objects.all()
    permission_classes = [AllowAny]
    pagination_class = None
    serializer_class = IngredientSerializer
    http_method_names = ['get']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
