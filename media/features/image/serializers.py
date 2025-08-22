from rest_framework import serializers

from media.features.image.models import Image
from services.image_service import ImageService

image_service = ImageService()


class ImageUploadSerializer(serializers.Serializer):
    """
    Serializer for handling image upload validation.
    """

    images = serializers.ListField(
        child=serializers.FileField(
            max_length=10_000_000,  # 10MB
            allow_empty_file=False,
            use_url=False,
        )
    )

class ImageSerializer(serializers.ModelSerializer):
    # For fetching image data
    class Meta:
        model = Image
        fields = [
            "uuid",
            "image_key",
            "original_file_name",
            "uploaded_by",
        ]
        read_only_fields = fields  # All fields read-only for fetching


class ImageDeleteSerializer(serializers.Serializer):
    image_uuid = serializers.UUIDField()

    def validate_image_uuid(self, image_uuid):
        if not Image.objects.filter(
            uuid=image_uuid, uploaded_by=self.context["request"].user.uuid
        ).exists():
            raise serializers.ValidationError(
                "Image not found or you do not have access."
            )

        return image_uuid


class GetImagesSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = [
            "uuid",
            "image_key",
            "created",
            "image_url",
        ]

    def get_image_url(self, obj):
        # Dynamically fetch the image URL based on the image_key
        return image_service.get_image_url(obj.image_key)
