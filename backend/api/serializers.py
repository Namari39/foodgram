import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag
)
from users.serializers import UserDetailSerializer


User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентв."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор связанных моделей."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount', 'name', 'measurement_unit']


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = RecipeIngredientSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    image = serializers.ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def to_internal_value(self, data):
        if 'image' in data and data['image']:
            data['image'] = self.handle_image_upload(data['image'])
        return super().to_internal_value(data)

    def handle_image_upload(self, image_data):
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        img = ContentFile(base64.b64decode(imgstr), name=f"recipe_image.{ext}")
        return img

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError("Ингредиенты обязательны.")
        ingredient_ids = [
            ingredient['ingredient'] for ingredient in ingredients
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Список ингредиентов содержит дубликаты."
            )
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    "Количество ингредиента должно быть больше 0."
                )
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError("Теги обязательны.")
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                "Список тегов содержит дубликаты."
            )
        text = data.get('text')
        if not text:
            raise serializers.ValidationError("Описание обязательно.")
        cooking_time = data.get('cooking_time')
        if cooking_time is not None and cooking_time < 1:
            raise serializers.ValidationError(
                "Время приготовления должно быть больше 0."
            )
        return data

    @staticmethod
    def handle_ingredients_and_tags(instance, ingredients_data, tags_data):
        if ingredients_data:
            instance.recipe_ingredients.all().delete()
            recipe_ingredients = [
                RecipeIngredient(recipe=instance, **ingredient_data)
                for ingredient_data in ingredients_data
            ]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        if tags_data:
            instance.tags.set(tags_data)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        tags_data = validated_data.pop('tags', [])
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        self.handle_ingredients_and_tags(recipe, ingredients_data, tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.handle_ingredients_and_tags(instance, ingredients_data, [])
        if tags_data is not None:
            instance.tags.set(tags_data)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения и отображения рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    author = UserDetailSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteRecipe.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False


class ShortRecipesSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для рецептов."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ['user', 'recipe']


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ['user', 'recipe']
