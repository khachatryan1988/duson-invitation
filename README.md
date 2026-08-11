# DUSON Invitation — Docker + PostgreSQL

This package is ready to run with Docker Compose.

Included:

- Flask
- Gunicorn
- PostgreSQL 16
- persistent PostgreSQL volume
- responsive DUSON landing page
- registration form
- admin panel
- Excel export
- automatic database table creation
- Docker healthchecks

## 1. Requirement

Install Docker Desktop.

Check:

```bash
docker --version
docker compose version
```

## 2. Start immediately

Windows: double-click:

```text
start.bat
```

or run:

```bash
docker compose up -d --build
```

## 3. Open

Website:

```text
http://localhost:8000
```

Admin:

```text
http://localhost:8000/admin
```

Admin password is also stored in:

```text
ADMIN_LOGIN.txt
```

Current generated admin password:

```text
DusonAdmin
```

## 4. Excel

Open `/admin` and click:

```text
Download Excel
```

## 5. Check containers

```bash
docker compose ps
```

Logs:

```bash
docker compose logs -f web db
```

## 6. Stop

```bash
docker compose down
```

Your registrations remain in the PostgreSQL Docker volume.

## 7. Restart

```bash
docker compose up -d
```

## 8. Delete database completely

WARNING: this deletes all registrations.

```bash
docker compose down -v
```

## 9. Production

Before putting the project on `invitation.duson.am`, change in `.env`:

```env
SECRET_KEY=...
ADMIN_PASSWORD=...
POSTGRES_PASSWORD=...
```

For the domain, point:

```text
invitation.duson.am
```

to the server IP and proxy Nginx to:

```text
127.0.0.1:8000
```

The provided file is:

```text
deployment/nginx.conf
```

Then enable HTTPS using Certbot or Cloudflare.

## PostgreSQL connection inside Docker

Host:

```text
db
```

Port:

```text
5432
```

Database:

```text
duson_event
```

User:

```text
duson_user
```

The password is stored in `.env`.

Do not expose PostgreSQL port 5432 publicly. The database is only available to the Docker network.
