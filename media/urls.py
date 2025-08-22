from django.urls import include, path

urlpatterns = [
    path("images/", include("media.features.image.urls")),
]
