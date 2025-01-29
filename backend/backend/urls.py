from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from recipes import views


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path('auth/', include('djoser.urls.authtoken')),
    path('api/', include('api.urls')),
    path('api/', include('users.urls')),
    path(
        's/<str:short_link>/',
        views.redirect_short_link,
        name='redirect-short-link'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
