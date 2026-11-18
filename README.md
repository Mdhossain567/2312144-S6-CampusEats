# CampusEats

CampusEats is a cafeteria ordering system where students and staff can browse the university cafeteria menu, place food orders, and track their order status. Cafeteria managers manage menu items, and kitchen staff view incoming orders and update their preparation status. It is built with React + TypeScript and FastAPI REST APIs, with accounts, Argon2 password hashing, token-based login and role-based access control.

**Status:** the menu feature (MVP) and the Beta features for accounts, roles and orders are built and deployed on Vercel with Supabase PostgreSQL. The refresh token with a server-side logout, profile editing and the admin user screens are planned.

## Features

**MVP (demo before mid-term)**

- Create, list (with pagination, category filter and search), view, update and delete menu items through a REST API (`/api/v1/menu`)
- React pages for the menu list, item details, add and edit
- Input validation with clear error responses
- Interactive API docs at `/api/docs`

**Beta (demo before final)**

- Sign up and log in; passwords are stored only as Argon2id hashes; a JWT access token (15 minutes)
- Login lockout: 5 failed attempts block login for 15 minutes
- Roles: customer, kitchen staff, admin, enforced on the server
- Only admins add, edit or delete menu items
- Customers: a cart, placing an order and a "My orders" page with statuses and cancelling
- Kitchen staff and admins: a kitchen board that moves orders through pending, preparing, ready and completed
- Profile page (view)

**Planned**

- Refresh token and logout on the server, profile editing and password change
- Admin user management and statistics, security headers

## User roles

- **Customer:** browse the menu, place orders, see and cancel own pending orders.
- **Kitchen staff:** see all orders and move them through the status steps.
- **Admin:** manage menu items, see all orders, do everything kitchen staff can do.

Everyone registers as a customer. See "Making an admin or kitchen account" below.

## Tech stack

| Part | Choice |
|------|--------|
| Frontend | React + TypeScript + Vite + React Router |
| Backend | Python 3.10+, FastAPI, SQLModel |
| API | REST, JSON (`application/json`) |
| Security | Argon2id (`argon2-cffi`), JWT (`PyJWT`) |
| Database | Supabase PostgreSQL (production), SQLite (local) |
| Hosting | Vercel (frontend and backend in one project) |

## Documentation

| Doc | What it covers |
|-----|----------------|
| [PRD](docs/01-prd.md) | Goals, features, user stories, milestones, implementation status |
| [SRS](docs/02-srs.md) | Requirements, use cases, permissions, acceptance criteria, implementation status |
| [TDD](docs/03-tdd.md) | Architecture, data model, API endpoints, authentication and security, deployment |

## Project structure

```text
backend/
  main.py             FastAPI app entry point
  scripts/set_role.py change the role of an account
  app/
    config.py         settings from environment variables
    security.py       password hashing and tokens
    database.py       engine and session
    menu_items/       menu feature
    users/            accounts
    auth/             current user and roles, register and login endpoints
    orders/           orders feature
frontend/
  src/
    components/       menu item form, cart panel, protected route
    context/          login state and cart
    pages/            menu, login, register, profile, My orders, kitchen board
    services/         api.ts, the only place that calls the backend
    types/            TypeScript types
docs/                 PRD, SRS, TDD
vercel.json           /api/* goes to the backend, everything else to the frontend
```

## API (summary)

| Area | Endpoints |
|------|-----------|
| Menu | `GET /api/v1/menu` (paged, public), `GET /api/v1/menu/{id}`, `POST`, `PATCH` and `DELETE` (admin only) |
| Accounts | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Orders | `POST /api/v1/orders` (customer), `GET /orders/my` (customer), `GET /orders` (kitchen staff, admin), `GET /orders/{id}`, `PATCH /orders/{id}/status` (kitchen staff, admin), `POST /orders/{id}/cancel` |

All lists return `{items, total, offset, limit}`. Full details are in the TDD and at `/api/docs`.

## Requirements

- Python 3.10+
- Node.js 22+

On macOS/Linux, use `python3` instead of `python`.

## Run locally

You need two terminals. Data is saved in a local SQLite file, `backend/campuseats.db`, created automatically and not committed.

**First time**

Backend (terminal 1):

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py
```

Frontend (terminal 2):

```bash
cd frontend
npm install
npm run dev
```

**Running again**

Activate the virtual environment and run `fastapi dev main.py` in `backend`, then `npm run dev` in `frontend`. Run `pip install -r requirements.txt` or `npm install` again only when a dependency changes.

Open http://localhost:5173. Vite forwards `/api` requests to the backend on port 8000. API docs: http://localhost:8000/api/docs.

**Reset the local data:** stop the backend and delete `backend/campuseats.db`.

## Making an admin or kitchen account

Everyone registers as a customer. To change a role:

- **Locally:** register the account in the app, then run this in `backend/`:
  ```bash
  python scripts/set_role.py you@example.com admin
  ```
  Use `kitchen_staff` for a kitchen account.
- **On Supabase:** register the account on the live site, then open Table Editor, `app_user`, and change the `role` cell of that row.

## Environment variables

Locally nothing needs to be set. In production set variables in Vercel under Project > Settings > Environment Variables. Never commit secrets or `.env` files.

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | The Supabase **transaction pooler** URL (port 6543), for example `postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres`. Leave it unset locally to use SQLite. If the password has special characters, URL-encode them (`@` becomes `%40`) |
| `POSTGRES_URL` | Used when `DATABASE_URL` is not set |
| `JWT_SECRET` | A long random string, for example `python -c "import secrets; print(secrets.token_urlsafe(48))"`. **Required on Vercel**: the app refuses to start without it. A fixed development value is used locally |
| `ACCESS_TOKEN_MINUTES` | Default 15 |
| `REFRESH_TOKEN_DAYS` | Default 7 (for the planned refresh token) |

Vercel cannot keep a SQLite file between requests, so without `DATABASE_URL` the deployed app would lose its data.

## Deploy to Vercel

1. Push the repo to GitHub.
2. Go to https://vercel.com/new, import the repo and click Deploy. Keep Root Directory as `./`.
3. Add `DATABASE_URL` and `JWT_SECRET` (Production and Preview) and redeploy.
4. Register an account on the live site and make it an admin (see above).

Every push to `main` redeploys automatically.

## Contributing

Every change starts from a GitHub issue.

- Branch: `mdhossain/#{issue_number}-{task_title}`
- Commit: `<type>: <summary> (#issue)`, for example `feat: add the order tables (#21)`
- Pull request title: `<type>: <summary> (#issue)`; description with Summary, Changes, How it was tested and Notes
- Each pull request ends with `Ref #{issue_number}`; the last pull request for an issue uses `Closes #{issue_number}`

## Troubleshooting

- "Running scripts is disabled" in PowerShell: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- `fastapi` not found: activate the virtual environment first.
- `ModuleNotFoundError` for `sqlmodel`, `psycopg`, `jwt` or `argon2`: run `pip install -r requirements.txt` inside the activated virtual environment.
- "Request failed" in the app: the backend isn't running, or `DATABASE_URL` is wrong.
- 500 `FUNCTION_INVOCATION_FAILED` on Vercel: check the runtime logs; usually `JWT_SECRET` or `DATABASE_URL` is missing for that environment, or the Supabase project is paused.
- "password authentication failed" with Supabase: check the password in `DATABASE_URL` and URL-encode special characters, or reset the database password to letters and numbers only.
- Locked out after failed logins: wait 15 minutes.
- Data looks wrong locally: stop the backend and delete `backend/campuseats.db`; it is recreated on the next start.
- Vercel build fails: check the Build Logs, and make sure `npm run build` works in `frontend/`.