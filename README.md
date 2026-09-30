# URL Shortener

A small multi-tenant URL shortener built with FastAPI, SQLAlchemy, and PostgreSQL. Users can create an account, shorten URLs, and view their links and click counts.

## Live app

Visit the deployed app: [url-shortener-50lo.onrender.com](https://url-shortener-50lo.onrender.com/)

Interactive API documentation is available at [/docs](https://url-shortener-50lo.onrender.com/docs).

## Features

- Account registration and login with HttpOnly cookie authentication
- Short links scoped to the signed-in account
- Public short-link redirects
- Click counts for shortened URLs
- Browser interface for managing links

## Run locally

Requires Python 3.10 or newer and PostgreSQL, or SQLite for local development.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

For SQLite, no database environment variable is required; the app uses `./urls.db` by default. Start the development server with:

```powershell
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000/) for the frontend or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the API docs.

Set `JWT_SECRET_KEY` to a long random value before starting the app. For local HTTP development only, set `COOKIE_SECURE=false`; deployed sites must use HTTPS and leave `COOKIE_SECURE=true`.

## Deploy on Render with Neon

Create a PostgreSQL database in Neon and set these environment variables for the Render web service:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Neon PostgreSQL connection string, including `sslmode=require` |
| `JWT_SECRET_KEY` | A long, randomly generated secret |
| `COOKIE_SECURE` | `true` (the default); keep enabled for HTTPS deployments |

Use these Render commands:

```text
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The application creates its tables when it starts. `create_all()` creates missing tables but does not migrate existing tables when the schema changes.

## API

### Register

```http
POST /auth/register
Content-Type: application/json

{"name":"Aniket","email":"aniket@example.com","password":"your-password"}
```

### Log in

```http
POST /auth/login
Content-Type: application/json

{"email":"aniket@example.com","password":"your-password"}
```

The response sets an HttpOnly `linklet_token` cookie. Browsers send it automatically; JavaScript cannot read it. Requests that change state must include the same-origin `Origin` header.

### Create a short URL

```http
POST /shorten
Content-Type: application/json

{"url":"https://example.com/a/long/path"}
```

### List your URLs

```http
GET /my-urls
```

Open the returned `short_url` to redirect to its destination. Each redirect increments its click count.
