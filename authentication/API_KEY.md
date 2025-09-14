# API Key Management Documentation

This document provides a detailed explanation of the API key management system.

## Table of Contents

- [API Key Authentication](#api-key-authentication)
- [API Key Endpoints](#api-key-endpoints)

## API Key Authentication

### How to Authenticate

To authenticate with the API using an API key, you must include it in the `Authorization` header of your request, using the `Bearer` scheme.

```
Authorization: Bearer <your_api_key>
```

Replace `<your_api_key>` with your actual API key.

### Key Types and Scopes

There are two types of API keys:

- **Public Key (`pk_...`):** Intended for use in client-side applications (e.g., web browsers, mobile apps). It has limited, read-only permissions.
  - **Scopes:**
    - `meters:read`
    - `organizations:read`

- **Secret Key (`sk_...`):** Intended for use in server-side applications. It has full access to all resources.
  - **Scopes:**
    - `auth:read`
    - `organizations:full`
    - `invitations:full`
    - `wallet:full`
    - `meters:full`
    - `apikeys:full`
    - `token_purchase:create`

## API Key Endpoints

### List API Keys

- **URL:** `/api/v1/auth/organizations/{org_uuid}/api-keys/`
- **Method:** `GET`
- **Description:** Retrieves a list of all API keys for an organization.
- **Response Body:**
  ```json
  [
    {
      "uuid": "...",
      "key_id": "pk_...",
      "key_type": "public",
      "key_type_display": "Public Key",
      "name": "My Public Key",
      "is_active": true,
      "created_at": "2023-10-27T10:00:00Z",
      "last_used_at": "2023-10-27T10:00:00Z",
      "scopes": [
        "meters:read",
        "organizations:read"
      ]
    }
  ]
  ```

### Create API Key

- **URL:** `/api/v1/auth/organizations/{org_uuid}/api-keys/create/`
- **Method:** `POST`
- **Description:** Creates a new API key for an organization. The full key is only returned once upon creation.
- **Request Body:**
  ```json
  {
    "key_type": "public",
    "name": "My New Public Key"
  }
  ```
- **Response Body:**
  ```json
  {
    "uuid": "...",
    "key_id": "pk_...",
    "full_key": "pk_...some_secret_part",
    "key_type": "public",
    "key_type_display": "Public Key",
    "name": "My New Public Key",
    "is_active": true,
    "created_at": "2023-10-27T10:00:00Z",
    "scopes": [
      "meters:read",
      "organizations:read"
    ]
  }
  ```

### API Key Detail

- **URL:** `/api/v1/auth/organizations/{org_uuid}/api-keys/{key_uuid}/`
- **Method:** `GET`, `PUT`, `PATCH`, `DELETE`
- **Description:** Retrieves, updates, or deletes an API key.
- **Request Body (PUT/PATCH):**
  ```json
  {
    "name": "Updated Key Name",
    "is_active": false
  }
  ```
- **Response Body (GET/PUT/PATCH):**
  ```json
  {
    "uuid": "...",
    "key_id": "pk_...",
    "key_type": "public",
    "key_type_display": "Public Key",
    "name": "Updated Key Name",
    "is_active": false,
    "created_at": "2023-10-27T10:00:00Z",
    "last_used_at": "2023-10-27T10:00:00Z",
    "scopes": [
      "meters:read",
      "organizations:read"
    ]
  }
  ```
- **Response (DELETE):**
  - Status: `204 No Content`

### Regenerate API Key

- **URL:** `/api/v1/auth/organizations/{org_uuid}/api-keys/{key_uuid}/regenerate/`
- **Method:** `POST`
- **Description:** Regenerates an API key. This will invalidate the old key and generate a new one. The full key is only returned once upon regeneration.
- **Response Body:**
  ```json
  {
    "uuid": "...",
    "key_id": "pk_...",
    "full_key": "pk_...new_secret_part",
    "key_type": "public",
    "key_type_display": "Public Key",
    "name": "My Public Key",
    "is_active": true,
    "created_at": "2023-10-27T10:00:00Z",
    "scopes": [
      "meters:read",
      "organizations:read"
    ]
  }
  ```

### Get Auth Context

- **URL:** `/api/v1/auth/key-auth/me/`
- **Method:** `GET`
- **Description:** Retrieves the current authentication context. This is useful for validating an API key and getting information about the associated organization and scopes.
- **Response Body (API Key Auth):**
  ```json
  {
    "auth_type": "api_key",
    "key_uuid": "...",
    "key_type": "public",
    "organization": {
      "id": "...",
      "uuid": "...",
      "name": "My Organization"
    },
    "scopes": [
      "meters:read",
      "organizations:read"
    ],
    "last_used_at": "2023-10-27T10:00:00Z"
  }
  ```
- **Response Body (JWT Auth):**
    ```json
  {
    "auth_type": "jwt",
    "user": {
      "uuid": "...",
      "email": "user@example.com"
    }
  }
  ```
