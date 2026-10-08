# Product Requirements Document (PRD) - CampusEats

## 1. Overview
CampusEats is a web application for university students and staff to pre-order cafeteria food, reducing wait times and improving order management.

## 2. Goals
- Allow students to browse the menu and place orders online.
- Allow kitchen staff to view and manage incoming orders.
- Allow admins to manage menu items and user roles.

## 3. Target Users
- Students & Staff (Customers)
- Cafeteria Kitchen Staff
- Cafeteria Admin / Manager

## 4. Scope (MVP)
### Included:
- User authentication (Sign up / Login with JWT)
- Menu browsing and searching
- Order placement and status tracking
- Admin menu management (CRUD)
- Role-Based Access Control (RBAC)

### Excluded (Future / Beta):
- Payment gateway integration
- Push notifications
- Loyalty points system

## 5. User Stories
- As a student, I want to see the cafeteria menu so I can decide what to order.
- As a student, I want to place an order so I can skip the line.
- As a kitchen staff member, I want to see new orders so I can prepare them.
- As an admin, I want to add/remove menu items so the menu stays up to date.

## 6. Success Metrics
- Students can complete an order in under 2 minutes.
- Kitchen staff can update order status in real-time.
