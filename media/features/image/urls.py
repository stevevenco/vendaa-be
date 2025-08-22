from django.urls import path

from media.api.image import (
    # GetDeleteImageView,
    ImageUploadView,
)

urlpatterns = [
    path("upload/", ImageUploadView.as_view(), name="upload_image"),
    # path(
    #     "<uuid:image_id>/",
    #     GetDeleteImageView.as_view(),
    #     name="get_delete_image",
    # ),
    # path("<uuid:image_id>/", DeleteImageView.as_view(), name="delete-image"),
]
