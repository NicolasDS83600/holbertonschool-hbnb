# Tests
 
Two test suites: a unittest suite (no server needed) and a cURL script (server must be running).
 
## Requirements
 
```bash
pip install flask flask-restx Flask-Bcrypt flask-jwt-extended flask-sqlalchemy
```
 
---
 
## unittest — unit & integration tests
 
Runs against an in-memory SQLite database. No server required.
 
```bash
# From the project root (part3/)
python -m unittest tests/test_hbnb.py -v
```
 
95 tests across 9 classes:
- `TestPasswordHashing` — bcrypt hashing, no password in responses
- `TestJWT` — login, invalid credentials, missing/fake token
- `TestAuthenticatedEndpoints` — places, reviews, users with ownership checks
- `TestAdminEndpoints` — admin-only actions, bypass ownership, email uniqueness
- `TestValidation` — required fields, format checks, 404s
- `TestPersistence` — data survives across requests, relationships in DB
- `TestEdgeCases` — nonexistent resources, public endpoints, query params
- `TestModelValidation` — field length limits, boundary values, whitespace
- `TestResponseStructure` — response fields, updated_at changes, partial updates
- `TestAuthEdgeCases` — admin creation, email case, partial update, 404 on PUT
 
---
 
## cURL — end-to-end tests
 
Requires the server to be running and the admin user seeded in the database.
 
**1. Start the server**
```bash
python run.py
```
 
**2. Initialize and seed the database** (first time only)
```bash
python3 -c "
from app import create_app
from config import DevelopmentConfig
from app import db
app = create_app(DevelopmentConfig)
with app.app_context():
    db.create_all()
"
sqlite3 instance/development.db < sql/initial_data.sql
```
 
**3. Make it executable and run it**
```bash
chmod +x tests/test_curl.sh
./tests/test_curl.sh
```
 
Results are printed as `PASS` / `FAIL` with a summary at the end.