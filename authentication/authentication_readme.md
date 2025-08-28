# Authentication API Endpoints

This document provides details on the authentication-related API endpoints.

---

### 1. Register User

-   **URL:** `/auth/register/`
-   **Method:** `POST`
-   **Description:** Creates a new user account. An OTP is sent to the user's email for verification.
-   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "strongpassword",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890"
    }
    ```
-   **Response Body (201 CREATED):**
    ```json
    {
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
        "organizations": []
    }
    ```

---

### 2. Login User

-   **URL:** `/auth/login/`
-   **Method:** `POST`
-   **Description:** Authenticates a user and returns JWT access and refresh tokens.
-   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "strongpassword"
    }
    ```
-   **Response Body (200 OK):**
    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

---

### 3. Refresh Access Token

-   **URL:** `/auth/token/refresh/`
-   **Method:** `POST`
-   **Description:** Refreshes an expired JWT access token using a valid refresh token.
-   **Request Body:**
    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
-   **Response Body (200 OK):**
    ```json
    {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

---

### 4. Verify OTP

-   **URL:** `/auth/otp-verify/`
-   **Method:** `POST`
-   **Description:** Verifies an OTP for account activation or password reset.
-   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "otp_code": "123456",
        "purpose": "signup"
    }
    ```
    For password reset, include `new_password`:
    ```json
    {
        "email": "user@example.com",
        "otp_code": "123456",
        "purpose": "password_reset",
        "new_password": "newstrongpassword"
    }
    ```
-   **Response Body (200 OK):**
    ```json
    {
        "detail": "OTP verified successfully."
    }
    ```

---

### 5. Request OTP

-   **URL:** `/auth/request-otp/`
-   **Method:** `POST`
-   **Description:** Requests a new OTP to be sent to the user's email.
-   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "purpose": "password_reset"
    }
    ```
-   **Response Body (200 OK):**
    ```json
    {
        "detail": "OTP sent to your email."
    }
    ```

---

### 6. Change Password

-   **URL:** `/auth/change-password/`
-   **Method:** `POST`
-   **Description:** Allows an authenticated user to change their password.
-   **Authentication:** `Bearer <access_token>` required.
-   **Request Body:**
    ```json
    {
        "old_password": "currentstrongpassword",
        "new_password": "newstrongpassword"
    }
    ```
-   **Response Body (200 OK):**
    ```json
    {
        "detail": "password updated successfully"
    }
    ```

---

### 7. Get User Details

-   **URL:** `/auth/me/`
-   **Method:** `GET`
-   **Description:** Retrieves the details of the currently authenticated user.
-   **Authentication:** `Bearer <access_token>` required.
-   **Response Body (200 OK):**
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

---

### 8. Update User Details

-   **URL:** `/auth/me/update/`
-   **Method:** `PATCH`
-   **Description:** Allows an authenticated user to update their profile information.
-   **Authentication:** `Bearer <access_token>` required.
-   **Request Body:**
    ```json
    {
        "first_name": "Johnny",
        "last_name": "Doer",
        "phone_number": "+1987654321"
    }
    ```
-   **Response Body (200 OK):**
    ```json
    {
        "email": "user@example.com",
        "first_name": "Johnny",
        "last_name": "Doer",
        "phone_number": "+1987654321",
        "organizations": [
            {
                "uuid": "...",
                "name": "My Organization",
                "role": "owner"
            }
        ]
    }
    ```
