# Meter App API Documentation

This document provides documentation for the API endpoints in the Meter App.

## Authentication

All endpoints require authentication. The API uses JWT for authentication. You need to include an `Authorization` header with a valid JWT in your requests.

**Example Header**:
```
Authorization: Bearer <your_jwt_token>
```

---

## 1. List and Create Meters

### Create a Meter

Creates a new meter for a given organization.

- **Endpoint**: `POST /api/v1/organizations/{org_uuid}/meters/`
- **Method**: `POST`
- **URL Parameters**:
  - `org_uuid` (string, required): The UUID of the organization.
- **Request Body**:
  ```json
  {
      "customer_name": "John Doe",
      "meter_number": "1234567890",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "address": "123 Main St, Anytown, USA",
      "sgc": "SGC-123",
      "tariff_index": "T1",
      "key_revision_number": "001",
      "meter_type": "electricity"
  }
  ```
- **Success Response**:
  - **Code**: `201 CREATED`
  - **Content**:
    ```json
    {
        "uuid": "...",
        "customer_name": "John Doe",
        "meter_number": "1234567890",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "address": "123 Main St, Anytown, USA",
        "sgc": "SGC-123",
        "tariff_index": "T1",
        "key_revision_number": "001",
        "meter_type": "electricity",
        "added_by": "user_uuid",
        "organization": "org_uuid",
        "created": "...",
        "last_updated": "..."
    }
    ```
- **Error Responses**:
  - **Code**: `400 BAD REQUEST` (Validation Error from remote service)
    ```json
    {
        "detail": "Failed to add meter: Invalid Meter Number"
    }
    ```
  - **Code**: `400 BAD REQUEST` (Meter already exists in our DB)
    ```json
    {
        "meter_number": "A meter with number '1234567890' already exists in your organization."
    }
    ```
  - **Code**: `401 UNAUTHORIZED`
  - **Code**: `403 FORBIDDEN` (User not a member of the organization)

---

### List Meters

Lists all meters for a given organization.

- **Endpoint**: `GET /api/v1/organizations/{org_uuid}/meters/`
- **Method**: `GET`
- **URL Parameters**:
  - `org_uuid` (string, required): The UUID of the organization.
- **Success Response**:
  - **Code**: `200 OK`
  - **Content**:
    ```json
    [
        {
            "uuid": "...",
            "customer_name": "John Doe",
            "meter_number": "1234567890",
            ...
        }
    ]
    ```
- **Error Responses**:
  - **Code**: `401 UNAUTHORIZED`
  - **Code**: `403 FORBIDDEN`

---

## 2. Retrieve, Update, and Delete a Meter

### Retrieve a Meter

Retrieves the details of a specific meter.

- **Endpoint**: `GET /api/v1/organizations/{org_uuid}/meters/{meter_uuid}/`
- **Method**: `GET`
- **URL Parameters**:
  - `org_uuid` (string, required): The UUID of the organization.
  - `meter_uuid` (string, required): The UUID of the meter.
- **Success Response**:
  - **Code**: `200 OK`
  - **Content**: (Same as the create success response)
- **Error Responses**:
  - **Code**: `401 UNAUTHORIZED`
  - **Code**: `403 FORBIDDEN`
  - **Code**: `404 NOT FOUND`

---

### Update a Meter

Updates a meter's details.

- **Endpoint**: `PUT /api/v1/organizations/{org_uuid}/meters/{meter_uuid}/`
- **Method**: `PUT`
- **URL Parameters**:
  - `org_uuid` (string, required): The UUID of the organization.
  - `meter_uuid` (string, required): The UUID of the meter.
- **Request Body**: (Same as creation, all fields required)
- **Success Response**:
  - **Code**: `200 OK`
  - **Content**: (Same as the create success response)

---

### Partially Update a Meter

Partially updates a meter's details.

- **Endpoint**: `PATCH /api/v1/organizations/{org_uuid}/meters/{meter_uuid}/`
- **Method**: `PATCH`
- **URL Parameters**:
  - `org_uuid` (string, required): The UUID of the organization.
  - `meter_uuid` (string, required): The UUID of the meter.
- **Request Body**: (Same as creation, fields are optional)
- **Success Response**:
  - **Code**: `200 OK`
  - **Content**: (Same as the create success response)

---

### Delete a Meter

Deletes a meter.

- **Endpoint**: `DELETE /api/v1/organizations/{org_uuid}/meters/{meter_uuid}/`
- **Method**: `DELETE`
- **URL Parameters**:
  - `org_uuid` (string, required): The UUID of the organization.
  - `meter_uuid` (string, required): The UUID of the meter.
- **Success Response**:
  - **Code**: `204 NO CONTENT`
- **Error Responses**:
  - **Code**: `401 UNAUTHORIZED`
  - **Code**: `403 FORBIDDEN`
  - **Code**: `404 NOT FOUND`

---

## 3. Generate Meter Token

### Generate a Token

Generates a token for a given meter.

- **Endpoint**: `GET /api/v1/organizations/{org_uuid}/generate-token/`
- **Method**: `GET`
- **URL Parameters**:
  - `org_uuid` (string, required): The UUID of the organization.
- **Request Body**:
  - **For KCT Token**:
    ```json
    {
      "token_type": "kct",
      "meter_number": "0179000982118",
      "amount": 10
    }
    ```
  - **For Credit Token**:
    ```json
    {
      "token_type": "credit",
      "meter_number": "0179000982118",
      "amount": 10
    }
    ```
  - **For MSE Token (Clear Credit)**:
    ```json
    {
      "token_type": "clear_credit",
      "meter_number": "0179000982118",
      "amount": 10
    }
    ```
- **Success Response**:
  - **For KCT Token**:
    - **Code**: `200 OK`
    - **Content**:
      ```json
      [
          {
              "description": "Set1stSectionDecoderKey",
              "token": "68731966733222119353"
          },
          {
              "description": "Set2ndSectionDecoderKey",
              "token": "60359552671630017681"
          }
      ]
      ```
  - **For Credit/MSE Token**:
    - **Code**: `200 OK`
    - **Content**:
      ```json
      {
          "token": "14274511299228717001"
      }
      ```
- **Error Responses**:
  - **Code**: `400 BAD REQUEST` (Validation Error)
  - **Code**: `401 UNAUTHORIZED`
  - **Code**: `403 FORBIDDEN`
