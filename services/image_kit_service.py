import environ
from django.conf import settings
from imagekitio import ImageKit

# Load environment variables
env = environ.Env()

# Initialize ImageKit instance
imagekit = ImageKit(
    private_key=env("IMAGE_KIT_PRIVATE_KEY"),
    public_key=env("IMAGE_KIT_PUBLIC_KEY"),
    url_endpoint=env("IMAGE_KIT_URL_ENDPOINT"),
)


def generate_image_kit_url(aws_url: str, height: int = 300, width: int = 300):
    """
    Generates an ImageKit URL based on the S3 image URL
        and optional transformations.
    :param aws_url: The S3 URL of the image.
    :param height: The desired height for the transformed image.
    :param width: The desired width for the transformed image.
    :return: The transformed ImageKit URL.
    """
    # Extract relative path from AWS S3 URL
    base_s3_url = f"https://{settings.AWS_CONFIG.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
    print(f"aws_url: {aws_url}")
    file_path = aws_url.split(base_s3_url)
    print(f"file_path: {file_path}")
    if file_path[0] != "":
        raise ValueError(
            "Provided URL does not match the expected S3 bucket URL."
        )

    # image_path = aws_url[len(base_s3_url) :]

    image_url = imagekit.url(
        {
            "path": file_path[-1],
            # "transformation": [{"height": height, "width": width}]
        }
    )
    return image_url
