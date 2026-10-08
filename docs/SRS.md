# Software Requirements Specification (SRS) - CampusEats

## 1. Introduction
This document specifies the functional and non-functional requirements for the CampusEats system.

## 2. User Roles
- Customer (Student/Staff): Can browse menu, place orders, view own order history.
- Kitchen Staff: Can view incoming orders, update order status (Preparing / Ready / Completed).
- Admin: Can manage menu items, manage users, view all orders.

## 3. Functional Requirements
- FR-01: Users must be able to register with name, email, and password.
- FR-02: Users must be able to log in and receive a JWT token.
- FR-03: Customers can view a list of available menu items.
- FR-04: Customers can add items to a cart and place an order.
- FR-05: Kitchen staff can view a list of pending orders.
- FR-06: Kitchen staff can update the status of an order.
- FR-07: Admin can add, edit, or delete menu items.
- FR-08: Admin can view all orders in the system.

## 4. Non-Functional Requirements
- NFR-01 (Performance): API responses must be under 500ms.
- NFR-02 (Security): Passwords must be hashed with bcrypt.
- NFR-03 (Security): Role-Based Access Control must be enforced on all protected endpoints.
- NFR-04 (Usability): UI must be responsive on mobile and desktop.

## 5. RBAC Permission Matrix
| Action | Customer | Kitchen Staff | Admin |
|--------|----------|---------------|-------|
| Browse Menu | Yes | Yes | Yes |
| Place Order | Yes | No | No |
| Update Order Status | No | Yes | Yes |
| Manage Menu Items | No | No | Yes |
| View All Orders | No | Yes | Yes |
