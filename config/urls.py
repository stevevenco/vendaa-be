from django.conf import settings
from django.contrib.staticfiles.urls import static, staticfiles_urlpatterns
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

import authentication.urls as auth_url
import media.urls as media_url
from config.admin import admin_site

schema_view = get_schema_view(
    openapi.Info(
        title="Vendaa API",
        default_version="v1",
        description="A list of testable endpoints for Vendaa.",
    ),
    public=True,
    permission_classes=[permissions.IsAdminUser],
)

urlpatterns = [
    path("admin/", admin_site.urls),
    path(
        "api/v1/",
        include(
            [
                path("auth/", include(auth_url)),
                path("media/", include(media_url)),
            ]
        ),
    ),
    path(
        "doccer/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]


if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
