# Authentication API Documentation

This document provides a detailed explanation of the authentication and authorization system.

## Table of Contents

- [Authentication Endpoints](#authentication-endpoints)
- [Organization Endpoints](#organization-endpoints)
- [Invitation Endpoints](#invitation-endpoints)
- [Member Endpoints](#member-endpoints)

## Authentication Endpoints

### User Registration

- **URL:** `/api/v1/auth/register/`
- **Method:** `POST`
- **Description:** Registers a new user.
- **Request Body:**
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "email": "user@example.com",
    "password": "strongpassword123",
    "phone_number": "+1234567890"
  }
  ```
- **Response Body:**
  ```json
  {
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "organizations": []
  }
  ```

### User Login

- **URL:** `/api/v1/auth/login/`
- **Method:** `POST`
- **Description:** Authenticates a user and returns access and refresh tokens.
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "strongpassword123"
  }
  ```
- **Response Body:**
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

### Token Refresh

- **URL:** `/api/v1/auth/token/refresh/`
- **Method:** `POST`
- **Description:** Refreshes an access token.
- **Request Body:**
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Response Body:**
  ```json
  {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

### OTP Verification

- **URL:** `/api/v1/auth/otp-verify/`
- **Method:** `POST`
- **Description:** Verifies an OTP for a specific purpose (e.g., signup, password reset).
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "otp_code": "123456",
    "purpose": "signup"
  }
  ```
- **Response Body:**
  ```json
  {
    "detail": "OTP verified successfully."
  }
  ```

### Request OTP

- **URL:** `/api/v1/auth/request-otp/`
- **Method:** `POST`
- **Description:** Requests an OTP for a specific purpose.
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "purpose": "password_reset"
  }
  ```
- **Response Body:**
  ```json
  {
    "detail": "OTP sent to your email."
  }
  ```

### Change Password

- **URL:** `/api/v1/auth/change-password/`
- **Method:** `POST`
- **Description:** Changes the password of an authenticated user.
- **Request Body:**
  ```json
  {
    "old_password": "strongpassword123",
    "new_password": "newstrongpassword123"
  }
  ```
- **Response Body:**
  ```json
  {
    "detail": "password updated successfully"
  }
  ```

### Reset Forgot Password

- **URL:** `/api/v1/auth/reset-password/`
- **Method:** `POST`
- **Description:** Resets the password of a user who has forgotten their password.
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "otp_code": "123456",
    "new_password": "newstrongpassword123"
  }
  ```
- **Response Body:**
  ```json
  {
    "detail": "Password updated successfully!"
  }
  ```

### User Detail

- **URL:** `/api/v1/auth/me/`
- **Method:** `GET`
- **Description:** Retrieves the details of the authenticated user.
- **Response Body:**
  ```json
  {
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "organizations": [
      {
        "uuid": "...",
        "name": "My Organization",
        "role": "owner"
      }
    ],
    "is_active": false,
    "is_staff": false,
    "is_verified": false
  }
  ```

### User Update

- **URL:** `/api/v1/auth/me/update/`
- **Method:** `PATCH`
- **Description:** Updates the details of the authenticated user.
- **Request Body:**
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
  }
  ```
- **Response Body:**
  ```json
  {
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "organizations": [
      {
        "uuid": "...",
        "name": "My Organization",
        "role": "owner"
      }
    ]
  }
  ```

## Organization Endpoints

### List and Create Organizations

- **URL:** `/api/v1/auth/organizations/`
- **Method:** `GET`, `POST`
- **Description:** Lists all organizations the user is a member of, or creates a new organization.
- **Request Body (POST):**
  ```json
  {
    "name": "New Organization",
    "country": "country_uuid"
  }
  ```
- **Response Body (GET):**
  ```json
  [
    {
      "uuid": "...",
      "name": "My Organization",
      "created_by": "user_uuid",
      "created": "2023-10-27T10:00:00Z",
      "country": "country_uuid",
      "currency": "USD"
    }
  ]
  ```
- **Response Body (POST):**
  ```json
  {
    "uuid": "...",
    "name": "New Organization",
    "created_by": "user_uuid",
    "created": "2023-10-27T10:00:00Z",
    "country": "country_uuid",
    "currency": "USD"
  }
  ```

### Update Organization

- **URL:** `/api/v1/auth/organizations/{uuid}/`
- **Method:** `PUT`, `PATCH`
- **Description:** Updates an organization.
- **Request Body:**
  ```json
  {
    "name": "Updated Organization Name"
  }
  ```
- **Response Body:**
  ```json
  {
    "uuid": "...",
    "name": "Updated Organization Name",
    "created_by": "user_uuid",
    "created": "2023-10-27T10:00:00Z",
    "country": "country_uuid",
    "currency": "USD"
  }
  ```

## Invitation Endpoints

### List Invitations

- **URL:** `/api/v1/auth/organizations/{org_uuid}/invitations/`
- **Method:** `GET`
- **Description:** Lists all invitations for an organization.
- **Query Parameters:**
  - `type`: `sent` or `received` (defaults to `received`)
- **Response Body:**
  ```json
  [
    {
      "token": "...",
      "email": "invited@example.com",
      "role": "Member",
      "organization_name": "My Organization",
      "organization_uuid": "...",
      "sent_by_email": "admin@example.com",
      "sent_by_name": "Admin User",
      "status": "pending",
      "created": "2023-10-27T10:00:00Z",
      "expires_at": "2023-11-03T10:00:00Z"
    }
  ]
  ```

### Verify Invitation

- **URL:** `/api/v1/auth/invites/verify/`
- **Method:** `GET`
- **Description:** Verifies an invitation token.
- **Query Parameters:**
  - `token`: The invitation token.
- **Response Body:**
  ```json
  {
    "token": "...",
    "email": "invited@example.com",
    "role": "Member",
    "organization_name": "My Organization",
    "organization_uuid": "...",
    "sent_by_email": "admin@example.com",
    "sent_by_name": "Admin User",
    "status": "pending",
    "created": "2023-10-27T10:00:00Z",
    "expires_at": "2023-11-03T10:00:00Z"
  }
  ```

### Accept Invitation

- **URL:** `/api/v1/auth/invites/accept/`
- **Method:** `POST`
- **Description:** Accepts an invitation.
- **Request Body:**
  ```json
  {
    "token": "..."
  }
  ```
- **Response Body:**
  ```json
  {
    "detail": "Invitation accepted successfully."
  }
  ```

### Cancel Invitation

- **URL:** `/api/v1/auth/invites/{invitation_id}/cancel/`
- **Method:** `POST`
- **Description:** Cancels an invitation.
- **Response Body:**
  ```json
  {
    "detail": "Invitation cancelled successfully."
  }
  ```

### Decline Invitation

- **URL:** `/api/v1/auth/invites/{invitation_id}/decline/`
- **Method:** `POST`
- **Description:** Declines an invitation.
- **Response Body:**
  ```json
  {
    "detail": "Invitation declined successfully."
  }
  ```

## Member Endpoints

### List and Create Members

- **URL:** `/api/v1/auth/organizations/{org_uuid}/members/`
- **Method:** `GET`, `POST`
- **Description:** Lists all members of an organization, or invites a new member.
- **Request Body (POST):**
  ```json
  {
    "email": "newmember@example.com",
    "role": "member"
  }
  ```
- **Response Body (GET):**
  ```json
  [
    {
      "uuid": "...",
      "user": {
        "email": "member@example.com",
        "first_name": "Member",
        "last_name": "User",
        "phone_number": "+1234567890"
      },
      "role": "member",
      "joined_at": "2023-10-27T10:00:00Z",
      "invited_by": "user_uuid"
    }
  ]
  ```
- **Response Body (POST):**
  ```json
  {
    "email": "newmember@example.com",
    "role": "member"
  }
  ```

### Member Detail

- **URL:** `/api/v1/auth/organizations/{org_uuid}/members/{uuid}/`
- **Method:** `GET`, `PUT`, `PATCH`, `DELETE`
- **Description:** Retrieves, updates, or deletes a member of an organization.
- **Request Body (PUT/PATCH):**
  ```json
  {
    "role": "admin"
  }
  ```
- **Response Body (GET/PUT/PATCH):**
  ```json
  {
    "uuid": "...",
    "user": {
      "email": "member@example.com",
      "first_name": "Member",
      "last_name": "User",
      "phone_number": "+1234567890"
    },
    "role": "admin",
    "joined_at": "2023-10-27T10:00:00Z",
    "invited_by": "user_uuid"
  }
  ```
- **Response (DELETE):**
  - Status: `204 No Content`
