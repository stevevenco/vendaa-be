from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidOTP(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = (
        "This OTP is either: invalid, already used or already expired."
    )
    default_code = "wrong_otp"
