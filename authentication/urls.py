from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AcceptInviteView,
    CancelInviteView,
    ChangePasswordView,
    CustomTokenObtainPairView,
    ResetForgotPasswordView,
    DeclineInviteView,
    ListInvitationsView,
    MemberDetailView,
    MemberListCreateView,
    OrganizationListCreateView,
    OrganizationUpdateView,
    RequestOTPView,
    UserCreateView,
    UserDetailView,
    UserUpdateView,
    VerifyInviteView,
    VerifyOTPView,
)

urlpatterns = [
    # ----- AUTHENTICATION ------ #
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
    path(
        "reset-password/",
        ResetForgotPasswordView.as_view(),
        name="reset_password",
    ),
    path("me/", UserDetailView.as_view(), name="user_detail"),
    path("me/update/", UserUpdateView.as_view(), name="user_update"),

    # ----- ORGANIZATION ------ #
    path(
        "organizations/",
        OrganizationListCreateView.as_view(),
        name="organization_list_create",
    ),
    path(
        "organizations/<uuid>/",
        OrganizationUpdateView.as_view(),
        name="organization_update",
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

    # ----- INVITATION ------ #
    path("invitations/", ListInvitationsView.as_view(), name="invitation_list"),
    path("invites/verify/", VerifyInviteView.as_view(), name="invite_verification"),
    path("invites/accept/", AcceptInviteView.as_view(), name="invite_acceptance"),
    path("invites/<uuid:invitation_id>/cancel/", CancelInviteView.as_view(), name="cancel_invite"),
    path("invites/<uuid:invitation_id>/decline/", DeclineInviteView.as_view(), name="decline_invite"),
]
