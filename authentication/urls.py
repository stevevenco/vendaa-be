from django.urls import path
from rest_framework_simplejwt.views import (
    # TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    CustomTokenObtainPairView,
    ForgotPasswordView,
    MemberDetailView,
    MemberListCreateView,
    OrganizationListCreateView,
    RequestOTPView,
    UserCreateView,
    UserDetailView,
    UserUpdateView,
    VerifyOTPView,
)

urlpatterns = [
    path("register/", UserCreateView.as_view(), name="register"),
    path(
        "login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path(
        "forgot-password/",
        ForgotPasswordView.as_view(),
        name="forgot_password",
    ),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("otp-verify/", VerifyOTPView.as_view(), name="otp_verification"),
    path("request-otp/", RequestOTPView.as_view(), name="request_otp"),
    # -----
    path("me/", UserDetailView.as_view(), name="user_detail"),
    path("me/update/", UserUpdateView.as_view(), name="user_update"),
    # -----
    path(
        "organizations/",
        OrganizationListCreateView.as_view(),
        name="organization_list_create",
    ),
    path(
        "organizations/<uuid:org_uuid>/members/",
        MemberListCreateView.as_view(),
        name="member_list_create",
    ),
    path(
        "organizations/<uuid:org_uuid>/members/<uuid:uuid>/",
        MemberDetailView.as_view(),
        name="member_detail",
    ),
]
