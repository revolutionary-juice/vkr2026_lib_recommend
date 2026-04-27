# Next Chat Notes

## What This Project Is

This is a library recommender system for students, teachers, and researchers.

Stack:
- Backend: Python + FastAPI + SQLAlchemy
- Frontend: React + TypeScript + Vite
- DB models: users, documents, interactions, ratings, search history

Main user features already present:
- registration and login
- catalog and document pages
- favorites
- ratings
- search history
- profile page
- recommendations

## Recent Changes Made

1. Profile page navigation to documents:
- In the profile, viewed / favorited / rated document cards now navigate to `/documents/:id`.

2. Admin panel added:
- Admin login intended as:
  - username: `admin`
  - password: `admin`
- Admin page route:
  - `/admin`
- Admin backend route prefix:
  - `/admin`

Admin functionality currently added:
- document CRUD
- CSV import
- document filtering
- user list / role change / block / delete
- interaction, rating, search history review and delete
- analytics overview
- recommendation diagnostics
- export CSV
- JSON backup endpoint
- duplicate cleanup tools
- runtime error/request logging in memory

## Important Files

Backend:
- `app/main.py`
- `app/api/admin.py`
- `app/api/auth.py`
- `app/api/users.py`
- `app/api/documents.py`
- `app/api/recommendations.py`
- `app/core/bootstrap.py`
- `app/core/admin_auth.py`
- `app/core/runtime_logs.py`
- `app/models/user.py`

Frontend:
- `frontend/src/App.tsx`
- `frontend/src/pages/AdminPage.tsx`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/utils/auth.ts`
- `frontend/src/api/admin.ts`
- `frontend/src/api/client.ts`
- `frontend/src/components/Layout.tsx`
- `frontend/src/index.css`

## Known Risks / Things That May Work Wrong

1. Admin authentication is weak.
- There is no real token/session auth.
- Admin access is effectively based on frontend state plus `X-Admin-User-Id`.
- This is not secure for production.

2. Password handling is insecure.
- Passwords are compared as plain strings.
- No hashing.

3. `User.is_blocked` was added as `Integer`, not `Boolean`.
- Works, but should be normalized later.

4. Auto-bootstrap of admin modifies/creates:
- username `admin`
- email `admin@example.com`
- password `admin`
- role `admin`

5. Runtime logs are in memory only.
- They reset when backend restarts.

6. Backup is JSON export, not a true DB dump.

7. Admin page is large and monolithic.
- `frontend/src/pages/AdminPage.tsx` should be split into smaller components.

8. Some old UI text encoding in the project is broken.
- There are mojibake Russian strings in several older files.
- Existing pages may still show broken text in some places.

9. Backend DB config may be environment-specific.
- `app/core/database.py` uses a PostgreSQL connection string.
- Earlier there was also a local `vkr.db` file in the repo root, so DB setup may be inconsistent depending on environment.

10. Some admin operations are expensive.
- Recommendation diagnostics and log checks can query a lot and may be slow on large data.

## Blank Page Bug That Was Fixed

There was a frontend blank screen after admin changes.

Cause:
- recursive bug in `frontend/src/utils/auth.ts`
- `getCurrentUser()` and `getCurrentUserId()` called each other

Fix:
- removed recursive dependency
- build passed after fix

If blank screen happens again:
- check browser console first
- clear local storage keys:
  - `currentUser`
  - `currentUserId`

## What Should Be Improved Next

Priority improvements:

1. Replace fake auth with real auth:
- JWT or server sessions
- proper admin authorization on backend

2. Hash passwords:
- use `passlib` / `bcrypt`

3. Move admin forms and tables into components:
- documents section
- users section
- interactions section
- analytics section
- exports section

4. Add backend pagination for admin lists:
- documents
- users
- interactions
- ratings
- search history

5. Add better validation and safer delete/merge flows:
- confirm destructive actions
- prevent invalid merges
- guard deleting heavily linked documents/users

6. Improve backup/export:
- real DB backup option
- export more entities

7. Persist logs:
- file logging
- structured error logging

8. Clean encoding issues:
- normalize Russian UI strings to UTF-8

9. Add tests:
- auth tests
- admin endpoint tests
- recommendation diagnostics tests
- profile navigation tests

10. Review admin backend performance:
- avoid repeated queries inside loops
- aggregate in SQL where possible

## If Next Chat Starts With “Project is broken”

First things to check:

1. Frontend:
- `frontend/src/utils/auth.ts`
- browser console
- `localStorage` values for `currentUser` and `currentUserId`

2. Backend:
- whether FastAPI starts successfully
- whether `/auth/login` works
- whether `/admin/*` routes load
- whether admin bootstrap runs without DB schema issues

3. DB:
- confirm which DB is actually being used
- check whether `users` table has `is_blocked`
- confirm admin user exists with role `admin`

## Suggested Next Prompt

If resuming later, a good prompt is:

"Прочитай `NEXT_CHAT_NOTES.md`, проверь текущее состояние админки и продолжи улучшения с безопасной авторизации и разбиения AdminPage на компоненты."
