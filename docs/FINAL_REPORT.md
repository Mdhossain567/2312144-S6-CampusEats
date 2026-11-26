  
**Independent University, Bangladesh CSE309 Web Application & Internet**   
   
**Final Project Submission Report Submitted by:**   
Name: Md Hossain  
Student ID: 2312144   
Section: 6 

Project Title: CampusEats \- Campus Cafeteria   
Vercel URL: [https\://2312144-s6-campuseats.vercel.app](https://2312144-s6-campuseats.vercel.app)   
GitHub Repository: [https\://github.com/Mdhossain567/2312144-S6-CampusEats](https://github.com/Mdhossain567/2312144-S6-CampusEats)

**Submitted To:**
Sayef Reyadh   
Adjunct Lecturer   
Department of Computer Science & Engineering Independent University, Bangladesh  

Semester: Autumn 2026  
Date of Submission: November 28, 2026

## Contents

1. Executive Summary  
2. Part A. Product Requirements (PRD)  
3. Part B. Software Requirements (SRS)  
4. Part C. Technical Design (TDD)  
5. Part D. Evidence: Screenshots of the Running Application  
6. Part E. Project Management and Conclusion  
7. Appendix. Test Accounts and Video Demo

### List of figures and tables

| Number | Caption |
| :---- | :---- |
| Figure 1 | System architecture |
| Figure 2 | Use case diagram |
| Figure 3 | Backend folder tree |
| Figure 4 | Frontend folder tree |
| Figure 5 | ER diagram |
| Figure 6 | JWT sequence: login, request, expiry, refresh and logout |
| Figure 7 | Authorisation flow of one request |
| Figure 8 | Admin pages and the endpoints they call |
| Figure 9 | Deployment layout |
| Table 1 to Table 28 | Referenced in the text; see the headings of each section |
| S1 to S21 | Screenshots in Part D |

Page numbers are added in the PDF version.

---

## 1\. Executive Summary

### 1.1 Project overview

CampusEats is a cafeteria ordering system for the students and staff of a university. Customers browse the menu, order alone or through a shared meal group, and follow the status of their orders. Kitchen staff prepare the orders. Administrators manage the menu, the users, the groups and the whole system from an admin dashboard. The system is a secure multi-user application with token-based login, role-based access control and an audit log.

Stack: React with TypeScript (Vite), FastAPI (Python), SQLModel with Alembic migrations, Supabase PostgreSQL (SQLite locally), deployed on Vercel.

### 1.2 What was built since the mid assessment

The mid assessment delivered the menu feature (v0.1.0). Then the orders, the cart and the kitchen board were added (v0.1.5). For the final submission (v0.2.0) the following were added, named as they appear in the application:

- **JWT authentication with refresh and logout:** login gives a 15-minute access token and sets a rotating 7-day httpOnly refresh cookie backed by a server-side session; logout ends the session on the server; the profile page lists and revokes sessions, updates the profile and changes the password.  
- **Role-based access control:** the roles customer, kitchen staff and admin, one central RBAC module, ownership rules, and **meal groups** where members have different permissions (create, edit, assign) and only the owner manages the group.  
- **Admin dashboard:** statistics, user search and filters with a detail view, ban and unban with a reason (single and bulk), role change, session revoke, content moderation, activity log, security view and CSV exports.  
- **Audit logging, brute-force protection and deployment:** an audit\_log table, a lockout after repeated failed logins, Alembic migrations, a seed script, automated tests, and a live deployment on Vercel with Supabase.

### 1.3 Live links

**Table 1\. Links**

| Item | Link |
| :---- | :---- |
| GitHub repository | [https\://github.com/Mdhossain567/2312144-S6-CampusEats](https://github.com/Mdhossain567/2312144-S6-CampusEats) |
| Vercel frontend | [https\://2312144-s6-campuseats.vercel.app](https://2312144-s6-campuseats.vercel.app) |
| API (base path) | [https\://2312144-s6-campuseats.vercel.app/api/v1](https://2312144-s6-campuseats.vercel.app/api/v1) |
| API docs | [https\://2312144-s6-campuseats.vercel.app/api/docs](https://2312144-s6-campuseats.vercel.app/api/docs) |
| Video demo | [https://youtu.be/8FrBgyThmDI?si=hmv6NvBJer7sXWnF](https://youtu.be/8FrBgyThmDI?si=hmv6NvBJer7sXWnF) |

The test accounts (user IDs and passwords) are in the Appendix of the PDF report only.

---

## Part A. Product Requirements (PRD)

### A1. Problem Statement

At lunch time on a campus, hundreds of students and staff want food within a short break between classes. They queue at the cafeteria counter, orders are taken verbally or on paper, and the kitchen has no clear view of what to prepare next. People lose class time, orders are forgotten or mixed up, and the cafeteria cannot see what sells.

Today people cope by arriving early, sending a friend to queue, or skipping the meal. Groups of colleagues also collect and write down their orders by hand. This matters because the waiting time is wasted, the kitchen works without a clear list, and money and trust are lost when orders go wrong.

### A2. Users and Roles

**Table 2\. Users and roles**

| Role | Who they are | Main tasks | Must never be able to |
| :---- | :---- | :---- | :---- |
| Visitor | A person who is not logged in | Read the menu, sign up, log in | Place an order, see any order, use any page that needs an account |
| Customer | A student or staff member with an account | Browse the menu, use the cart, place and follow own orders, cancel own pending orders, manage own profile and sessions, create meal groups | See or change another customer's orders, change the menu, change anyone's role |
| Kitchen staff | A cafeteria worker | See all orders, move orders through their steps | Change the menu, manage users, place orders |
| Group member / owner | A customer inside a meal group | Member: use the group according to the permissions the owner gave (create, edit, assign). Owner: also rename and delete the group and manage members and permissions | A member cannot manage the group or members; nobody can use a group action without the permission |
| Admin | A cafeteria manager or system administrator | Manage the menu, users (ban, unban, role, sessions), content, read the audit log and security view, export CSV files | Change their own role, ban another admin or themselves |

### A3. Goals and Success Measures

**Table 3\. Goals and measures**

| ID | Goal | Measure |
| :---- | :---- | :---- |
| G-01 | Customers order without queueing | A customer completes an order from the menu in under 2 minutes on the live site (timed once) |
| G-02 | The kitchen always knows what to prepare | A status change by the kitchen is visible on the customer's "My orders" page within 15 seconds (yes or no check) |
| G-03 (security) | No user can read another user's data | In the ownership tests, a request for another customer's order never returns the record (404 or 403\) |
| G-04 (security) | Sessions are short-lived and revocable | The access token lives at most 15 minutes; after logout or revoke, the refresh cookie is rejected with 401 |
| G-05 (security) | A banned user is stopped at once | The banned user's next request returns 403, and the interface logs them out within about 10 seconds |
| G-06 | Admins can govern the system | An admin can find a user, ban them with a reason, and see the matching entry in the audit log (yes or no check) |

### A4. Scope and Non-Goals

**In scope**

- Authentication: sign up, login, short-lived access token, rotating refresh cookie, logout, sessions, profile, password change, lockout  
- Role-based access control with three roles, ownership rules and meal groups with member permissions  
- Admin dashboard: statistics, users, ban and unban, role change, moderation, activity log, security view, exports  
- Domain features: menu with pagination, search and filters; cart; orders; kitchen board  
- Audit log, migrations, seed data, automated tests and deployment on Vercel with Supabase

**Out of scope (and why)**

- Online payment: it needs a payment provider and is not part of the course goals  
- Email verification and password reset by email: they need an email service  
- Push notifications and real-time sockets: Vercel functions are short-lived; the pages refresh at fixed intervals instead  
- Delivery tracking, loyalty points and discounts: not needed for the learning goals

**Assumptions and constraints**

- Current versions of Chrome, Edge or Firefox are used  
- Vercel runs the backend as short-lived functions, so no background jobs or long connections  
- The free Supabase project can pause after a period without use  
- The work was done by one student within the course timetable

### A5. User Stories

**Table 4\. User stories**

| ID | Story |
| :---- | :---- |
| US-01 | As a visitor I want to sign up with my email and a password so that I can place orders. |
| US-02 | As a user I want to log in and stay logged in safely, without typing my password again every few minutes, so that I can work without interruption. |
| US-03 | As a user I want to see the devices where I am logged in and end any of them so that I can stop someone who got access to my account. |
| US-04 | As a user I want to change my password after entering the current one so that my account stays safe. |
| US-05 | As a customer I want to see only my own orders so that my data stays private. |
| US-06 | As a group owner I want to give each member different permissions so that members can only do what I allow. |
| US-07 | As a group member with the assign permission I want to assign an item to a member so that everybody knows who picks it up. |
| US-08 | As a group member without the edit permission I want the system to refuse my edits so that the owner's rules are respected. |
| US-09 | As kitchen staff I want to move an order through its steps so that customers know when it is ready. |
| US-10 | As an admin I want to see overview statistics so that I understand how the system is used. |
| US-11 | As an admin I want to ban a user with a reason, and have them logged out at once, so that abuse stops immediately. |
| US-12 | As an admin I want to read the audit log with filters so that I can find who did what and when. |
| US-13 | As an admin I want to export users, records and activity as CSV files so that I can report outside the system. |
| US-14 | As a customer I want to put items in a cart and place an order so that I can skip the queue. |
| US-15 | As an admin I want to add, edit and delete menu items so that the menu is always correct. |

---

## Part B. Software Requirements (SRS)

### B1. Introduction

**Purpose.** This part states exactly what CampusEats shall do. Every requirement has a unique ID and can be tested. **Readers.** The course instructor, and any developer who wants to check or extend the system.

**Table 5\. Definitions**

| Term | Meaning |
| :---- | :---- |
| JWT | JSON Web Token: a signed token that carries claims such as the user id and the role |
| Access token | A short-lived JWT sent with every protected request |
| Refresh token | A longer-lived secret, kept in an httpOnly cookie and stored hashed on the server, used to get a new access token |
| RBAC | Role-Based Access Control: what a user may do depends on the role |
| Role | A named group of permissions: customer, kitchen staff or admin |
| Permission | A single allowed action, such as can\_create, can\_edit or can\_assign inside a group |
| Audit log | A record of important events with who, what, when, IP address and browser |

**References.** RFC 7519 (JSON Web Token); RFC 9106 (Argon2); OWASP Application Security Verification Standard (ASVS); OWASP Cheat Sheet Series (authentication, session management, CSRF); FastAPI, SQLModel, Alembic, Vercel and Supabase documentation.

### B2. Functional Requirements

**Table 6\. FR-AUTH: authentication and sessions**

| ID | Requirement | Story |
| :---- | :---- | :---- |
| FR-AUTH-01 | The system shall let a visitor sign up with a name, a unique email and a password of at least 8 characters with a letter and a digit, and shall always create the account with the role customer. | US-01 |
| FR-AUTH-02 | The system shall log a user in with the email and password, and shall answer a wrong email and a wrong password with the same message. | US-02 |
| FR-AUTH-03 | The system shall store passwords only as Argon2id hashes mixed with a secret pepper read from an environment variable. | US-01 |
| FR-AUTH-04 | The system shall issue a signed JWT access token that contains the user id and the role and lives at most 15 minutes. | US-02 |
| FR-AUTH-05 | The system shall verify the access token on every protected request and shall answer a missing, invalid, tampered or expired token with 401\. | US-02 |
| FR-AUTH-06 | The system shall issue a refresh token in an httpOnly cookie, store only its hash in the user\_session table, and replace it with a new one every time it is used (rotation). | US-02 |
| FR-AUTH-07 | The system shall end the session on the server when the user logs out, so that its refresh token no longer works. | US-03 |
| FR-AUTH-08 | The system shall list the active sessions of the logged-in user with the browser, the IP address and the times. | US-03 |
| FR-AUTH-09 | The system shall let a user revoke any of their own sessions, and nobody else's. | US-03 |
| FR-AUTH-10 | The system shall block login for a period after 5 failed attempts and shall answer with 429 while the account is locked. | US-02 |
| FR-AUTH-11 | The system shall let a user update their profile name. | US-04 |
| FR-AUTH-12 | The system shall change a password only when the current password is correct and the new password passes the validation rules, and shall count a wrong current password as a failed attempt. | US-04 |
| FR-AUTH-13 | The frontend shall refresh the access token once when the server answers 401, log the user out if the refresh fails, and show no guest content while the session is being restored. | US-02 |

**Table 7\. FR-RBAC: roles, ownership and groups**

| ID | Requirement | Story |
| :---- | :---- | :---- |
| FR-RBAC-01 | The system shall store each user's role (customer, kitchen staff or admin) in the database and read it on every protected request. | US-05 |
| FR-RBAC-02 | The system shall check roles and permissions on the server for every protected endpoint through one reusable RBAC module. | US-05 |
| FR-RBAC-03 | The system shall let a customer read, change or cancel only their own orders and shall answer a request for another user's order with 404 or 403\. | US-05 |
| FR-RBAC-04 | The system shall let only the owner of a meal group rename it, delete it, and manage its members and their permissions. | US-06 |
| FR-RBAC-05 | The system shall let a group member add items only with the create permission, change items only with the edit permission, and assign items only with the assign permission, and shall answer 403 otherwise. | US-07, US-08 |
| FR-RBAC-06 | The system shall not let an admin change their own role. | US-11 |
| FR-RBAC-07 | The system shall not let an admin ban another admin or themselves. | US-11 |
| FR-RBAC-08 | The system shall reject a banned user on the very next request with 403 and shall end all of their sessions. | US-11 |
| FR-RBAC-09 | The frontend shall guard routes and show menus according to the role, matching the server rules. | US-05 |

**Table 8\. FR-ADM: admin dashboard**

| ID | Requirement | Story |
| :---- | :---- | :---- |
| FR-ADM-01 | The system shall show statistics: total users, banned users, orders, groups and new users in the last 7 days. | US-10 |
| FR-ADM-02 | The system shall list users with search by name or email, filters by role and status, and pagination. | US-10 |
| FR-ADM-03 | The system shall show a user's detail with their orders, groups, sessions and recent activity. | US-10 |
| FR-ADM-04 | The system shall ban and unban a user and shall require a reason when banning. | US-11 |
| FR-ADM-05 | The system shall let an admin change another user's role. | US-11 |
| FR-ADM-06 | The system shall let an admin revoke all sessions of a user. | US-11 |
| FR-ADM-07 | The system shall ban and unban several users in one action and shall report how many were changed and how many were skipped. | US-11 |
| FR-ADM-08 | The system shall list all orders and groups with filters and shall let an admin delete one or many. | US-10 |
| FR-ADM-09 | The system shall record login, failed login, logout, password change, role change, ban, unban, delete and export events with the user, IP address, browser and time, and shall let an admin search and filter them. | US-12 |
| FR-ADM-10 | The system shall show failed logins grouped by IP address and by account. | US-12 |
| FR-ADM-11 | The system shall export users, records and activity as CSV files that respect the current filters. | US-13 |

**Table 9\. FR-DOMAIN: menu, cart, orders and kitchen**

| ID | Requirement | Story |
| :---- | :---- | :---- |
| FR-DOMAIN-01 | The system shall let everyone read the menu with pagination, a search by name and a category filter. | US-14 |
| FR-DOMAIN-02 | The system shall let only an admin create, change and delete menu items, and shall refuse to delete an item that is part of an order. | US-15 |
| FR-DOMAIN-03 | The system shall let a customer place an order with 1 to 50 different items and a quantity from 1 to 20 each, calculate the total on the server from the menu prices, and refuse unknown or unavailable items. | US-14 |
| FR-DOMAIN-04 | The system shall keep the name and price of each item inside the order, so that later menu changes do not change old orders. | US-14 |
| FR-DOMAIN-05 | The system shall show a customer their own orders with their status. | US-05 |
| FR-DOMAIN-06 | The system shall let kitchen staff and admins list all orders by status and move an order only through pending, preparing, ready and completed. | US-09 |
| FR-DOMAIN-07 | The system shall let a customer cancel their order, and an admin cancel any order, only while it is pending. | US-14 |
| FR-DOMAIN-08 | The system shall let members of a meal group put items in a shared list and let the owner place the list as an order. | US-06 |

### B3. Non-Functional Requirements

**Table 10. Non-functional requirements**

| ID | Category | Requirement and measure |
| :--- | :--- | :--- |
| NFR-SEC-01 | Security | Secrets (database URL, JWT secret, pepper) shall only be in environment variables. A search of the repository finds none, and `.env.example` lists names only. |
| NFR-SEC-02 | Security | Login errors shall be generic: the same message for a wrong email and a wrong password. |
| NFR-SEC-03 | Security | Password hashes, refresh tokens and secrets shall never be returned in a response or written to a log. |
| NFR-SEC-04 | Security | CORS shall allow only the frontend origin given in `FRONTEND_ORIGIN`. |
| NFR-SEC-05 | Security | An unexpected error shall return 500 with a short message and never a stack trace. |
| NFR-PERF-01 | Performance | Every list endpoint shall be paginated with offset of at least 0 and limit from 1 to 100. |
| NFR-PERF-02 | Performance | A normal request shall answer in under 500 ms on the deployed API (confirmed in Chrome DevTools Network tab on Vercel: `/api/v1/auth/me` answered in 204 ms, `/api/v1/menu` in 225 ms, and `/api/v1/groups/1` in 427 ms). |
| NFR-USE-01 | Usability | The interface shall be responsive and show loading, error and empty states, with no console errors on the main pages. |
| NFR-REL-01 | Reliability | Data shall persist in a hosted PostgreSQL database after a restart or a new deployment. |
| NFR-REL-02 | Reliability | `alembic upgrade head` shall build the whole schema on an empty database. |
| NFR-MAINT-01 | Maintainability | Permission checks shall live in one RBAC module (`backend/app/auth/rbac.py`). |
| NFR-MAINT-02 | Maintainability | Automated `pytest` tests shall cover login, token rejection and at least three RBAC rules. |

### B4. Roles and Permission Matrix

### B4. Roles and Permission Matrix

**Table 11\. Endpoint groups by role** (yes, no, own, or the condition)

| Endpoint group | Visitor | Customer | Kitchen staff | Group member | Group owner | Admin |
| :---- | :---: | :---: | :---: | :---: | :---: | :---: |
| Read the menu | yes | yes | yes | yes | yes | yes |
| Create, change, delete menu items | no | no | no | no | no | yes |
| Sign up and log in | yes | \- | \- | \- | \- | \- |
| Own profile, password, sessions | no | own | own | own | own | own |
| Place an order | no | yes | no | yes | yes | no |
| See orders | no | own | all | own | own | all |
| Change an order's status | no | no | yes | no | no | yes |
| Cancel an order | no | own, pending | no | own, pending | own, pending | any, pending |
| Create a meal group | no | yes | no | \- | \- | no |
| Create a group order, add items | no | no | no | if create | yes | no |
| Change quantity or notes of an item | no | no | no | if edit | yes | no |
| Assign an item to a member | no | no | no | if assign | yes | no |
| Rename or delete a group, manage members and permissions | no | no | no | no | yes | delete through content moderation only |
| Admin dashboard (statistics, users, moderation, activity log, security view, exports) | no | no | no | no | no | yes |

**Table 12\. Group permissions**

| Action | Owner | create | edit | assign |
| :---- | :---: | :---: | :---: | :---: |
| Create a group order | yes | yes | no | no |
| Add an item to a group order | yes | yes | no | no |
| Change the quantity or the notes of an item | yes | no | yes | no |
| Assign an item to a member | yes | no | no | yes |
| Rename the group | yes | no | no | no |
| Delete the group | yes | no | no | no |
| Add or remove members | yes | no | no | no |
| Change members' permissions | yes | no | no | no |

The three permissions are stored as the switches can\_create, can\_edit and can\_assign of each group\_member row. Their meaning follows the model: can\_create adds items and orders to the shared pool, can\_edit updates items and quantities, and can\_assign assigns items to members.

**Table 13\. Admin rules**

| Rule | Behaviour |
| :---- | :---- |
| Change own role | Refused with 403 |
| Ban another admin or themselves | Refused with 403; bulk bans skip admins and report them as skipped |
| Banned users | Rejected on the next request with 403, sessions ended, cannot log in |
| Extra rights inside a group | None; an admin can only delete a group through content moderation |

### B5. Use Cases

**Figure 2\. Use case diagram**

```mermaid
flowchart LR
    V([Visitor]) --> UC1(Sign up)
    V --> UC2(Log in)
    C([Customer]) --> UC3(Refresh session and log out)
    C --> UC4(Place an order)
    C --> UC5(Manage sessions and password)
    C --> UC6(Create a meal group)
    O([Group owner]) --> UC7(Change a member's permissions)
    M([Group member]) --> UC8(Add, edit or assign items)
    K([Kitchen staff]) --> UC9(Move an order forward)
    A([Admin]) --> UC10(Ban or unban a user)
    A --> UC11(Read the audit log)
    A --> UC12(Moderate content)
    A --> UC13(Export CSV)
```

**Table 14. Use case descriptions**

| ID | Use case | Actor | Preconditions | Main flow | Alternative and error flows | Postconditions |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| UC-01 | Log in and refresh | Customer | Account exists and is not banned | 1. Enter email and password. 2. The server checks the lock and the password. 3. It returns a 15-minute access token and sets the refresh cookie. 4. When the token expires, the app asks `/auth/refresh` once and gets a new token. | Wrong email or password: 401, same message. Account locked: 429. Banned: 403. Refresh fails: the user is logged out. | A session exists in `user_session`; a `LOGIN` event is logged |
| UC-02 | Place an order | Customer | Logged in; items are available | 1. Add items to the cart. 2. Press Place order. 3. The server checks each item and calculates the total. 4. The order is saved as pending. | Not logged in: 401. Wrong role: 403. Unknown or unavailable item, or bad quantity: 422. | An order with its lines exists, with the name and price copied |
| UC-03 | Change a member's permissions | Group owner | The group exists; the user is its owner | 1. Open the group. 2. Change a member's create, edit and assign switches. 3. Save. | Not the owner: 403. Not a member or unknown group: 404. | The member's permissions are updated in `group_member` and recorded in `audit_log` |
| UC-04 | A denied action | Group member without edit | Member of the group | 1. Try to change an item's quantity. 2. The server checks the permission. | 403 "no permission"; the item is unchanged. | Nothing changes; the denial is visible in the app and the network tab |
| UC-05 | Ban a user | Admin | Logged in as admin; the target is not an admin | 1. Open the user. 2. Press Ban and enter a reason. 3. The server marks the user banned and ends their sessions. | Target is an admin or the admin themselves: 403. Empty reason: 422. Unknown user: 404. | The user is rejected on the next request; a `BAN` event is logged |
| UC-06 | Read the audit log | Admin | Logged in as admin | 1. Open the activity log. 2. Filter by event, user or date and search. | Not an admin: 403. | The matching events are listed with user, IP address, browser and time |

### B6. Acceptance Criteria

**Table 15\. Acceptance criteria**

| ID | Requirement | Given / When / Then |
| :---- | :---- | :---- |
| AC-01 | FR-AUTH-05 | Given an access token that has expired, when it is sent to a protected endpoint, then the answer is 401\. |
| AC-02 | FR-AUTH-05 | Given a token whose payload or signature was changed, when it is sent, then the answer is 401\. |
| AC-03 | FR-AUTH-05 | Given no token, when a protected endpoint is called, then the answer is 401\. |
| AC-04 | FR-AUTH-02 | Given a wrong password and an unknown email, when each logs in, then both get the same 401 message. |
| AC-05 | FR-AUTH-10 | Given 5 failed logins on an account, when the correct password is then used, then the answer is 429 until the lock ends. |
| AC-06 | FR-AUTH-06 | Given a refresh cookie that was already used, when it is sent again, then the answer is 401\. |
| AC-07 | FR-AUTH-07 | Given a logged-out session, when its refresh cookie is sent, then the answer is 401\. |
| AC-08 | FR-RBAC-03 | Given two customers, when customer A requests customer B's order, then the answer is 404 or 403\. |
| AC-09 | FR-RBAC-05 | Given a member without the edit permission, when they change an item in the group, then the answer is 403\. |
| AC-10 | FR-RBAC-08 | Given a banned user with a valid token, when they send any request, then the answer is 403\. |
| AC-11 | FR-RBAC-07 | Given two admins, when one bans the other, then the answer is 403\. |
| AC-12 | FR-DOMAIN-02 | Given a customer token, when a menu item is created, changed or deleted, then the answer is 403; without a token it is 401\. |
| AC-13 | FR-DOMAIN-04 | Given an order, when an admin later changes an item's price, then the order still shows the old price. |
| AC-14 | FR-ADM-11 | Given a filter on the users list, when the CSV is exported, then only the filtered users are in the file. |

### B7. Traceability Matrix

Endpoint paths are listed in Table 20\. `test_auth.py` and `test_rbac.py` are in `backend/tests/`. "Manual" means checked by hand on the live site.

**Table 16. Requirement, endpoint or screen, test, screenshot**

| Requirement | Endpoint or screen | Test | Screenshot |
| :--- | :--- | :--- | :--- |
| FR-AUTH-01 | `POST /api/v1/auth/register`, sign-up page | manual | S1 |
| FR-AUTH-02 | `POST /api/v1/auth/login`, login page | `test_auth.py` | S1 |
| FR-AUTH-03 | `backend/app/security.py` | `test_auth.py::test_register_and_login` | S1 |
| FR-AUTH-04 | login response, token in the network tab | `test_auth.py::test_register_and_login` | S7 |
| FR-AUTH-05 | every protected endpoint | `test_auth.py::test_token_rejection_missing`, `_tampered`, `_expired` | S7 |
| FR-AUTH-06 | `POST /api/v1/auth/refresh` | `test_auth.py::test_refresh_token_rotation` | S8 |
| FR-AUTH-07 | `POST /api/v1/auth/logout` | `test_auth.py::test_refresh_token_rotation` | S8 |
| FR-AUTH-08 | `GET /api/v1/auth/sessions`, profile page | manual | S4 |
| FR-AUTH-09 | `DELETE /api/v1/auth/sessions/{id}`, profile page | manual | S4 |
| FR-AUTH-10 | `POST /api/v1/auth/login` | `test_auth.py` | S16 |
| FR-AUTH-11 | `PATCH /api/v1/auth/profile`, profile page | manual | S3 |
| FR-AUTH-12 | `POST /api/v1/auth/change-password`, profile page | manual | S3 |
| FR-AUTH-13 | `frontend/src/services/api.ts`, auth context | manual | S7, S8 |
| FR-RBAC-01 | `app_user.role`, `get_current_user` | `test_rbac.py` | S6 |
| FR-RBAC-02 | `backend/app/auth/rbac.py` | `test_rbac.py` | S6 |
| FR-RBAC-03 | orders endpoints | `test_rbac.py` | S2, S6 |
| FR-RBAC-04 | groups endpoints, group page | manual | S5 |
| FR-RBAC-05 | groups endpoints | `test_rbac.py` | S5, S6 |
| FR-RBAC-06 | admin role change | manual | S12 |
| FR-RBAC-07 | admin ban | `test_rbac.py` | S13 |
| FR-RBAC-08 | `get_current_user` | `test_rbac.py` | S9 |
| FR-RBAC-09 | route guards, menus | manual | S6 |
| FR-ADM-01 | admin overview | manual | S10 |
| FR-ADM-02 | admin users page | manual | S11 |
| FR-ADM-03 | admin user detail | manual | S12 |
| FR-ADM-04 | admin ban dialog | manual | S13 |
| FR-ADM-05 | admin role change | manual | S12 |
| FR-ADM-06 | admin revoke sessions | manual | S12 |
| FR-ADM-07 | admin bulk actions | manual | S14 |
| FR-ADM-08 | admin moderation page | manual | S14 |
| FR-ADM-09 | admin activity log | manual | S15 |
| FR-ADM-10 | admin security view | manual | S16 |
| FR-ADM-11 | CSV export buttons | manual | S17 |
| FR-DOMAIN-01 | `GET /api/v1/menu`, menu page | manual | S2 |
| FR-DOMAIN-02 | `POST`, `PATCH`, `DELETE /api/v1/menu` | `test_rbac.py::test_rbac_menu_role_boundaries` | S6 |
| FR-DOMAIN-03 | `POST /api/v1/orders`, cart | manual | S2 |
| FR-DOMAIN-04 | order lines | manual | S2 |
| FR-DOMAIN-05 | `GET /api/v1/orders/my`, My orders page | manual | S2 |
| FR-DOMAIN-06 | `GET /api/v1/orders`, `PATCH /api/v1/orders/{id}/status`, kitchen board | manual | S2 |
| FR-DOMAIN-07 | `POST /api/v1/orders/{id}/cancel` | manual | S2 |
| FR-DOMAIN-08 | groups endpoints, group page | manual | S5 |

## Part C. Technical Design (TDD)

### C1. Technology Stack

**Table 17\. Technology stack and installed versions**

| Layer | Technology | Version | Purpose |
| :---- | :---- | :---- | :---- |
| Frontend UI | React (react / react-dom) | 19.3.0 | Component-based single-page user interface |
| Frontend Language | TypeScript | 7.0.2 | Static typing across API clients, contexts, and pages |
| Frontend Routing | React Router (react-router-dom) | 7.18.5 | Client-side routing and role-protected route guards |
| Frontend Build Tool | Vite (@vitejs/plugin-react 6.1.1) | 8.3.2 | Local development server and production bundle builder |
| Backend Framework | FastAPI (Python 3.14.0) | 0.162.0 | REST API with automatic OpenAPI documentation |
| ORM & Validation | SQLModel / SQLAlchemy / Pydantic | 0.0.48 / 2.1.6 / 2.14.2 | Typed database models, queries, and request/response schemas |
| Database Migrations | Alembic | 1.20.1 | Versioned schema migrations for PostgreSQL and SQLite |
| Password Hashing | Argon2-cffi (argon2-cffi) | 25.1.0 | Argon2id password hashing combined with HMAC-SHA256 server pepper |
| Token Signing | PyJWT | 2.15.1 | HS256 JWT access token encoding and signature/expiry verification |
| Database Drivers | SQLite (dev) / PostgreSQL (psycopg) | 3.3.7 | Local SQLite development database and Supabase PostgreSQL production database |
| Automated Testing | Pytest / HTTPX | 9.2.0 / 0.28.1 | Integration test suite for authentication, sessions, RBAC, and safety rules |

### C2. System Architecture

**Figure 1\. System architecture**

```mermaid
flowchart LR
    B[Browser: React app] -->|1. load pages| F[Vercel frontend service]
    B -->|2. /api requests with Authorization header| A[Vercel API service: FastAPI]
    B -->|3. refresh and logout with the httpOnly cookie| A
    A -->|4. queries through the repositories| D[(Supabase PostgreSQL)]
    A -->|5. writes events| L[(audit_log table)]
    D --- L
```

| Arrow | Explanation |
| :---- | :---- |
| 1 | The browser loads the static React pages from the frontend service. A rewrite sends every path to index.html so deep links and reloads work. |
| 2 | The React app sends JSON requests to /api/v1/... on the same domain. Protected requests carry the access token in the Authorization: Bearer header. |
| 3 | The refresh token travels only in an httpOnly cookie sent to the authentication paths. JavaScript cannot read it, and the server rotates it on every refresh. |
| 4 | The API reads and writes data through repositories, with SQL built by the ORM. The connection uses Supabase's transaction pooler. |
| 5 | Important events are written to the audit\_log table in the same database. Admins read them through the activity log and security view. |

### C3. Backend and Frontend Structure

**Figure 3\. Backend folder tree**

```
backend/
  main.py                    FastAPI app, routers, error handler
  alembic/                   migrations (versions/)
  scripts/                   seed.py, set_role.py
  tests/                     test_auth.py, test_rbac.py
  app/
    config.py                settings from environment variables
    security.py              Argon2 hashing with pepper, JWT helpers
    database.py              engine and session
    clock.py                 UTC helpers
    menu_items/              model, schemas, repository, service, router
    users/                   accounts
    auth/                    login, sessions, current user, rbac.py
    orders/                  orders and the kitchen workflow
    groups/                  meal groups and member permissions
    admin/                   admin dashboard endpoints
    audit/                   audit log
```

**Figure 4\. Frontend folder tree**

```
frontend/
  vercel.json                rewrites every path to index.html
  src/
    components/              reusable parts, route guards, forms, cart
    context/                 authentication state, cart
    pages/                   menu, login, profile, orders, kitchen, groups, admin
    services/api.ts          the only place that calls the backend
    types/                   TypeScript types
    App.tsx                  routes
```

**Where things live.** *Backend:* routes are in each feature's router.py; business rules in service.py; database queries in repository.py; tables in models.py; request and response shapes in schemas.py. The authentication code is in app/auth/ and app/security.py; the RBAC module is app/auth/rbac.py; the admin code is in app/admin/. *Frontend:* pages are in src/pages, components and route guards in src/components, the API client in src/services/api.ts, and the authentication state in src/context.

### C4. Data Model

**Figure 5\. ER diagram**

```mermaid
erDiagram
    APP_USER ||--o{ USER_SESSION : has
    APP_USER ||--o{ CUSTOMER_ORDER : places
    CUSTOMER_ORDER ||--|{ ORDER_ITEM : contains
    MENU_ITEM ||--o{ ORDER_ITEM : "is ordered as"
    APP_USER ||--o{ MEAL_GROUP : owns
    MEAL_GROUP ||--o{ GROUP_MEMBER : has
    APP_USER ||--o{ GROUP_MEMBER : "is member"
    MEAL_GROUP ||--o{ GROUP_ORDER : has
    APP_USER ||--o{ GROUP_ORDER : creates
    GROUP_ORDER ||--o{ GROUP_ORDER_ITEM : contains
    MENU_ITEM ||--o{ GROUP_ORDER_ITEM : "is added as"

    APP_USER {
        int id PK
        string name
        string email UK
        string password_hash
        string role
        bool is_active
        int failed_logins
        datetime locked_until
        datetime last_login_at
        datetime created_at
        bool is_banned
        datetime banned_at
        string ban_reason
    }
    USER_SESSION {
        int id PK
        int user_id FK
        string refresh_token_hash
        string user_agent
        string ip_address
        datetime created_at
        datetime expires_at
        bool revoked
    }
    MENU_ITEM {
        int id PK
        string name UK
        string description
        float price
        string category
        bool is_available
        datetime created_at
        datetime updated_at
    }
    CUSTOMER_ORDER {
        int id PK
        int user_id FK
        string status
        float total
        datetime created_at
        datetime updated_at
    }
    ORDER_ITEM {
        int id PK
        int order_id FK
        int menu_item_id FK
        string name
        float unit_price
        int quantity
    }
    MEAL_GROUP {
        int id PK
        string name
        string description
        int owner_id FK
        datetime created_at
        datetime updated_at
    }
    GROUP_MEMBER {
        int id PK
        int group_id FK
        int user_id FK
        string role
        bool can_create
        bool can_edit
        bool can_assign
        datetime joined_at
    }
    GROUP_ORDER {
        int id PK
        int group_id FK
        int creator_id FK
        string title
        string notes
        string status
        float total
        datetime created_at
        datetime updated_at
    }
    GROUP_ORDER_ITEM {
        int id PK
        int group_order_id FK
        int menu_item_id FK
        string name
        float unit_price
        int quantity
        int added_by_id FK
        int assigned_to_id FK
        string notes
    }
    AUDIT_LOG {
        int id PK
        int user_id
        string user_email
        string action
        string resource_type
        string resource_id
        string ip_address
        string user_agent
        string details
        datetime created_at
    }
```

**How the special data is stored**

- **Roles and bans:** the role column of app\_user holds customer, kitchen\_staff or admin. A ban is stored in is\_banned, together with banned\_at and ban\_reason, and a banned user is rejected on every request. The table also keeps an is\_active flag (default true).  
- **Sessions and refresh tokens:** each login creates a row in user\_session. The refresh token itself is never stored: only its SHA-256 hash is, in refresh\_token\_hash, together with the browser (user\_agent), the IP address, created\_at, expires\_at and the boolean revoked flag (default false).  
- **Group membership with permissions:** group\_member links a user to a meal\_group with a group role (owner or member, default member) and three switches, can\_create (default true), can\_edit (default false) and can\_assign (default false). The owner is also stored in meal\_group.owner\_id. A group order (group\_order) holds its items in group\_order\_item, each with the user who added it (added\_by\_id) and the member it is assigned to (assigned\_to\_id).  
- **Activity log:** every important event is a row in audit\_log with the action, the user id and email, the resource type and id, the IP address, the browser (user\_agent), the details and the time. user\_id is a plain number without a foreign key.

**Table 18\. app\_user**

| Column | Type | Key / constraint | Index |
| :---- | :---- | :---- | :---- |
| id | integer | primary key | yes |
| name | text (max 80\) | required | no |
| email | text (max 254\) | unique, required | yes |
| password\_hash | text (max 255\) | required; Argon2id hash with its own salt | no |
| role | text (max 20\) | customer, kitchen\_staff or admin; default customer | yes |
| is\_active | boolean | default true | no |
| failed\_logins | integer | default 0 (lockout counter) | no |
| locked\_until | datetime | optional (lockout time) | no |
| last\_login\_at | datetime | optional | no |
| created\_at | datetime | default now (UTC) | no |
| is\_banned | boolean | default false | no |
| banned\_at | datetime | optional | no |
| ban\_reason | text (max 500\) | optional | no |

The indexed columns of app\_user are id, email (unique) and role. The ban columns have no index.

**Table 19\. Other tables**

| Table | Columns | Keys and constraints | Indexes |
| :---- | :---- | :---- | :---- |
| user\_session | id, user\_id, refresh\_token\_hash (max 64), user\_agent (max 512, optional), ip\_address (max 45, optional), created\_at, expires\_at, revoked (default false) | primary key id; foreign key user\_id to app\_user | user\_id, refresh\_token\_hash |
| menu\_item | id, name (max 100), description (max 500, optional), price, category (max 20), is\_available (default true), created\_at, updated\_at | primary key id; name unique | name, category |
| customer\_order | id, user\_id, status (max 20, default pending), total, created\_at, updated\_at | foreign key user\_id to app\_user | user\_id, status |
| order\_item | id, order\_id, menu\_item\_id, name (max 100), unit\_price, quantity | foreign keys to customer\_order and menu\_item; name and price copied at order time | order\_id, menu\_item\_id |
| meal\_group | id, name (max 100), description (max 255, optional), owner\_id, created\_at, updated\_at | foreign key owner\_id to app\_user | name, owner\_id |
| group\_member | id, group\_id, user\_id, role (max 20, default member), can\_create (default true), can\_edit (default false), can\_assign (default false), joined\_at | foreign keys to meal\_group and app\_user | group\_id, user\_id |
| group\_order | id, group\_id, creator\_id, title (max 100), notes (max 255, optional), status (open, placed or cancelled; default open), total (default 0), created\_at, updated\_at | foreign keys to meal\_group and app\_user | group\_id, creator\_id |
| group\_order\_item | id, group\_order\_id, menu\_item\_id, name (max 100), unit\_price, quantity (default 1), added\_by\_id, assigned\_to\_id (optional), notes (max 100, optional) | foreign keys to group\_order, menu\_item and app\_user (added\_by\_id and assigned\_to\_id both point to app\_user) | group\_order\_id, menu\_item\_id, added\_by\_id, assigned\_to\_id |
| audit\_log | id, user\_id (optional), user\_email (max 254, optional), action (max 50), resource\_type (max 50, optional), resource\_id (max 100, optional), ip\_address (max 45, optional), user\_agent (max 512, optional), details (max 1000, optional), created\_at | primary key id; no foreign keys | user\_id, action, ip\_address, created\_at |

---

### C5. API Design

All paths start with `/api/v1`, except `/api/health`. Requests and responses are JSON, except the CSV exports (`text/csv`). Errors have the form `{"detail": "message"}`; validation errors (`422`) return a list of problems. Paginated lists return `{items, total, offset, limit}`. Every endpoint except the public ones returns `401` without a valid token and `403` for a banned account.

**Table 20\. Endpoint list**

| Method and path | Authentication | Role or permission | Request | Success | Errors |
| :---- | :---- | :---- | :---- | :---- | :---- |
| `GET /menu` | no | public | query: `offset`, `limit`, `category`, `available`, `q` | 200 (`MenuItemPage`) | 422 |
| `GET /menu/{menu_item_id}` | no | public | \- | 200 (`MenuItemRead`) | 404 |
| `POST /menu` | yes | `admin` | `name`, `description`, `price`, `category`, `is_available` | 201 (`MenuItemRead`) | 401, 403, 409, 422 |
| `PATCH /menu/{menu_item_id}` | yes | `admin` | any of `name`, `description`, `price`, `category`, `is_available` | 200 (`MenuItemRead`) | 401, 403, 404, 409, 422 |
| `DELETE /menu/{menu_item_id}` | yes | `admin` | \- | 204 | 401, 403, 404, 409 |
| `POST /auth/register` | no | public | `name`, `email`, `password` | 201 (`UserRead`) | 409, 422 |
| `POST /auth/login` | no | public | `email`, `password` | 200 (`TokenResponse` + `campuseats_refresh` cookie) | 401, 403, 422, 429 |
| `POST /auth/refresh` | refresh cookie | any logged-in user | \- | 200 (`TokenResponse` + rotated cookie) | 401, 403 |
| `POST /auth/logout` | refresh cookie | any logged-in user | \- | 204 (clears cookie) | \- |
| `GET /auth/me` | yes | any role | \- | 200 (`UserRead`) | 401, 403 |
| `PATCH /auth/profile` | yes | own | `name` | 200 (`UserRead`) | 401, 403, 422 |
| `POST /auth/change-password` | yes | own | `current_password`, `new_password` | 204 | 400, 401, 403, 422, 429 |
| `GET /auth/sessions` | yes | own | \- | 200 (`list[SessionRead]`) | 401, 403 |
| `DELETE /auth/sessions/{session_id}` | yes | own | \- | 204 | 401, 403, 404 |
| `POST /orders` | yes | `customer` | `items`: list of `{menu_item_id, quantity}` | 201 (`OrderRead`) | 401, 403, 422 |
| `GET /orders` | yes | `kitchen_staff`, `admin` | query: `offset`, `limit`, `status` | 200 (`OrderPage`) | 401, 403, 422 |
| `GET /orders/my` | yes | `customer` | query: `offset`, `limit` | 200 (`OrderPage`) | 401, 403, 422 |
| `GET /orders/{order_id}` | yes | owner, `kitchen_staff`, `admin` | \- | 200 (`OrderRead`) | 401, 404 |
| `PATCH /orders/{order_id}/status` | yes | `kitchen_staff`, `admin` | `status` | 200 (`OrderRead`) | 401, 403, 404, 409, 422 |
| `POST /orders/{order_id}/cancel` | yes | `customer` (own), `admin` | \- | 200 (`OrderRead`) | 401, 403, 404, 409 |
| `GET /groups` | yes | any authenticated user (lists own groups, or all if `admin`) | \- | 200 (`list[GroupRead]`) | 401, 403 |
| `POST /groups` | yes | authenticated user (creator becomes owner) | `name`, `description` | 201 (`GroupRead`) | 401, 403, 422 |
| `GET /groups/{group_id}` | yes | group member | \- | 200 (`GroupDetailRead`) | 401, 403, 404 |
| `PATCH /groups/{group_id}` | yes | group owner | `name`, `description` | 200 (`GroupRead`) | 401, 403, 404, 422 |
| `DELETE /groups/{group_id}` | yes | group owner | \- | 204 | 401, 403, 404 |
| `POST /groups/{group_id}/members` | yes | group owner | `user_id` or `email`, `can_create`, `can_edit`, `can_assign` | 201 (`GroupMemberRead`) | 401, 403, 404, 409, 422 |
| `PATCH /groups/{group_id}/members/{target_user_id}` | yes | group owner | `can_create`, `can_edit`, `can_assign` | 200 (`GroupMemberRead`) | 401, 403, 404, 422 |
| `DELETE /groups/{group_id}/members/{target_user_id}` | yes | group owner or target member | \- | 204 | 401, 403, 404 |
| `POST /groups/{group_id}/orders` | yes | group owner or member with `can_create` | `title`, `notes` | 201 (`GroupOrderRead`) | 401, 403, 404, 422 |
| `POST /groups/{group_id}/orders/{order_id}/items` | yes | group owner or member with `can_create` | `menu_item_id`, `quantity`, `notes` | 201 (`GroupOrderItemRead`) | 401, 403, 404, 422 |
| `PATCH /groups/{group_id}/orders/{order_id}/items/{item_id}` | yes | member with `can_edit` or item adder (`quantity`, `notes`); `can_assign` (`assigned_to_id`) | `quantity`, `notes`, `assigned_to_id` | 200 (`GroupOrderItemRead`) | 401, 403, 404, 422 |
| `DELETE /groups/{group_id}/orders/{order_id}/items/{item_id}` | yes | group owner, member with `can_edit`, or item adder | \- | 204 | 401, 403, 404 |
| `GET /admin/stats` | yes | `admin` | \- | 200 (`AdminStats`) | 401, 403 |
| `GET /admin/users` | yes | `admin` | query: `offset`, `limit`, `q`, `role`, `status` | 200 (`AdminUserPage`) | 401, 403, 422 |
| `GET /admin/users/{user_id}` | yes | `admin` | \- | 200 (`AdminUserDetail`) | 401, 403, 404 |
| `POST /admin/users/{user_id}/ban` | yes | `admin` (never an `admin` target) | `reason` | 204 | 400, 401, 403, 404, 422 |
| `POST /admin/users/{user_id}/unban` | yes | `admin` | \- | 204 | 401, 403, 404 |
| `POST /admin/users/{user_id}/role` | yes | `admin` (never own role) | `role` | 204 | 400, 401, 403, 404, 422 |
| `POST /admin/users/{user_id}/revoke-sessions` | yes | `admin` | \- | 204 | 401, 403, 404 |
| `POST /admin/users/bulk-ban` | yes | `admin` | `user_ids`, `reason` | 200 (`BulkActionResponse`: `affected`, `skipped`) | 401, 403, 422 |
| `POST /admin/users/bulk-unban` | yes | `admin` | `user_ids` | 200 (`BulkActionResponse`: `affected`, `skipped`) | 401, 403, 422 |
| `GET /admin/content` | yes | `admin` | query: `type` (`orders`, `menu`, `groups`), `q`, `offset`, `limit` | 200 (`items`, `total`) | 401, 403, 422 |
| `DELETE /admin/content/{content_type}/{content_id}` | yes | `admin` | \- | 204 | 401, 403, 404, 409 |
| `POST /admin/content/bulk-delete` | yes | `admin` | `type`, `ids` | 200 (`BulkDeleteResponse`: `deleted`, `skipped`) | 401, 403, 422 |
| `GET /admin/audit-logs` | yes | `admin` | query: `offset`, `limit`, `action`, `user_id`, `q` | 200 (`items`, `total`, `offset`, `limit`) | 401, 403, 422 |
| `GET /admin/security` | yes | `admin` | \- | 200 (failed logins by IP and account) | 401, 403 |
| `GET /admin/export/users` | yes | `admin` | \- | 200 (`text/csv`, `campuseats_users.csv`) | 401, 403 |
| `GET /admin/export/orders` | yes | `admin` | \- | 200 (`text/csv`, `campuseats_orders.csv`) | 401, 403 |
| `GET /admin/export/audit-logs` | yes | `admin` | \- | 200 (`text/csv`, `campuseats_audit_logs.csv`) | 401, 403 |
| `GET /api/health` | no | public | \- | 200 (`{"status": "ok"}`) | \- |

### C6. JWT Authentication Design

**Figure 6\. JWT sequence**

```mermaid
sequenceDiagram
    participant B as Browser (React)
    participant A as API (FastAPI)
    participant D as Database
    B->>A: POST /auth/login (email, password)
    A->>D: find the user, check lock and ban
    A->>A: verify the Argon2id hash (with the pepper)
    A->>D: create the user_session (hashed refresh token)
    A-->>B: access token (15 min) and the httpOnly refresh cookie
    B->>A: request with Authorization: Bearer access token
    A->>D: check signature and expiry, load the user, role and ban state
    A-->>B: 200, or 401 / 403
    Note over B,A: after 15 minutes the access token has expired
    B->>A: request with the expired token
    A-->>B: 401
    B->>A: POST /auth/refresh (cookie)
    A->>D: check the session, rotate the refresh token
    A-->>B: new access token and new cookie
    B->>A: POST /auth/logout
    A->>D: revoke the session
    A-->>B: cookie cleared
    B->>A: POST /auth/refresh with the old cookie
    A-->>B: 401 (session revoked or token already used)
```

**Table 21\. Access token claims**

| Claim | Meaning |
| :---- | :---- |
| sub | The authenticated user's integer ID (str(user\_id)) |
| role | The user's role at the time of login (customer, kitchen\_staff, or admin; informational only—the server always reads the live role from the database) |
| iat | Issued-at UTC timestamp |
| exp | Expiry timestamp, ACCESS\_TOKEN\_MINUTES (15 minutes) after issue |

- **Algorithm and secret:** HS256, signed with JWT\_SECRET from environment variables. Passwords are never hashed raw; security.py computes an HMAC-SHA256 digest using PASSWORD\_PEPPER (\_pepper(password)) before passing it to Argon2id (PasswordHasher()), and verifies DUMMY\_HASH on unknown emails to prevent user-enumeration timing attacks.  
- **Lifetimes:** Access tokens expire in ACCESS\_TOKEN\_MINUTES (15 minutes) so a stolen token has a narrow window of exposure. Refresh tokens expire in REFRESH\_TOKEN\_DAYS (7 days) and rotate on every POST /api/v1/auth/refresh call (sess\_repo.rotate), immediately invalidating the previous refresh token hash.  
- **Where the tokens are stored in the browser:** The refresh token (campuseats\_refresh) is stored exclusively in an httpOnly cookie that JavaScript cannot read, configured with SameSite="lax", path="/api/v1/auth", and Secure=True in production (VERCEL). The access token is kept **in JavaScript memory only** (let accessToken: string \| null \= null inside frontend/src/services/api.ts, never in localStorage or sessionStorage). Storing the access token solely in memory eliminates persistent token theft via XSS while keeping its lifetime capped at 15 minutes; restricting the httpOnly refresh cookie with SameSite="lax" and path="/api/v1/auth" mitigates CSRF exposure while allowing tryRestoreSession() to silently restore login state across page reloads.  
- **What the server checks on every request (auth/dependencies.py):** The server checks for the Authorization: Bearer \<token\> header, verifies the HS256 signature and exp timestamp via decode\_access\_token(), queries the database for the user (repository.get(session, user\_id)), and confirms user.is\_active \== True and user.is\_banned \== False (returning 403 Account is banned immediately if banned, even before the 15-minute access token expires). Session revocation (db\_session.revoked and expires\_at) is enforced on POST /api/v1/auth/refresh, preventing any revoked session from obtaining a new access token.  
- **What the frontend does on a 401 (api.ts & AuthContext.tsx):** When a request returns 401, api.ts deduplicates concurrent refreshes using a shared refreshPromise, sends POST /api/v1/auth/refresh with credentials: 'include', stores the rotated access\_token in memory, and retries the original request once with the new Bearer token. If the refresh fails, it clears accessToken, triggers onUnauthorized (sessionExpired \= true), and shows the login page. While tryRestoreSession() runs on initial page load, AuthContext holds loading \= true so no guest UI flashes before the session resolves.

### C7. RBAC Design

**Figure 7\. Authorisation flow**

```mermaid
flowchart TD
    R[Request] --> T{Valid token?}
    T -- no --> E1[401]
    T -- yes --> U{User exists and not banned?}
    U -- no user --> E1
    U -- banned --> E2[403 Account banned]
    U -- ok --> P{Role or permission allowed?}
    P -- no --> E3[403]
    P -- yes --> O{Own record?}
    O -- no, and not staff or admin --> E4[404 or 403]
    O -- yes --> G{Group permission, for a group action}
    G -- missing --> E3
    G -- ok --> H[Handler runs]
```

A request is authorised in this order: the token, the user, the role or permission check, the ownership check, the group permission check, and then the handler.

- **Roles and permission constants (`backend/app/auth/rbac.py`):**
  - **Role constants (`UserRole`):** `CUSTOMER = "customer"`, `KITCHEN_STAFF = "kitchen_staff"`, `ADMIN = "admin"`.
  - **Permission constants (`Permission`):**
    - **Menu:** `MENU_READ = "menu:read"`, `MENU_MANAGE = "menu:manage"`
    - **Orders:** `ORDER_CREATE = "order:create"`, `ORDER_READ_OWN = "order:read_own"`, `ORDER_MANAGE_STATUS = "order:manage_status"`, `ORDER_CANCEL_OWN = "order:cancel_own"`
    - **Groups:** `GROUP_CREATE = "group:create"`, `GROUP_READ = "group:read"`, `GROUP_MANAGE = "group:manage"`
    - **Admin:** `ADMIN_DASHBOARD = "admin:dashboard"`, `USER_MANAGE = "user:manage"`, `CONTENT_MODERATE = "content:moderate"`, `AUDIT_VIEW = "audit:view"`, `DATA_EXPORT = "data:export"`
  - **Role-to-permissions mapping (`ROLE_PERMISSIONS`):**
    - `customer`: `menu:read`, `order:create`, `order:read_own`, `order:cancel_own`, `group:create`, `group:read`
    - `kitchen_staff`: `menu:read`, `order:manage_status`, `group:read`
    - `admin`: all `Permission` values
- **The reusable dependency (`backend/app/auth/rbac.py`):**

```python
def require_permission(permission: str | Permission):
    """Reusable FastAPI dependency to enforce a specific permission on an endpoint."""
    perm_val = permission.value if isinstance(permission, Permission) else permission

    def dependency(user: CurrentUser) -> AppUser:
        if not has_permission(user, perm_val):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return dependency
```

- **Ownership in queries:** a customer's order list is filtered by the owner id in the database query (`WHERE user_id = ...`), and a single order of another customer is answered with `404`, so the record is never loaded for the wrong user and its existence is not revealed.
- **Adding a new role or permission:** add the constant to `UserRole` or `Permission` in `rbac.py`, add it to `ROLE_PERMISSIONS`, apply `Depends(require_permission(...))` on the endpoints, and add automated tests for both allowed and denied cases.
- **Administrative safety invariants (`check_admin_safety`):** prevents an administrator from banning another administrator (`400 Bad Request`) and prevents an administrator from changing their own role (`400 Bad Request`). A banned user is rejected on the next request (`403 Forbidden`) because `is_banned` is read from the database on every request, and banning also revokes all of the user's active sessions.

### C8. Admin Dashboard Design

**Figure 8\. Admin pages and the endpoints they call**

```mermaid
flowchart LR
    O[Overview] --> E1[/api/v1/admin/stats]
    U[Users and user detail] --> E2[/api/v1/admin/users]
    M[Moderation: orders and groups] --> E3[/api/v1/admin/content]
    L[Activity log] --> E4[/api/v1/admin/audit-logs]
    S[Security view] --> E5[/api/v1/admin/security]
    X[CSV exports] --> E6[/api/v1/admin/export/*]
```

**Table 22\. Admin pages**

| Page | Endpoints | Filters | Actions | Audit events |
| :---- | :---- | :---- | :---- | :---- |
| Overview | `GET /api/v1/admin/stats` | \- | \- | \- |
| Users | `GET /api/v1/admin/users`, `POST /api/v1/admin/users/bulk-ban`, `POST /api/v1/admin/users/bulk-unban` | `q` (search), `role`, `status`, `offset`, `limit` | ban, unban, role change, revoke sessions, bulk ban/unban | `USER_BAN`, `USER_UNBAN`, `ROLE_CHANGE`, `SESSIONS_REVOKE`, `BULK_BAN`, `BULK_UNBAN` |
| User detail | `GET /api/v1/admin/users/{user_id}`, `POST /api/v1/admin/users/{user_id}/ban`, `POST /api/v1/admin/users/{user_id}/unban`, `POST /api/v1/admin/users/{user_id}/role`, `POST /api/v1/admin/users/{user_id}/revoke-sessions` | \- | single-user ban, unban, role change, revoke sessions | `USER_BAN`, `USER_UNBAN`, `ROLE_CHANGE`, `SESSIONS_REVOKE` |
| Moderation | `GET /api/v1/admin/content`, `DELETE /api/v1/admin/content/{content_type}/{content_id}`, `POST /api/v1/admin/content/bulk-delete` | `type` (`orders`, `menu`, `groups`), `q`, `offset`, `limit` | delete single or bulk records | `CONTENT_DELETE` |
| Activity log | `GET /api/v1/admin/audit-logs` | `action`, `user_id`, `q`, `offset`, `limit` | \- | \- |
| Security view | `GET /api/v1/admin/security` | aggregates failed logins by IP address and account | \- | \- |
| Exports | `GET /api/v1/admin/export/users`, `GET /api/v1/admin/export/orders`, `GET /api/v1/admin/export/audit-logs` | \- | download CSV (`campuseats_users.csv`, `campuseats_orders.csv`, `campuseats_audit_logs.csv`) | `EXPORT_CSV` |

Bulk actions return {"affected": \<int\>, "skipped": \<int\>}, skipping administrator accounts and the acting admin during bulk bans. CSV exports stream all matching rows as text/csv attachments via Python's csv.writer and record an EXPORT\_CSV entry in audit\_log.

### C9. Security Design and Threats

**Table 23\. Threats and defences**

| Threat | Defence | Where |
| :---- | :---- | :---- |
| Password database leak | Argon2id with a salt and a secret pepper, so stolen hashes are hard to crack | app/security.py |
| Stolen access token | Lifetime of 15 minutes; role and ban state are read from the database on every request | app/security.py, app/auth/ |
| Stolen refresh token | httpOnly cookie, only its hash is stored, rotation on use, revocation by logout, revoke or ban | app/auth/, user\_session |
| Brute-force login | Lockout after 5 failed attempts (429) and one generic error message | app/users/service.py |
| Privilege escalation | Registration always creates a customer; the role is never read from a request; admin self-protection rules | app/users/, app/admin/ |
| Access to another user's record | Ownership filtering in queries; 404 for another user's order | app/orders/, app/auth/rbac.py |
| Cross-site scripting | React escapes output (no use of dangerouslySetInnerHTML); the refresh token is not readable by scripts | frontend/src |
| Cross-site request forgery | The access token is sent in a header, not a cookie; the refresh cookie is SameSite and limited to the authentication paths | app/auth/ |
| CORS misuse | Only the frontend origin from FRONTEND\_ORIGIN is allowed | main.py, app/config.py |
| Secrets in the repository | Environment variables only; .env.example lists names | app/config.py |
| SQL injection | The ORM builds parameterised queries; no SQL is built from user text | repositories |
| Over-posting of fields | Separate input schemas; role, ban and ownership fields are not accepted from the client | schemas.py files |

### C10. Deployment on Vercel

CampusEats is one Vercel project with two services. The root vercel.json defines a backend service (the backend folder, FastAPI, entry point main:app) and a frontend service (the frontend folder, Vite). Rewrites send /api/\* to the backend and every other path to the frontend. frontend/vercel.json rewrites every path to index.html, so deep links and reloads work. The frontend calls the API on the same domain with relative /api/v1 paths, so there are no localhost addresses. The database is a hosted Supabase PostgreSQL project, reached through its transaction pooler.

**Figure 9\. Deployment layout**

```mermaid
flowchart LR
    G[GitHub main branch] -->|push triggers a build| V[Vercel project]
    V --> FE[Frontend service: Vite build]
    V --> BE[Backend service: FastAPI]
    BE --> DB[(Supabase PostgreSQL)]
    U[User's browser] --> V
```

**Table 24\. Environment variable names**

| Name | What it is for |
| :---- | :---- |
| DATABASE\_URL | Connection to Supabase PostgreSQL (empty locally, then SQLite is used) |
| JWT\_SECRET | Signs the access tokens; required in production |
| PASSWORD\_PEPPER | Secret mixed into every password before hashing; required in production |
| FRONTEND\_ORIGIN | The frontend address allowed by CORS |
| ACCESS\_TOKEN\_MINUTES | Access token lifetime (15) |
| REFRESH\_TOKEN\_DAYS | Refresh token lifetime (7) |
| CORS\_ORIGIN | Allowed frontend origin in production (optional when same-origin on Vercel) |

**How to redeploy.** Merge to main: Vercel builds and deploys by itself. To redeploy without a code change use the Redeploy button in the Vercel dashboard. A new table or column needs an Alembic migration run against Supabase before the code that needs it is deployed.

### C11. Testing

**Strategy.** Automated API tests (pytest) check the security rules on a temporary database. Manual tests on the live site check the interface and every admin feature. **How to run:** cd backend then pytest \-v.

**Table 25\. Automated tests and results**  
**Strategy.** Automated API integration tests (pytest) verify authentication, token rejection, refresh rotation, brute-force lockout, ownership isolation, group permissions, and administrative safety rules against an isolated SQLite test database. Manual end-to-end verification on the deployed Vercel URL (https\://2312144-s6-campuseats.vercel.app) confirms the user flows, DevTools cookie/header behavior, and all admin dashboard actions.

**How to run:** cd backend then pytest \-v.

| Test | Requirement it checks | Result |
| :---- | :---- | :---- |
| tests/test\_auth.py::test\_register\_and\_login | FR-AUTH-01, FR-AUTH-02 | PASSED |
| tests/test\_auth.py::test\_invalid\_password | FR-AUTH-02, NFR-SEC-02 | PASSED |
| tests/test\_auth.py::test\_brute\_force\_lockout | FR-AUTH-10 | PASSED |
| tests/test\_auth.py::test\_token\_rejection\_missing | FR-AUTH-05 | PASSED |
| tests/test\_auth.py::test\_token\_rejection\_tampered | FR-AUTH-05 | PASSED |
| tests/test\_auth.py::test\_token\_rejection\_expired | FR-AUTH-05 | PASSED |
| tests/test\_auth.py::test\_banned\_user\_immediate\_rejection | FR-RBAC-08 | PASSED |
| tests/test\_auth.py::test\_refresh\_token\_rotation | FR-AUTH-04, FR-AUTH-07 | PASSED |
| tests/test\_auth.py::test\_change\_password | FR-AUTH-08 | PASSED |
| tests/test\_rbac.py::test\_rbac\_ownership\_isolation | FR-RBAC-03 | PASSED |
| tests/test\_rbac.py::test\_rbac\_group\_permissions | FR-RBAC-05 | PASSED |
| tests/test\_rbac.py::test\_rbac\_admin\_safety\_rules | FR-RBAC-07 | PASSED |
| tests/test\_rbac.py::test\_rbac\_menu\_role\_boundaries | FR-RBAC-02 | PASSED |

**Total:** 13 tests, 13 passed, 0 failed (executed in 4.07s via pytest \-v).

## Part D. Evidence: Screenshots of the Running Application

### D1. User Side

**S1: Sign-up and login page with a validation error (a weak password) — Shows FR-AUTH-01, FR-AUTH-02**
![S1 — Sign-up and login page validation error](images/S1_signup_login_validation_error.png)

**S2: The main page of a logged-in customer: the menu and cart, and "My orders" showing only that customer's orders — Shows FR-DOMAIN-01, FR-DOMAIN-03, FR-DOMAIN-05, FR-RBAC-03**
![S2 — Logged-in customer orders](images/S2_logged_in_user_orders.png)

**S3: Profile page and the change-password form with a wrong current password rejected — Shows FR-AUTH-11, FR-AUTH-12**
![S3 — Profile change password rejected](images/S3_profile_change_password_rejected.png)

**S4: The sessions list with the revoke action — Shows FR-AUTH-08, FR-AUTH-09**
![S4 — Active sessions list and revoke action](images/S4_active_sessions_revoke.png)

**S5: A group page showing the members and their permissions — Shows FR-RBAC-04, FR-RBAC-05**
![S5 — Meal group members and permissions](images/S5_meal_group_members_permissions.png)

**S6: An action denied by RBAC: the message in the app and the 403 response in the network tab — Shows FR-RBAC-02, FR-RBAC-05, FR-RBAC-09**
![S6 — RBAC action denied with 403 response](images/S6_rbac_denied_403.png)

### D2. Security Behaviour

**S7: The network tab showing the Authorization header (token hidden) and an expired token returning 401 — Shows FR-AUTH-04, FR-AUTH-05, FR-AUTH-13**
![S7 — Authorization header and expired token 401](images/S7_network_auth_header_expired_401.png)

**S8: The refresh request returning a new access token, and the httpOnly cookie in the Application tab — Shows FR-AUTH-06, FR-AUTH-07**
![S8a — Refresh request returning a new access token](images/S8_refresh_token.png)
![S8b — campuseats_refresh HttpOnly cookie in Application tab](images/S8a_httponly_cookie.png)

**S9: A banned user rejected on the next request — Shows FR-RBAC-08**
![S9 — Banned user rejected with 403](images/S9_banned_user_rejected_403.png)

### D3. Admin Dashboard

**S10: Overview statistics — Shows FR-ADM-01**
![S10 — Admin dashboard overview statistics](images/S10_admin_overview_stats.png)

**S11: Users list with search, filters and pagination — Shows FR-ADM-02**
![S11 — Admin users list with search and pagination](images/S11_admin_users_search_pagination.png)

**S12: User detail with sessions and recent activity — Shows FR-ADM-03, FR-ADM-05, FR-ADM-06**
![S12 — Admin user detail with sessions and activity](images/S12_admin_user_detail_sessions_activity.png)

**S13: The ban dialog with a reason, and the banned state afterwards — Shows FR-ADM-04, FR-RBAC-07**
![S13 — Admin ban dialog and banned status](images/S13_admin_ban_dialog_and_status.png)

**S14: The moderation list of orders and groups with filters and a bulk action — Shows FR-ADM-07, FR-ADM-08**
![S14 — Content moderation list with filters and bulk action](images/S14_admin_moderation_filters_bulk.png)

**S15: The activity log with filters, showing the events caused by the steps above — Shows FR-ADM-09**
![S15 — Admin activity log with filters](images/S15_admin_audit_logs_filters.png)

**S16: The security view with failed logins by IP and by account — Shows FR-ADM-10, FR-AUTH-10**
![S16 — Security view with failed logins](images/S16_admin_security_failed_logins.png)

**S17: A CSV export downloaded and opened — Shows FR-ADM-11**
![S17 — CSV export downloaded and opened](images/S17_admin_csv_export_opened.png)

### D4. Deployment

**S18: The Vercel project with the production deployment and the domain**
![S18 — Vercel production deployment and domain](images/S18_vercel_frontend_deployment_domain.png)

**S19: The environment variable names in Vercel, with the values hidden**
![S19 — Vercel environment variables with values hidden](images/S19_vercel_env_variables_hidden.png)

**S20: The live API documentation page**
![S20 — Live FastAPI Swagger documentation](images/S20_live_api_swagger_docs.png)

### D5. Tests

**S21: The output of `pytest -v` showing every test and the result — Shows NFR-MAINT-02**
![S21 — Pytest automated test suite output](images/S21_pytest_automated_tests_passed.png)
## Part E. Project Management and Conclusion

### E1. How to Run and Test

**Prerequisites.** Python 3.10 or newer, Node.js 22 or newer, and Git.

**Environment file.** Copy `.env.example` from the repository root to `backend/.env` and set the variable names from Table 24\. Example values for local work: leave `DATABASE_URL` empty (SQLite is used), set `JWT_SECRET` and `PASSWORD_PEPPER` to long random strings, set `CORS_ORIGIN` to `http://localhost:5173`, `ACCESS_TOKEN_MINUTES` to `15` and `REFRESH_TOKEN_DAYS` to `7`.

**Backend** (terminal 1\)

```sh
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
fastapi dev main.py
```

**Frontend** (terminal 2\)

```sh
cd frontend
npm install
npm run dev
```

**Tests**

```sh
cd backend
pytest -v
```

**Logging in with the test accounts.** The seed script creates admin accounts, a kitchen staff account, normal customer accounts, a banned account and one shared meal group with mixed permissions. Log in as an **admin** to see the dashboard, as **kitchen staff** to see the kitchen board, and as a **user** (customer) for the shop and the group. The user IDs and passwords are in the Appendix of the PDF report only, never in this file.

### E2. GitHub Work

All development was conducted under GitHub account Mdhossain567 using structured issues, feature branches, and pull requests (\#4 through \#32) with commit messages referencing each tracking issue.

**Table 26\. Issues and pull requests**

| Feature | Issue | Pull requests | What it delivered |
| :---- | :---- | :---- | :---- |
| Documents (PRD, SRS, TDD) | \#3, \#5 | \#4, \#6 | Initial and updated planning, requirements, and technical design documents |
| Menu CRUD & Deployment (mid assessment, v0.1.0) | \#7 | \#8, \#9, \#10, \#11, \#12, \#13, \#14, \#15 | Database model, paginated REST API, React menu pages, Supabase PostgreSQL pooler, Vercel deployment, and SPA reload rewrites |
| JWT login, roles, protected menu | \#16 | \#17, \#18, \#19, \#20 | app\_user table with Argon2id \+ pepper hashing, register/login with lockout, auth pages, and role-protected menu endpoints |
| Orders and kitchen board (v0.1.5) | \#21 | \#22, \#23, \#24, \#25, \#26 | Order tables and endpoints, cart context/panel, My Orders page, Kitchen Board, and updated PRD/SRS/TDD docs |
| Final features (v0.2.0): sessions, RBAC, groups, admin, demo login | \#16, \#29, \#31 | \#27, \#28, \#30, \#32 | Rotating refresh sessions, immediate ban checks, centralized rbac.py, shared meal groups, admin dashboard/audit/exports, Alembic migrations, pytest suite, and demo login buttons |

Development progressed across three milestones: the mid-assessment menu CRUD and Vercel/Supabase deployment baseline (\#7–\#15), authentication and order/kitchen workflows (\#16–\#26), and the final assessment security, RBAC, shared meal groups, admin dashboard, automated test suite, and evaluation demo login controls (\#27–\#32).

### E3. Limitations

- Email addresses are not verified, and there is no password reset by email, so anyone can register with any email address. A new account is only a customer.  
- The cart is kept in memory only, so it is empty after a page reload.  
- The order pages refresh at fixed intervals (10 to 15 seconds); there are no real-time push updates.  
- A banned user is stopped on the next request, but the page of an idle user is logged out only at the next check, within about 10 seconds.  
- There is no rate limit beyond the account lockout, and no protection against many accounts being created automatically.  
- The free Supabase project can pause after inactivity, and the first request after a quiet period can be slow.  
- Migrations are run by hand against Supabase before a deployment that needs them.  
- Shared meal group orders operate as collaborative item pools without integrated online payment gateway settlement, and real-time kitchen board updates rely on explicit fetch refreshes rather than WebSocket push notifications. 

### E4. Future Work

1. Email verification and password reset by email, so accounts belong to real people.  
2. Rate limiting by IP address, to slow automated attacks.  
3. Real-time order updates with server-sent events or a managed realtime service, so customers and the kitchen do not wait for the next refresh.  
4. Online payment, so an order can be paid in the application.  
5. A larger automated test suite for the admin features and the group flows, and a continuous integration run on every pull request.

### E5. Sources, Libraries and Tools

**Table 27\. Sources, libraries and tools**

| Name | Version or link | What it was used for |
| :---- | :---- | :---- |
| FastAPI | [https\://fastapi.tiangolo.com](https://fastapi.tiangolo.com) | Backend framework and API docs |
| SQLModel and SQLAlchemy | [https\://sqlmodel.tiangolo.com](https://sqlmodel.tiangolo.com) | Models and database access |
| Alembic | [https\://alembic.sqlalchemy.org](https://alembic.sqlalchemy.org) | Database migrations |
| argon2-cffi | [https\://argon2-cffi.readthedocs.io](https://argon2-cffi.readthedocs.io) | Password hashing |
| PyJWT | [https\://pyjwt.readthedocs.io](https://pyjwt.readthedocs.io) | Signing and checking tokens |
| pytest | [https\://docs.pytest.org](https://docs.pytest.org) | Automated tests |
| React, TypeScript, Vite, React Router | [https\://react.dev](https://react.dev), [https\://vite.dev](https://vite.dev), [https\://reactrouter.com](https://reactrouter.com) | Frontend |
| Supabase | [https\://supabase.com/docs](https://supabase.com/docs) | Hosted PostgreSQL |
| Vercel | [https\://vercel.com/docs](https://vercel.com/docs) | Hosting |
| RFC 7519, RFC 9106, OWASP ASVS and Cheat Sheets | [https\://www\.rfc-editor.org](https://www.rfc-editor.org), [https\://owasp.org](https://owasp.org) | Design of the security features |

**AI tools.** I used AI tools during this project. I used Claude (Anthropic) for step-by-step guidance, explanations, draft code and draft documents, and an AI coding agent (Google Antigravity) for part of the final-assessment implementation. AI coding assistants were used to accelerate boilerplate scaffolding for FastAPI routers, React TypeScript components, and Alembic migration scripts. Every generated endpoint, SQLModel constraint, and cookie configuration was manually inspected, debugged against live Vercel/Supabase deployment errors (including SPA rewrite rules and \`psycopg\` pooler compatibility), and verified end-to-end through the 13 automated \`pytest\` security tests and manual browser DevTools checks.  I can explain all submitted code in the code defence viva.

---

