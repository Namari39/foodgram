from rest_framework.pagination import PageNumberPagination


class ApiPagination(PageNumberPagination):
    """Пагинация для постов, с максимальным лимитом."""

    page_size_query_param = 'limit'
