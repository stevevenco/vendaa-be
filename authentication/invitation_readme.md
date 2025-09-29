# Invitation API Endpoints

This document provides details on the invitation-related API endpoints.

---

### 1. List Invitations

-   **URL:** `/auth/invitations/`
-   **Method:** `GET`
-   **Description:** Lists invitations. By default, it shows invitations received by the authenticated user. Use the `type` query parameter to see sent invitations.
-   **Authentication:** `Bearer <access_token>` required.
-   **Query Parameters:**
    -   `type` (optional): `sent` or `received` (default).
        -   `received`: Shows invitations sent to the current user's email.
        -   `sent`: Shows invitations sent by organizations where the user is an admin or owner.
-   **Response Body (200 OK):**
    ```json
    [
        {
            "token": "invitation_uuid",
            "email": "user@example.com",
            "role": "Member",
            "organization_name": "Awesome Inc.",
            "organization_uuid": "org_uuid",
            "sent_by_email": "admin@awesome.inc",
            "sent_by_name": "Admin User",
            "status": "pending",
            "created": "2025-08-28T10:00:00Z",
            "expires_at": "2025-09-04T10:00:00Z"
        }
    ]
    ```

---

### 2. Verify Invitation

-   **URL:** `/auth/invites/verify/`
-   **Method:** `GET`
-   **Description:** Verifies an invitation token to check its validity and details before accepting.
-   **Query Parameters:**
    -   `token`: The UUID token from the invitation link.
-   **Response Body (200 OK):**
    ```json
    {
        "token": "invitation_uuid",
        "email": "user@example.com",
        "role": "Member",
        "organization_name": "Awesome Inc.",
        "organization_uuid": "org_uuid",
        "sent_by_email": "admin@awesome.inc",
        "sent_by_name": "Admin User",
        "status": "pending",
        "created": "2025-08-28T10:00:00Z",
        "expires_at": "2025-09-04T10:00:00Z"
    }
    ```

---

### 3. Accept Invitation

-   **URL:** `/auth/invites/accept/`
-   **Method:** `POST`
-   **Description:** Accepts a pending invitation, making the user a member of the organization.
-   **Authentication:** `Bearer <access_token>` required. The authenticated user's email must match the invitation email.
-   **Request Body:**
    ```json
    {
        "token": "invitation_uuid"
    }
    ```
-   **Response Body (200 OK):**
    ```json
    {
        "detail": "Invitation accepted successfully."
    }
    ```

---

### 4. Cancel Invitation

-   **URL:** `/auth/invites/<uuid:invitation_id>/cancel/`
-   **Method:** `POST`
-   **Description:** Cancels a pending invitation. This can only be done by an admin or owner of the organization that sent the invite.
-   **Authentication:** `Bearer <access_token>` required.
-   **URL Parameters:**
    -   `invitation_id`: The UUID of the invitation to cancel.
-   **Response Body (200 OK):**
    ```json
    {
        "detail": "Invitation cancelled successfully."
    }
    ```

---

### 5. Decline Invitation

-   **URL:** `/auth/invites/<uuid:invitation_id>/decline/`
-   **Method:** `POST`
-   **Description:** Declines a pending invitation. This can only be done by the user to whom the invitation was sent.
-   **Authentication:** `Bearer <access_token>` required.
-   **URL Parameters:**
    -   `invitation_id`: The UUID of the invitation to decline.
-   **Response Body (200 OK):**
    ```json
    {
        "detail": "Invitation declined successfully."
    }
    ```
