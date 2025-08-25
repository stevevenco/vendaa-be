from django.urls import path
from rest_framework_simplejwt.views import (
    # TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    ChangePasswordView,
    CustomTokenObtainPairView,
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
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("otp-verify/", VerifyOTPView.as_view(), name="otp_verification"),
    path("request-otp/", RequestOTPView.as_view(), name="request_otp"),
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change_password",
    ),
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
