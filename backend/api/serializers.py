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
        fields = ['id', 'name', 'measurement_unit']


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


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


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    ingredients = RecipeIngredientSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    author = UserDetailSerializer(read_only=True)
    image = serializers.ImageField(required=True, allow_null=False)
    is_favorited = serializers.SerializerMethodField(default=False)
    is_in_shopping_cart = serializers.SerializerMethodField(default=False)

    class Meta:
        model = Recipe
        fields = ['id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'name',
                  'image',
                  'text',
                  'cooking_time']

    def to_internal_value(self, data):
        if 'image' in data and data['image']:
            data['image'] = self.handle_image_upload(data['image'])
        return super().to_internal_value(data)

    def handle_image_upload(self, image_data):
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        img = ContentFile(base64.b64decode(imgstr), name=f"recipe_image.{ext}")
        return img

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient_data)
        recipe.tags.set(tags_data)
        return recipe

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['id'] = instance.id
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        representation['image'] = (
            instance.image.url if instance.image else None
        )
        return representation

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

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        tags_data = validated_data.pop('tags', [])
        if len(ingredients_data) < 1:
            raise serializers.ValidationError(
                "Количество ингредиентов не может быть меньше 1."
            )
        ingredient_ids = [
            ingredient['ingredient'] for ingredient in ingredients_data
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Список ингредиентов содержит дубликаты."
            )
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ingredients_data:
            instance.ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance, **ingredient_data
                )
        if tags_data:
            tag_ids = [tag.id for tag in tags_data]
            tag_objects = Tag.objects.filter(id__in=tag_ids)
            instance.tags.set(tag_objects)
        return instance


class ShortRecipesSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для рецептов."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']
