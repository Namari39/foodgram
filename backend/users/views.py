from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Subscription
from users.permissions import IsAuthenticatedOrReadOnly
from users.serializers import (
    AvatarSerializer,
    SubscriptionSerializer,
    UserDetailSerializer,
)


User = get_user_model()


class UserViewSet(UserViewSet):
    """Вью для пользователей, унаследованная от djoser."""

    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Информация о текущем аутентифицированном пользователе."""
        user = request.user
        serializer = UserDetailSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user.avatar = serializer.validated_data['avatar']
            user.save()
            avatar_url = (
                request.build_absolute_uri(
                    user.avatar.url
                ) if user.avatar else None
            )
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
                return Response(
                    {'detail': 'Аватар успешно удалён.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'detail': 'Аватар не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
        pagination_class=LimitOffsetPagination
    )
    def manage_subscription(self, request, id=None):
        user_to_manage = self.get_object()
        if user_to_manage == request.user:
            return Response(
                {'detail': 'Нельзя подписываться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                user=request.user,
                subscribed_to=user_to_manage
            )
            if created:
                serializer = SubscriptionSerializer(
                    user_to_manage,
                    context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=request.user,
                subscribed_to=user_to_manage
            )
            if subscription.exists():
                subscription.delete()
                return Response(
                    {'detail': 'Подписка отменена.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'detail': 'Подписки не существует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'Некорректный метод запроса.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated],
        pagination_class=LimitOffsetPagination
    )
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(
            user=request.user
        ).select_related('subscribed_to')
        subscribed_users = [
            subscription.subscribed_to for subscription in subscriptions
        ]
        serializer = UserDetailSerializer(
            subscribed_users,
            many=True,
            context={'request': request}
        )
        page = self.paginate_queryset(subscribed_users)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data, status=status.HTTP_200_OK)
