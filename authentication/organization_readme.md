# Organization API Endpoints

This document provides details on the organization-related API endpoints.

---

### 1. List and Create Organizations

-   **URL:** `/auth/organizations/`
-   **Method:** `GET`, `POST`
-   **Description:**
    -   `GET`: Lists all organizations the authenticated user is a member of.
    -   `POST`: Creates a new organization. The user who creates it becomes the owner.
-   **Authentication:** `Bearer <access_token>` required.
-   **Request Body (POST):**
    ```json
    {
        "name": "New Awesome Company"
    }
    ```
-   **Response Body (GET - 200 OK):**
    ```json
    [
        {
            "uuid": "org_uuid_1",
            "name": "My First Company",
            "created_by": "user_uuid_1",
            "created": "2025-08-28T12:00:00Z"
        }
    ]
    ```
-   **Response Body (POST - 201 CREATED):**
    ```json
    {
        "uuid": "new_org_uuid",
        "name": "New Awesome Company",
        "created_by": "current_user_uuid",
        "created": "2025-08-28T13:00:00Z"
    }
    ```

---

### 2. Update Organization

-   **URL:** `/auth/organizations/<uuid>/`
-   **Method:** `PUT`, `PATCH`
-   **Description:** Updates the name of an organization.
-   **Authentication:** `Bearer <access_token>` required. User must be an owner or admin of the organization.
-   **URL Parameters:**
    -   `uuid`: The UUID of the organization to update.
-   **Request Body:**
    ```json
    {
        "name": "Updated Company Name"
    }
    ```
-   **Response Body (200 OK):**
    ```json
    {
        "name": "Updated Company Name"
    }
    ```

---

### 3. List and Invite Members

-   **URL:** `/auth/organizations/<uuid:org_uuid>/members/`
-   **Method:** `GET`, `POST`
-   **Description:**
    -   `GET`: Lists all members of a specific organization.
    -   `POST`: Invites a new member to the organization by sending an email.
-   **Authentication:** `Bearer <access_token>` required. User must be an owner or admin of the organization.
-   **URL Parameters:**
    -   `org_uuid`: The UUID of the organization.
-   **Request Body (POST):**
    ```json
    {
        "email": "new.member@example.com",
        "role": "member"
    }
    ```
-   **Response Body (GET - 200 OK):**
    ```json
    [
        {
            "uuid": "member_uuid_1",
            "user": {
                "email": "owner@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "phone_number": null
            },
            "role": "owner",
            "joined_at": "2025-08-28T12:00:00Z",
            "invited_by": "user_uuid_1"
        }
    ]
    ```
-   **Response Body (POST - 201 CREATED):**
    ```json
    {
        "email": "new.member@example.com",
        "role": "member"
    }
    ```

---

### 4. Member Details and Role Management

-   **URL:** `/auth/organizations/<uuid:org_uuid>/members/<uuid:uuid>/`
-   **Method:** `GET`, `PUT`, `PATCH`, `DELETE`
-   **Description:**
    -   `GET`: Retrieves details of a specific member.
    -   `PUT`/`PATCH`: Updates the role of a member.
    -   `DELETE`: Removes a member from the organization.
-   **Authentication:** `Bearer <access_token>` required. User must be an owner or admin of the organization.
-   **URL Parameters:**
    -   `org_uuid`: The UUID of the organization.
    -   `uuid`: The UUID of the member.
-   **Request Body (PUT/PATCH):**
    ```json
    {
        "role": "admin"
    }
    ```
-   **Response Body (GET - 200 OK):**
    ```json
    {
        "uuid": "member_uuid_1",
        "user": {
            "email": "member@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": null
        },
        "role": "member",
        "joined_at": "2025-08-28T14:00:00Z",
        "invited_by": "user_uuid_1"
    }
    ```
-   **Response Body (PUT/PATCH - 200 OK):**
    ```json
    {
        "role": "admin"
    }
    ```
-   **Response (DELETE - 204 NO CONTENT):** No response body.
-   **Important Notes:**
    -   The last owner or admin of an organization cannot have their role changed to "member" or be removed.
