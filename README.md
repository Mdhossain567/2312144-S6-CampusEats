# CampusEats

CampusEats is a cafeteria ordering system where students and staff can browse the university cafeteria menu, place food orders, and track their order status. Cafeteria managers manage menu items, prices, and availability, while kitchen staff view incoming orders and update their preparation status. The application is built with React + TypeScript and FastAPI REST APIs, with authentication and role-based access control planned for the Beta release.

**Status:** MVP in progress. Menu item CRUD (create, paginated list, view, update, delete) works through REST APIs and a React UI, running locally with SQLite and in production on Supabase PostgreSQL. Orders, authentication and roles are planned for the Beta.

## Features

**MVP (demo before mid-term)**

- Create, list (with pagination, category filter and search), view, update and delete menu items through a REST API (`/api/v1/menu`)
- React pages for the menu list, item details, add and edit
- Input validation with clear error responses
- Interactive API docs at `/api/docs`

**Beta (demo before final)**

- Sign up, log in, log out (JWT access token + refresh token)
- User profile page
- Roles: customer, kitchen staff, admin, enforced with role-based access control
- Orders and the kitchen board
- Admin user management and dashboard statistics
- Security hardening

## User roles

- **Admin / Cafeteria Manager:** manage menu items, prices and availability; view all orders.
- **Kitchen Staff:** view incoming orders and update preparation status.
- **Customer (Student/Staff):** browse the menu, place orders, view order history.

## Tech stack

| Part | Choice |
|------|--------|
| Frontend | React + TypeScript + Vite |
| Backend | Python 3.10+, FastAPI, SQLModel |
| API | REST, JSON (`application/json`) |
| Database | Supabase PostgreSQL (production), SQLite (local) |
| Hosting | Vercel (frontend and backend in one project) |

## Documentation

| Doc | What it covers |
|-----|----------------|
| [PRD](docs/01-prd.md) | Goals, features, user stories, milestones |
| [SRS](docs/02-srs.md) | Requirements, use cases, permissions, acceptance criteria |
| [TDD](docs/03-tdd.md) | Architecture, data model, API endpoints, deployment |

## Project structure

```text
backend/
  main.py             FastAPI app entry point
  app/
    config.py         settings (DATABASE_URL)
    database.py       engine and session
    menu_items/       model, schemas, repository, service, router
frontend/
  src/
    components/       reusable UI parts (menu item form)
    pages/            list, details, add and edit pages
    services/         api.ts, the only place that calls the backend
    types/            TypeScript types
docs/                 PRD, SRS, TDD
vercel.json           /api/* goes to the backend, everything else to the frontend
```

## API (MVP)

| Method | Path | Result |
|--------|------|--------|
| POST | `/api/v1/menu` | 201, creates a menu item |
| GET | `/api/v1/menu?offset=0&limit=20` | 200, `{items, total, offset, limit}` (limit 1 to 100); optional `category`, `available`, `q` |
| GET | `/api/v1/menu/{id}` | 200 or 404 |
| PATCH | `/api/v1/menu/{id}` | 200 or 404, only sent fields change |
| DELETE | `/api/v1/menu/{id}` | 204 or 404 |

## Requirements

- Python 3.10+
- Node.js 22+

On macOS/Linux, use `python3` instead of `python`.

## Run locally

You need two terminals: one for the backend and one for the frontend. Menu items are saved in a local SQLite file, `backend/campuseats.db`, which is created automatically on the first run and is not committed.

**First time (initial setup)**

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

## Environment variables

Locally nothing needs to be set: the app uses the SQLite file `backend/campuseats.db`. In production (Vercel) the app uses Supabase PostgreSQL. Set variables in Vercel under Project > Settings > Environment Variables. Never commit secrets or `.env` files.

| Variable | Needed for | Notes |
|----------|------------|-------|
| `DATABASE_URL` | MVP (production) | The Supabase **transaction pooler** URL (port 6543), for example `postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres`. Leave it unset locally to use SQLite. If the password contains special characters, URL-encode them (for example `@` becomes `%40`). |
| `POSTGRES_URL` | MVP (production) | Used when `DATABASE_URL` is not set (for example when set by the Supabase integration on Vercel). |
| `JWT_SECRET` | Beta | A long random string. |
| `ACCESS_TOKEN_MINUTES` | Beta | Default 15. |
| `REFRESH_TOKEN_DAYS` | Beta | Default 7. |

Vercel cannot keep a SQLite file between requests, so without `DATABASE_URL` the deployed app would lose its data.

## Deploy to Vercel

1. Push the repo to GitHub.
2. Go to https://vercel.com/new, import the repo and click Deploy. Keep Root Directory as `./`.
3. Add `DATABASE_URL` under Settings > Environment Variables (Production and Preview) and redeploy.

Every push to `main` redeploys automatically.

## Contributing

Every change starts from a GitHub issue.

- Branch: `mdhossain/#{issue_number}-{task_title}`
- Commit: `<type>: <summary> (#issue)`, for example `feat: add menu item service (#7)`
- Pull request title: `<type>: <summary> (#issue)`; description with Summary, Changes, How it was tested and Notes
- Each pull request ends with `Ref #{issue_number}`; the last pull request for an issue uses `Closes #{issue_number}`

## Troubleshooting

- "Running scripts is disabled" in PowerShell: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- `fastapi` not found: activate the virtual environment first.
- `ModuleNotFoundError: sqlmodel` or `psycopg`: run `pip install -r requirements.txt` inside the activated virtual environment.
- "Request failed" in the app: the backend isn't running, or `DATABASE_URL` is wrong.
- "password authentication failed" with Supabase: check the password in `DATABASE_URL` and URL-encode special characters, or reset the database password to letters and numbers only.
- Menu items look wrong locally: stop the backend and delete `backend/campuseats.db`; it is recreated on the next start.
- Vercel build fails: check the Build Logs in the Vercel dashboard, and make sure `npm run build` works in `frontend/`.