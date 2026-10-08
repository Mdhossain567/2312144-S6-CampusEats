# Technical Design Document (TDD) - CampusEats

## 1. Architecture
- Frontend: React + TypeScript + Vite
- Backend: FastAPI (Python)
- Database: PostgreSQL (Production), SQLite (Local Dev)
- Deployment: Frontend on Vercel, Backend on Vercel/Render
- Authentication: JWT (Access + Refresh Tokens)

## 2. Project Structure

frontend/
  src/
    components/
    pages/
    services/
    App.tsx

backend/
  app/
    routers/
    services/
    repositories/
    models/
    schemas/
    main.py

## 3. Database Schema
- users: id, name, email, hashed_password, role (customer/staff/admin)
- menu_items: id, name, description, price, is_available
- orders: id, user_id, status (pending/preparing/ready/completed), created_at
- order_items: id, order_id, menu_item_id, quantity, price

## 4. API Endpoints
| Method | Endpoint | Role Required |
|--------|----------|---------------|
| POST | /api/auth/register | Public |
| POST | /api/auth/login | Public |
| GET | /api/menu | Public |
| POST | /api/orders | Customer |
| GET | /api/orders/my | Customer |
| GET | /api/orders | Kitchen Staff, Admin |
| PATCH | /api/orders/{id}/status | Kitchen Staff, Admin |
| POST | /api/menu | Admin |
| PATCH | /api/menu/{id} | Admin |
| DELETE | /api/menu/{id} | Admin |

## 5. Security
- JWT-based authentication
- Password hashing with bcrypt
- CORS configuration
- Role-Based Access Control (RBAC) via FastAPI dependencies
