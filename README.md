# CampusEats

CampusEats is a campus cafeteria ordering system. Students and staff browse the cafeteria menu, place orders and follow their status. Kitchen staff prepare the orders, and administrators manage the menu, the users and the whole system. It is a multi-user application with token-based login, role-based access control, shared meal groups and an admin dashboard.

| | |
|---|---|
| **Live app** | https://2312144-s6-campuseats.vercel.app |
| **API docs** | https://2312144-s6-campuseats.vercel.app/api/docs |
| **Release** | v0.2.0 (final submission) |
| **Course** | CSE309, Autumn 2026 |

## Status

All planned features are implemented, covered by automated tests (`pytest`) and deployed on Vercel with a hosted Supabase PostgreSQL database.

| Release | What it delivered |
|---------|-------------------|
| v0.1.0 (MVP) | Menu item CRUD with pagination, search and filters, deployed on Vercel |
| v0.1.5 (Beta) | Accounts and login, roles, orders, cart and kitchen board |
| v0.2.0 (Final) | Sessions and refresh tokens, password pepper, profile and password change, central RBAC, meal groups with permissions, admin dashboard, audit log, migrations, seed data and tests |

## Features

### Menu and orders
- Menu items with category, price and availability: create, list (paginated, with search and a category filter), view, update and delete, through a REST API and React pages. Only admins change the menu; everybody can read it.
- Customers use a cart, place orders and follow them on a "My orders" page, and can cancel an order while it is pending.
- Kitchen staff use a kitchen board that moves orders through pending, preparing, ready and completed.
- The server calculates every total from the menu prices and keeps the name and price of each item inside the order, so later menu changes do not change old orders.

### Authentication and sessions
- Sign up and log in. Passwords are stored only as **Argon2id** hashes, mixed with a secret **pepper** (`PASSWORD_PEPPER`) kept in an environment variable.
- A signed **JWT access token** that lives 15 minutes and contains the user id (`sub`) and the role. It is checked on every protected request. A missing, invalid, tampered or expired token returns `401`.
- A **rotating 7-day refresh token** in an `httpOnly` cookie, stored on the server in the `user_session` table. Logging out invalidates the session on the server.
- Users can list their active sessions (device, IP address, times) and revoke any of them.
- Profile update and password change (the current password is required, the new one is validated).
- **Brute-force protection:** 5 failed logins lock the account temporarily (`429`). A wrong email and a wrong password give the same error message.
- The frontend refreshes or logs out when the server rejects a token, and does not flash guest content while a session is being restored.

### Roles and access control (RBAC)
- Three roles stored in the database: `customer`, `kitchen_staff` and `admin`. (In the course specification, "user" means a customer or a kitchen staff member.)
- One central module, `backend/app/auth/rbac.py`, with the permissions and the reusable dependencies used by the endpoints. The role is read from the database on every request, not trusted from the token.
- **Ownership rules:** a normal user can only read, change or cancel their own records. Another user's record returns `403` or `404`.
- **Banned users** are rejected on their very next request with `403`, are logged out of the interface within seconds, and cannot log in.
- **Safety rules:** an admin cannot ban another admin, cannot ban themselves, and cannot change or lower their own role.
- The React app has route guards and role-based menus that match the server rules. The server is the real protection.

### Meal groups (shared resource)
Customers can share an order list in a meal group, and every member has different permissions:
- **Owner:** the only one who can rename or delete the group and manage its members and their permissions.
- **`can_create`:** add items to the group order.
- **`can_edit`:** change quantities or instructions of items.
- **`can_assign`:** assign items to members.
- Actions without the needed permission are refused by the server (`403`).

### Admin dashboard
- Overview statistics: total users, banned users, orders, groups and new sign-ups in the last 7 days.
- Users: search, filters by role and status, pagination and a detail view with the user's records, groups, sessions and recent activity.
- Actions: ban and unban with a reason (single and bulk), role change, revoke sessions.
- Content moderation: lists of orders and groups with filters, and single or bulk delete.
- **Audit log:** login, failed login, logout, password change, role change, ban, delete and export events, with the user, IP address, browser and time, searchable and filterable.
- Security view: failed logins by IP address and by account.
- CSV exports of users, records and activity that respect the current filters.

### Quality
- Database schema managed with **Alembic** migrations.
- A **seed script** for demo data (see below).
- Automated **pytest** tests for login, lockout, token rejection and the access-control rules.
- No secrets in the repository (only `.env.example`). CORS is limited to the frontend origin.

## Roles and permissions (summary)

| Action | Customer | Kitchen staff | Admin |
|--------|:--------:|:-------------:|:-----:|
| Browse the menu | Yes | Yes | Yes |
| Add, edit or delete menu items | No | No | Yes |
| Place an order and see own orders | Yes | No | No |
| See all orders | No | Yes | Yes |
| Change an order's status | No | Yes | Yes |
| Use the admin dashboard, manage users | No | No | Yes |

The complete matrix, with the ownership and group rules, is in `docs/02-srs.md` and `docs/FINAL_REPORT.md`.

## Demo accounts and shared group (for the instructor)

**Passwords are not written in this repository.** They are provided in the instructor submission form and in the PDF report.

| User ID (email) | Name | Role | Notes |
|-----------------|------|------|-------|
| `admin1@campuseats.com` | Chief Administrator | `admin` | Full admin dashboard |
| `admin2@campuseats.com` | Auditor Admin | `admin` | Second admin, for the "cannot ban another admin" rule |
| `chef@campuseats.com` | Chef Mario | `kitchen_staff` | Kitchen board |
| `alice@campuseats.com` | Alice Student | `customer` | Owner of the shared group |
| `bob@campuseats.com` | Bob Fellow | `customer` | Group member |
| `charlie@campuseats.com` | Charlie Staff | `customer` | Group member |
| `banned@campuseats.com` | Suspended Account | `customer` | Banned, to check the `403` response |

**Shared group: "Faculty & Student Lunch Club"**

| Member | Group role | `can_create` | `can_edit` | `can_assign` |
|--------|-----------|:------------:|:----------:|:------------:|
| Alice | Owner | Yes | Yes | Yes (and manages the group) |
| Bob | Member | Yes | Yes | No |
| Charlie | Member | Yes | No | Yes |

Sample data (menu items and orders) is created by the seed script.

**Quick checks for the instructor**
- Log in as `alice` or `bob`, open a group and try to assign an item as Bob: the server refuses (`403`).
- Log in as `charlie` and try to edit an item: the server refuses (`403`).
- Try to log in as `banned@campuseats.com`: the account is refused (`403`).
- Log in as `admin1` and open the admin dashboard: statistics, users, ban and unban with a reason, audit log, security view and CSV export.
- Log in as `chef` and open the kitchen board to move an order forward.

## Tech stack

| Part | Choice |
|------|--------|
| Frontend | React + TypeScript + Vite + React Router |
| Backend | Python 3.10+, FastAPI, SQLModel |
| Security | Argon2id (`argon2-cffi`) with a pepper, JWT (`PyJWT`), `httpOnly` refresh cookie |
| Database | Supabase PostgreSQL (production), SQLite (local) |
| Migrations | Alembic |
| Tests | pytest |
| Hosting | Vercel (frontend and backend in one project) |

## Project structure

```text
backend/
  main.py                    FastAPI app entry point
  alembic/                   database migrations
  scripts/seed.py            demo accounts and sample data
  scripts/set_role.py        change the role of an account
  tests/                     pytest tests (login, tokens, access control)
  app/
    config.py, security.py, database.py, clock.py
    menu_items/              menu feature
    users/                   accounts
    auth/                    login, sessions, current user, rbac.py
    orders/                  orders and the kitchen workflow
    groups/                  meal groups and member permissions
    admin/                   admin dashboard endpoints
    audit/                   audit log
frontend/
  src/
    components/              reusable parts and route guards
    context/                 login state and cart
    pages/                   menu, login, orders, kitchen, groups, admin and more
    services/                api.ts, the only place that calls the backend
    types/                   TypeScript types
docs/                        PRD, SRS, TDD and the final report
vercel.json                  /api/* goes to the backend, everything else to the frontend
```

## API overview

Every list returns `{items, total, offset, limit}`. The complete and current list of endpoints, with their request and response shapes, is at `/api/docs`.

| Area | Examples |
|------|----------|
| Menu | `GET /api/v1/menu` (public), `POST`, `PATCH`, `DELETE` (admin) |
| Authentication | `POST /api/v1/auth/register`, `/login`, `/refresh`, `/logout`; `GET /api/v1/auth/me`; sessions, profile update and password change under `/api/v1/auth` |
| Orders | place an order, my orders, all orders and status changes (kitchen staff and admin), cancel |
| Groups | create a group, manage members and permissions, add, edit and assign items |
| Admin | statistics, users (ban, unban, role, sessions), moderation, audit log, security view, CSV exports |

## Run locally

You need Python 3.10+ and Node.js 22+. On macOS or Linux use `python3` instead of `python`.

**Backend** (terminal 1)

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head            # creates the tables
python -m scripts.seed          # demo accounts and sample data (local use)
fastapi dev main.py
```

**Frontend** (terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite forwards `/api` requests to the backend on port 8000. API docs: http://localhost:8000/api/docs.

Locally `DATABASE_URL` is empty, so the app uses the SQLite file `backend/campuseats.db`. To start again, stop the backend, delete that file and run `alembic upgrade head` once more.

## Tests

```bash
cd backend
pytest -v
```

The tests cover login and the brute-force lockout, rejection of missing, expired and tampered tokens, ownership rules, group permissions, the admin safety rule (an admin cannot ban another admin) and the immediate rejection of a banned user.

## Environment variables

Never commit secrets or a `.env` file. `.env.example` lists the names only. In production, set them in Vercel under Project > Settings > Environment Variables.

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | The Supabase **transaction pooler** URL (port 6543). Leave it empty locally to use SQLite. URL-encode special characters in the password |
| `JWT_SECRET` | A long random string that signs the access tokens. Required in production: the app refuses to start without it |
| `PASSWORD_PEPPER` | A long random secret mixed into every password before hashing. Required in production. Never change it after users exist |
| `FRONTEND_ORIGIN` | The deployed frontend URL, used to limit CORS (`https://2312144-s6-campuseats.vercel.app`) |
| `ACCESS_TOKEN_MINUTES` | Access token lifetime, 15 by default |
| `REFRESH_TOKEN_DAYS` | Refresh token lifetime, 7 by default |

A random secret can be made with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

## Deployment (Vercel and Supabase)

1. Push the repository to GitHub and import it on https://vercel.com/new. Keep the root directory as `./`.
2. Set `DATABASE_URL`, `JWT_SECRET`, `PASSWORD_PEPPER` and `FRONTEND_ORIGIN` for Production and Preview.
3. Run `alembic upgrade head` against the Supabase database from your own machine, **before** you deploy code that needs a new table or column. Use the Supabase session pooler for migrations. Back up the database first.
4. Load the demo data with `python -m scripts.seed` only on a database you accept to fill with demo accounts.
5. Open the live site and the API docs page and test login, refresh, access control, groups and the admin dashboard.

Every push to `main` redeploys automatically. `frontend/vercel.json` rewrites every path to `index.html`, so deep links and page reloads work.

## Documentation

| Document | What it covers |
|----------|----------------|
| [PRD](docs/01-prd.md) | Goals, users, features, milestones |
| [SRS](docs/02-srs.md) | Requirements, permissions, acceptance criteria |
| [TDD](docs/03-tdd.md) | Architecture, data model, endpoints, security design |
| [Final report](docs/FINAL_REPORT.md) | The three documents together with testing and live deployment evidence |

## Working with Git

Every change starts from a GitHub issue.

- Branch: `mdhossain/#{issue}-{short-title}`
- Commit: `<type>: <summary> (#issue)`
- Pull request: title `<type>: <summary> (#issue)`, a description with Summary, Changes, How it was tested and Notes, ending with `Ref #{issue}` (the last pull request of an issue uses `Closes #{issue}`)

## Troubleshooting

- "Running scripts is disabled" in PowerShell: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- `fastapi` not found: activate the virtual environment first.
- A missing module such as `argon2`, `jwt` or `psycopg`: run `pip install -r requirements.txt` inside the activated environment.
- "no such table" locally: run `alembic upgrade head` in `backend/`.
- The app refuses to start in production: set `JWT_SECRET` and `PASSWORD_PEPPER` in the Vercel variables.
- 500 `FUNCTION_INVOCATION_FAILED` on Vercel: read the runtime logs; usually a variable is missing for that environment or the Supabase project is paused.
- "password authentication failed" with Supabase: check the password in `DATABASE_URL` and URL-encode special characters.
- Account locked after failed logins: wait for the lock time to pass.