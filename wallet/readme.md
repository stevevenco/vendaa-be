# Wallet API Endpoints

This document provides details on the wallet-related API endpoints, which are used for creating wallets, checking balances, and initiating payments for funding.

---

### Automatic Wallet Creation

It's important to note that a wallet is automatically created for an organization as soon as it is registered, thanks to a `post_save` signal on the `Organization` model. The manual creation endpoint below is available but typically not needed for new organizations.

---

### 1. Create Wallet (Manual)

-   **URL:** `/wallet/create/`
-   **Method:** `POST`
-   **Description:** Manually triggers the creation of a wallet for a specified organization. This is useful if the automatic creation failed or for other specific scenarios.
-   **Authentication:** `Bearer <access_token>` required.
-   **Request Body:**
    ```json
    {
        "organization_id": "your_organization_uuid"
    }
    ```
-   **Response Body (201 CREATED):**
    ```json
    {
        "message": "Wallet created successfully",
        "data": {
            "wallet_id": "WLT-000123",
            "created_by": "owner@example.com",
            "reference": "organization_uuid",
            "currency": "NGN",
            "available_balance": "0.00"
        }
    }
    ```

---

### 2. Get Wallet Balance

-   **URL:** `/wallet/balance/<uuid:organization_id>/`
-   **Method:** `GET`
-   **Description:** Retrieves the current balance of an organization's wallet from the external meter services API. The local wallet balance is updated if the external balance is higher.
-   **Authentication:** `Bearer <access_token>` required.
-   **URL Parameters:**
    -   `organization_id`: The UUID of the organization whose wallet balance is being checked.
-   **Response Body (200 OK):**
    ```json
    {
        "balance": "₦1,500.00"
    }
    ```

---

### 3. Initiate Wallet Funding

-   **URL:** `/wallet/initiate-payment/<uuid:organization_id>`
-   **Method:** `GET`
-   **Description:** Initiates a payment process to fund an organization's wallet and returns available payment options.
-   **Authentication:** `Bearer <access_token>` required.
-   **URL Parameters:**
    -   `organization_id`: The UUID of the organization whose wallet is being funded.
-   **Query Parameters:**
    -   `payment_option`: `online_checkout` or `bank_transfer`.
    -   `amount`: A positive number representing the amount to fund.
-   **Example Request:** `/wallet/initiate-payment/your_org_uuid?payment_option=bank_transfer&amount=5000`
-   **Response Body (200 OK for `bank_transfer`):**
    ```json
    [
        {
            "payment_gateway": "Paystack",
            "slug": "paystack-bank-transfer",
            "logo": "https://example.com/logo.png",
            "amount": "5000.00",
            "fee": "50.00",
            "provider": "Paystack",
            "bank_name": "Example Bank",
            "icon": "https://example.com/icon.png",
            "account_number": "1234567890",
            "account_name": "Vendaa Inc - Org Name",
            "account_reference": "UNIQUE-REF-123"
        }
    ]
    ```
-   **Response Body (200 OK for `online_checkout`):**
    ```json
    [
        {
            "payment_gateway": "Paystack",
            "slug": "paystack-card",
            "logo": "https://example.com/logo.png",
            "amount": "5000.00",
            "fee": "75.00",
            "provider": "Paystack",
            "payment_url": "https://checkout.paystack.com/abcdefg"
        }
    ]
    ```
