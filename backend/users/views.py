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
    DetailSubscriptionSerializer
)


User = get_user_model()


class UserViewSet(UserViewSet):
    """Вью для пользователей, унаследованная от djoser."""

    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
            return Response(
                {'detail': 'Аватар успешно удален.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
        pagination_class=LimitOffsetPagination
    )
    def manage_subscription(self, request, id=None):
        user_to_subscribe = self.get_object()
        if request.method == 'POST':
            serializer = SubscriptionSerializer(data={
                'user': request.user.id,
                'subscribed_to': user_to_subscribe.id
            })
            serializer.is_valid(raise_exception=True)
            serializer.save()
            detail_serializer = DetailSubscriptionSerializer(
                user_to_subscribe,
                context={'request': request}
            )
            response_data = detail_serializer.data
            response_data['is_subscribed'] = True
            return Response(response_data, status=status.HTTP_201_CREATED)
        try:
            subscription = Subscription.objects.get(
                user=request.user,
                subscribed_to=user_to_subscribe
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response(
                {"detail": "Ваша подписка не найдена."},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated],
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
            serializer = DetailSubscriptionSerializer(
                page, many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data, status=status.HTTP_200_OK)
