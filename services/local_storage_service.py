import os

from django.conf import settings
from django.core.files.storage import default_storage


def upload_file_to_local(file, file_path):
    try:
        path = default_storage.save(file_path, file)
        return os.path.join(settings.MEDIA_URL, path)
    except Exception as e:
        print(f"Local upload failed: {e}")
        return None
