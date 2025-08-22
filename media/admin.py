from django.contrib import admin

from config.admin import admin_site
from media.features.image.models import Image


class ImagesAdmin(admin.ModelAdmin):
    list_display = [
        "original_file_name",
        "uploaded_by",
        "created",
    ]
    search_fields = [
        "original_file_name",
        "uploaded_by",
    ]
    list_filter = [
        "uploaded_by",
    ]
    readonly_fields = [
        "uuid",
        "image_key",
        "uploaded_by",
        "original_file_name",
    ]
    ordering = ["-created"]

    # def has_add_permission(self, request):
    #     # Disable manual addition of Images through
    # the admin interface, since uploads are managed via API.
    #     return False


admin_site.register(Image, ImagesAdmin)
