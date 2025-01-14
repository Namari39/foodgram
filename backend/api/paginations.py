from rest_framework.pagination import LimitOffsetPagination


class ApiPagination(LimitOffsetPagination):
    """Пагинация для постов, с максимальным лимитом."""

    default_limit = 10
    max_limit = 100
