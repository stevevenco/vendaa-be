from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from media.features.image.models import Image
from media.features.image.serializers import (
    ImageSerializer,
    ImageUploadSerializer,
)
from services.image_service import ImageService


class ImageUploadView(APIView):
    """
    View for handling image uploads via API.
    """

    parser_classes = [MultiPartParser]
    serializer_class = ImageUploadSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_service = ImageService()

    def post(self, request):
        """
        Handle batch image uploads.
        """
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uploaded_images = self.image_service.batch_upload_images(
                serializer.validated_data["images"],
                uploaded_by=request.user,
            )
            return Response(uploaded_images, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class GetDeleteImageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, image_id):
        try:
            image = ImageService.get_image(image_id)
            serializer = ImageSerializer(image)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Image.DoesNotExist:
            return Response(
                {"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, image_id):
        # Call the delete_image function with the provided image_id
        ImageService.delete_image(image_id, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
