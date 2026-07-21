# KayaRemit API Documentation

This document provides the REST API specification for **KayaRemit**. The API uses standard HTTP methods, RESTful endpoint design, and a consistent response format across all endpoints.

---

# General Response Standard

## Success Response

**HTTP Status:** `200 OK`, `201 Created`

```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {}
}
```

---

## Error Response

**HTTP Status:** `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`

```json
{
  "success": false,
  "reason": "INVALID_CREDENTIALS",
  "message": "The email or password provided is incorrect."
}
```

---

# 1. User Authentication & Profile Management

## Register User

**Endpoint**

```http
POST /api/v1/auth/register
```

Registers a new user account.

### Request Body

```json
{
  "full_name": "Donald Banda",
  "email": "donald@example.com",
  "phone": "+265991234567",
  "password": "SecurePassword123!"
}
```

### Success Response (201 Created)

```json
{
  "success": true,
  "message": "User registered successfully.",
  "data": {
    "user_id": "usr_987654321",
    "full_name": "Donald Banda",
    "email": "donald@example.com",
    "phone": "+265991234567"
  }
}
```

---

## Login

**Endpoint**

```http
POST /api/v1/auth/login
```

Authenticates a user and returns an access token.

### Request Body

```json
{
  "email": "donald@example.com",
  "password": "SecurePassword123!"
}
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsIn...",
    "user": {
      "user_id": "usr_987654321",
      "full_name": "Donald Banda",
      "email": "donald@example.com"
    }
  }
}
```

---

## Get User Profile

**Endpoint**

```http
GET /api/v1/user/profile
```

Retrieves the authenticated user's profile.

### Headers

```text
Authorization: Bearer <token>
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Profile retrieved successfully.",
  "data": {
    "user_id": "usr_987654321",
    "full_name": "Donald Banda",
    "email": "donald@example.com",
    "phone": "+265991234567",
    "kyc_status": "VERIFIED",
    "created_at": "2026-07-21T08:00:00Z"
  }
}
```

---

## Update User Profile

**Endpoint**

```http
PUT /api/v1/user/profile
```

Updates personal information.

### Headers

```text
Authorization: Bearer <token>
```

### Request Body

```json
{
  "full_name": "Donald Banda",
  "phone": "+265881234567"
}
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Profile updated successfully.",
  "data": {
    "user_id": "usr_987654321",
    "full_name": "Donald Banda",
    "phone": "+265881234567"
  }
}
```

---

# 2. Digital Wallet & Transaction Engine

## Get Wallet Details

**Endpoint**

```http
GET /api/v1/wallet
```

Returns wallet information, including balance.

### Headers

```text
Authorization: Bearer <token>
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Wallet details fetched successfully.",
  "data": {
    "wallet_id": "wal_11223344",
    "currency": "MWK",
    "balance": 150000.00,
    "status": "ACTIVE"
  }
}
```

---

## Transfer Funds

**Endpoint**

```http
POST /api/v1/wallet/transfer
```

Transfers money to another user or supported account.

### Headers

```text
Authorization: Bearer <token>
```

### Request Body

```json
{
  "recipient_identifier": "+265999000111",
  "amount": 25000.00,
  "currency": "MWK",
  "narration": "Project expenses"
}
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Transfer processed successfully.",
  "data": {
    "transaction_id": "tx_55667788",
    "amount": 25000.00,
    "fee": 0.00,
    "recipient": "Innocent Kapalamula",
    "status": "COMPLETED",
    "timestamp": "2026-07-21T08:30:00Z"
  }
}
```

### Error Response (400 Bad Request)

```json
{
  "success": false,
  "reason": "INSUFFICIENT_FUNDS",
  "message": "Your wallet balance is insufficient to complete this transaction."
}
```

---

## Get Transaction History

**Endpoint**

```http
GET /api/v1/wallet/transactions
```

Retrieves paginated transaction history.

### Headers

```text
Authorization: Bearer <token>
```

### Query Parameters

```text
?page=1&limit=10
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Transactions retrieved successfully.",
  "data": {
    "transactions": [
      {
        "transaction_id": "tx_55667788",
        "type": "DEBIT",
        "amount": 25000.00,
        "recipient_or_sender": "Innocent Kapalamula",
        "status": "COMPLETED",
        "created_at": "2026-07-21T08:30:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_records": 48
    }
  }
}
```

---

# 3. Budgeting & Financial Goal Setting

## Create Budget

**Endpoint**

```http
POST /api/v1/budgets
```

Creates a spending budget for a category.

### Headers

```text
Authorization: Bearer <token>
```

### Request Body

```json
{
  "category": "Groceries",
  "limit_amount": 50000.00,
  "period": "MONTHLY"
}
```

### Success Response (201 Created)

```json
{
  "success": true,
  "message": "Budget created successfully.",
  "data": {
    "budget_id": "bdg_001",
    "category": "Groceries",
    "limit_amount": 50000.00,
    "spent_amount": 0.00,
    "period": "MONTHLY"
  }
}
```

---

## List Budgets

**Endpoint**

```http
GET /api/v1/budgets
```

Returns all active budgets.

### Headers

```text
Authorization: Bearer <token>
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Budgets retrieved successfully.",
  "data": [
    {
      "budget_id": "bdg_001",
      "category": "Groceries",
      "limit_amount": 50000.00,
      "spent_amount": 12500.00,
      "remaining_amount": 37500.00,
      "period": "MONTHLY"
    }
  ]
}
```

---

## Create Savings Goal

**Endpoint**

```http
POST /api/v1/goals
```

Creates a financial savings goal.

### Headers

```text
Authorization: Bearer <token>
```

### Request Body

```json
{
  "title": "Emergency Fund",
  "target_amount": 200000.00,
  "target_date": "2026-12-31"
}
```

### Success Response (201 Created)

```json
{
  "success": true,
  "message": "Savings goal created successfully.",
  "data": {
    "goal_id": "gol_101",
    "title": "Emergency Fund",
    "target_amount": 200000.00,
    "current_amount": 0.00,
    "target_date": "2026-12-31"
  }
}
```

---

## Deposit to Savings Goal

**Endpoint**

```http
POST /api/v1/goals/{goal_id}/deposit
```

Deposits funds into an existing savings goal.

### Headers

```text
Authorization: Bearer <token>
```

### Request Body

```json
{
  "amount": 10000.00
}
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Deposit to savings goal successful.",
  "data": {
    "goal_id": "gol_101",
    "title": "Emergency Fund",
    "target_amount": 200000.00,
    "current_amount": 10000.00,
    "progress_percentage": 5.0
  }
}
```

---

# 4. Notifications

## Get Notifications

**Endpoint**

```http
GET /api/v1/notifications
```

Retrieves transaction and system notifications.

### Headers

```text
Authorization: Bearer <token>
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Notifications fetched successfully.",
  "data": [
    {
      "notification_id": "notif_9901",
      "title": "Money Sent",
      "message": "You sent MWK 25,000.00 to Innocent Kapalamula.",
      "is_read": false,
      "created_at": "2026-07-21T08:30:00Z"
    }
  ]
}
```

---

## Mark Notification as Read

**Endpoint**

```http
PATCH /api/v1/notifications/{notification_id}/read
```

Marks a notification as read.

### Headers

```text
Authorization: Bearer <token>
```

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Notification marked as read.",
  "data": {
    "notification_id": "notif_9901",
    "is_read": true
  }
}
```
