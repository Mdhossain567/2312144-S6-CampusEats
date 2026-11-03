# CampusEats

A campus cafeteria pre-order system. Students and staff browse the cafeteria menu, place food orders and track their status; cafeteria managers manage menu items, and kitchen staff update order progress. Built as a REST API with FastAPI and a React + TypeScript frontend, deployed on Vercel.

**Live demo:** https://2312144-s6-campuseats.vercel.app

> **Status:** MVP release. Menu item management (create, list, view, update, delete) works through the REST API and the React UI. Orders, login and roles are planned for the Beta.

## Features

**MVP (demo before mid-term)**

- Menu item CRUD through a REST API (`/api/v1/menu`)
- Paged menu list (offset and limit) with the total count
- Input validation with clear error responses (422 for invalid data, 409 for a duplicate name, 404 for a missing item)
- React UI: menu list with Next/Previous pages, item details, add, edit and delete
- Interactive API docs at `/api/docs`

**Beta (demo before final)**

- Place and track orders, kitchen order board
- Sign up, log in, log out (JWT access token + refresh token)
- Roles: customer, kitchen staff and admin (RBAC)
- Profile page, admin dashboard, security hardening

## User roles

| Role | What they do |
|------|--------------|
| Admin / Cafeteria Manager | Manage menu items, prices and availability; view all orders |
| Kitchen Staff | View incoming orders and update preparation status |
| Customer (Student/Staff) | Browse the menu, place orders, view order history |

In the MVP there is no login, so every client acts anonymously. Roles are enforced from the Beta.

## Tech stack

| Part | Choice |
|------|--------|
| Frontend | React + TypeScript, built with Vite |
| Backend | Python 3.10+, FastAPI, SQLModel |
| Database | Supabase PostgreSQL (production), SQLite (local) |
| API | REST, documented with OpenAPI at `/api/docs` |
| Hosting | Vercel (frontend and backend in one project) |
| Beta extras | Alembic (migrations), PyJWT, Argon2 password hashing |

## Documentation

- [PRD - Product Requirements Document](docs/01-prd.md): goals, features, user stories, milestones
- [SRS - Software Requirements Specification](docs/02-srs.md): requirements, validation rules, acceptance criteria
- [TDD - Technical Design Document](docs/03-tdd.md): architecture, data model, API endpoints, configuration, deployment

## Project structure

```text
backend/    FastAPI app (routes under /api)
  main.py           app entry point
  app/menu_items/   menu feature: router, service, repository, schemas
frontend/   Vite + React + TypeScript
  src/pages/        menu list and item details pages
  src/services/     api.ts, the only place that talks to the backend
  src/types/        TypeScript types
docs/       PRD, SRS, TDD
vercel.json Vercel setup: /api/* goes to the backend, everything else to the frontend
```

## How it works

**Frontend:** a page shows the screen and keeps its data, and `services/api.ts` sends every request to the backend.

**Backend:** each layer has one job. The router handles HTTP and status codes, the service applies the rules, and the repository reads and writes the database. The response goes back up the same way.

## API endpoints (MVP)

Base path: `/api/v1`

| Method | Endpoint | Description | Success |
|--------|----------|-------------|---------|
| POST | `/menu` | Create a menu item | 201 |
| GET | `/menu?offset=0&limit=20` | List items, paged: `{items, total, offset, limit}` (limit 1 to 100) | 200 |
| GET | `/menu/{id}` | Get one item | 200 |
| PATCH | `/menu/{id}` | Update an item | 200 |
| DELETE | `/menu/{id}` | Delete an item | 204 |

Full details and a live try-out page: `/api/docs`.

## Requirements

- [Python](https://www.python.org/downloads/) 3.10+
- [Node.js](https://nodejs.org/) 22+

> On macOS/Linux, use `python3` instead of `python`.

## Run locally

You need two terminals: one for the backend and one for the frontend. Locally the app saves data in a SQLite file that is created automatically on the first run and is not committed.

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

**Running again (after the initial setup)**

Backend (terminal 1):

```bash
cd backend
.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate
fastapi dev main.py
```

Frontend (terminal 2):

```bash
cd frontend
npm run dev
```

Open http://localhost:5173. Vite forwards `/api` requests to the backend on port 8000. API docs: http://localhost:8000/api/docs.

To run it the way Vercel does instead, from the project root:

```bash
npm install -g vercel
vercel dev -L
```

> Add new Python packages to `backend/requirements.txt`. Run `pip install -r requirements.txt` or `npm install` again only when a dependency changes.

## Environment variables

Locally nothing needs to be set: the app uses the SQLite file. In production (Vercel) the app uses Supabase PostgreSQL. Set variables in Vercel under **Project → Settings → Environment Variables**. A local `.env` is never committed.

| Variable | Needed for | Notes |
|----------|------------|-------|
| `DATABASE_URL` | Production | The Supabase **transaction pooler** URL (port 6543), for example `postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres`. **Leave it unset locally** to use SQLite. Vercel cannot keep a SQLite file between requests, so without a hosted database the deployed app loses its data. |

Never commit secrets, passwords or `.env` files.

## Deploy to Vercel

1. Push the repo to GitHub.
2. Go to https://vercel.com/new, import the repo and click **Deploy**. Keep **Root Directory** as `./`.
3. Add `DATABASE_URL` in the project's environment variables, then redeploy.

Every push to `main` redeploys automatically, and every pull request gets a preview deployment.

## Contributing

Every change starts from a GitHub issue.

- **Branch:** `mdhossain/#{issue_number}-{short-title}`, for example `mdhossain/#7-add-menu-create-ui`
- **Commit:** `<type>: <summary> (#issue)`, for example `feat: add create menu item form (#7)`
- **Pull request:** one small PR per task, with `Refs #{issue_number}` in the description, and `Closes #{issue_number}` in the last one

## Troubleshooting

- **"Running scripts is disabled" in PowerShell:** run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **`fastapi` not found:** activate the virtual environment first.
- **`ModuleNotFoundError`:** run `pip install -r requirements.txt` inside the activated virtual environment.
- **`Request failed: 500` in the app:** the backend isn't running.
- **The menu page shows no Next button:** the pager shows 5 items per page, so add more than 5 items.
- **Data looks wrong locally:** stop the backend and delete the local SQLite file; it is recreated on the next start.
- **App at localhost:8000 shows an old version:** delete `frontend/dist`.
- **Vercel build fails:** check **Build Logs** in the Vercel dashboard, and make sure `npm run build` works in `frontend/`.