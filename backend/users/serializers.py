import base64
import os

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from rest_framework import serializers

from recipes.models import Recipe
from users.models import Subscription


User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    """Сериализатор для создания пользователей."""

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'password'
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('avatar', None)
        return representation


class UserDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра деталей пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_subscribed_to(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                subscribed_to=obj
            ).exists()
        return False

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                subscribed_to=obj
            ).exists()
        return False


class AvatarSerializer(serializers.Serializer):
    """Сериализатор для изменения аватара."""

    avatar = serializers.CharField()

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        base64_data = validated_data['avatar'].split(",")[1]
        image_data = base64.b64decode(base64_data)
        file_name = f"avatar_{os.urandom(16).hex()}.png"
        image_file = ContentFile(image_data, name=file_name)
        validated_data['avatar'] = image_file
        return validated_data


class ShortRecipesSerializer(serializers.ModelSerializer):
    """Сокращенный сериализатор для рецептов в подписках."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    recipes = ShortRecipesSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'avatar',
            'recipes_count'
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                subscribed_to=obj
            ).exists()
        return False

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def to_representation(self, instance):
        recipes_limit = self.context[
            'request'
        ].query_params.get('recipes_limit')
        representation = super().to_representation(instance)
        if recipes_limit:
            limit = int(recipes_limit)
            representation['recipes'] = representation['recipes'][:limit]
        return representation
