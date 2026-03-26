# Bug Fixes — HBnB Part 3
 
Four bugs were identified during testing and corrected.
 
---
 
## Bug 1 — Circular import on startup
 
**File:** `app/__init__.py`
 
**Description:** The application crashed on startup with `ImportError: cannot import name 'db' from partially initialized module 'app'`.
 
**Cause:** The API namespaces were imported at module level, before `db`, `bcrypt` and `jwt` were instantiated. Python had not finished initializing `app` when `repository.py` tried to import `db` from it.
 
**Fix:** Moved the namespace import inside `create_app()`, after the extensions are initialized.
 
```python
# Before
from app.api.v1 import namespaces as v1_namespaces  # ← at module level, too early
 
bcrypt = Bcrypt()
jwt = JWTManager()
db = SQLAlchemy()
 
def create_app(config_class):
    ...
 
# After
bcrypt = Bcrypt()
jwt = JWTManager()
db = SQLAlchemy()
 
def create_app(config_class):
    ...
    from app.api.v1 import namespaces as v1_namespaces  # ← inside create_app, db already defined
```
 
---
 
## Bug 2 — `GET /api/v1/places/<id>` crashed with 500
 
**File:** `app/services/facade.py` → `get_place()`
 
**Description:** Any request to `GET /api/v1/places/<id>` returned a 500 Internal Server Error.
 
**Cause:** `get_place()` returned amenities as a list of dicts `{"id": ..., "name": ...}`, but the Flask-RESTX response model declared `amenities` as `fields.List(fields.String)`. The marshaller tried to iterate over each dict as if it were a string, causing a `TypeError`.
 
**Fix:** Changed `get_place()` to return amenity IDs only, matching the declared response model.
 
```python
# Before
"amenities": [{"id": a.id, "name": a.name} for a in place.amenities]
 
# After
"amenities": [amenity.id for amenity in place.amenities]
```
 
---
 
## Bug 3 — `PUT /api/v1/places/<id>` returned 400 instead of 404 for nonexistent places
 
**File:** `app/api/v1/places.py` → `PlaceResource.put()`
 
**Description:** Sending a PUT request on a nonexistent place ID returned 400 Bad Request instead of 404 Not Found.
 
**Cause:** `facade.get_place()` raises a `ValueError` when the place does not exist. This exception was caught by the same `except ValueError` block used to handle validation errors, converting it into a 400 response before the `api.abort(404)` could be reached.
 
**Fix:** Separated the "fetch" block from the "validate and update" block, each with its own exception handler.
 
```python
# Before — one try/except swallowing both not-found and validation errors
try:
    place = facade.get_place(place_id)  # raises ValueError if not found
    ...
    result = facade.update_place(place_id, api.payload)
    return result, 200
except ValueError as e:
    api.abort(400, str(e))  # ← caught the not-found ValueError too
 
# After — two separate blocks
try:
    place = facade.get_place(place_id)
except ValueError:
    api.abort(404, "Place not found")  # ← not found handled first
 
try:
    result = facade.update_place(place_id, api.payload)
    return result, 200
except ValueError as e:
    api.abort(400, str(e))  # ← only validation errors reach here
```
 
---
 
## Bug 4 — `PUT /api/v1/reviews/<id>` returned 400 instead of 404 for nonexistent reviews
 
**File:** `app/api/v1/reviews.py` → `ReviewResource.put()`
 
**Description:** Sending a PUT request on a nonexistent review ID returned 400 Bad Request instead of 404 Not Found.
 
**Cause:** Same root cause as Bug 3 — `facade.get_review_by_id()` raises a `ValueError` when the review does not exist, which was caught by the `except (ValueError, TypeError)` validation block, returning 400 instead of 404.
 
**Fix:** Same approach as Bug 3 — separated the fetch and the update into two distinct try/except blocks. The `DELETE` method in the same file had the same issue and was fixed at the same time.
 
```python
# Before
try:
    review = facade.get_review_by_id(review_id)  # raises ValueError if not found
    ...
    return updated_review, 200
except (ValueError, TypeError) as e:
    api.abort(400, str(e))  # ← caught the not-found ValueError too
 
# After
try:
    review = facade.get_review_by_id(review_id)
except ValueError:
    api.abort(404, "Review not found")  # ← not found handled first
 
try:
    updated_review = facade.update_review(review_id, api.payload)
    return updated_review, 200
except (ValueError, TypeError) as e:
    api.abort(400, str(e))  # ← only validation errors reach here
```