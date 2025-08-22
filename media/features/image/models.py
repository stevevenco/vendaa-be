from django.conf import settings
from django.db import models

from utils.models import TrackObjectStateMixin


def generate_upload_path(user_id: str) -> str:
    return f"images/{user_id}/"


class Image(TrackObjectStateMixin):
    image_key = models.CharField(max_length=255, blank=True, null=True)
    original_file_name = models.TextField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"{self.image_key}"
