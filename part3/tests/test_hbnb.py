import unittest
import time
from app import create_app
from app import db as _db
 
 
class TestConfig:
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
 
 
_app = create_app(TestConfig)
with _app.app_context():
    _db.create_all()
 
_client = _app.test_client()
_state = {}
 
 
def _post(url, json=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return _client.post(url, json=json, headers=headers)
 
 
def _put(url, json=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return _client.put(url, json=json, headers=headers)
 
 
def _get(url):
    return _client.get(url)
 
 
def _delete(url, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return _client.delete(url, headers=headers)
 
 
def _setup():
    from app import db
    from app.models.user import User
 
    with _app.app_context():
        admin = User(
            first_name="Admin", last_name="HBnB",
            email="admin@hbnb.io", password="admin1234", is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
 
    r = _post("/api/v1/auth/login", json={"email": "admin@hbnb.io", "password": "admin1234"})
    assert r.status_code == 200
    _state["admin_token"] = r.json["access_token"]
 
    r = _post("/api/v1/users/", json={
        "first_name": "John", "last_name": "Doe",
        "email": "john@example.com", "password": "password123"
    }, token=_state["admin_token"])
    assert r.status_code == 201
    r = _post("/api/v1/auth/login", json={"email": "john@example.com", "password": "password123"})
    _state["user_token"] = r.json["access_token"]
 
    r = _post("/api/v1/users/", json={
        "first_name": "Jane", "last_name": "Doe",
        "email": "jane@example.com", "password": "password456"
    }, token=_state["admin_token"])
    assert r.status_code == 201
    r = _post("/api/v1/auth/login", json={"email": "jane@example.com", "password": "password456"})
    _state["user2_token"] = r.json["access_token"]
 
    r = _post("/api/v1/amenities/", json={"name": "WiFi"}, token=_state["admin_token"])
    assert r.status_code == 201
    _state["amenity_id"] = r.json["id"]
 
    r = _post("/api/v1/places/", json={
        "title": "Cozy Studio", "description": "Nice place",
        "price": 80.0, "latitude": 48.8566, "longitude": 2.3522,
        "amenities": [_state["amenity_id"]]
    }, token=_state["user_token"])
    assert r.status_code == 201
    _state["place_id"] = r.json["id"]
 
    r = _post("/api/v1/reviews/", json={
        "text": "Great place!", "rating": 5, "place_id": _state["place_id"]
    }, token=_state["user2_token"])
    assert r.status_code == 201
    _state["review_id"] = r.json["id"]
 
 
_setup()
 
 
# ---------------------------------------------------------------------------
# Task 1 — Password hashing
# ---------------------------------------------------------------------------
 
class TestPasswordHashing(unittest.TestCase):
 
    def test_01_password_not_in_create_response(self):
        """POST /users/ must not return the password field."""
        r = _post("/api/v1/users/", json={
            "first_name": "Test", "last_name": "User",
            "email": "nopwd@example.com", "password": "secret"
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 201)
        self.assertNotIn("password", r.json)
 
    def test_02_password_not_in_get_response(self):
        """GET /users/<id> must not return the password field."""
        r = _post("/api/v1/users/", json={
            "first_name": "Test", "last_name": "Hidden",
            "email": "hidden@example.com", "password": "secret"
        }, token=_state["admin_token"])
        user_id = r.json["id"]
        r = _get(f"/api/v1/users/{user_id}")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("password", r.json)
 
    def test_03_password_is_hashed_in_db(self):
        """Password stored in DB must be a bcrypt hash, not plaintext."""
        from app.models.user import User
        with _app.app_context():
            user = User.query.filter_by(email="john@example.com").first()
            self.assertIsNotNone(user)
            self.assertNotEqual(user.password, "password123")
            self.assertTrue(user.password.startswith("$2b$"))
 
    def test_04_verify_password_correct(self):
        """verify_password must return True for the correct password."""
        from app.models.user import User
        with _app.app_context():
            user = User.query.filter_by(email="john@example.com").first()
            self.assertTrue(user.verify_password("password123"))
 
    def test_05_verify_password_wrong(self):
        """verify_password must return False for a wrong password."""
        from app.models.user import User
        with _app.app_context():
            user = User.query.filter_by(email="john@example.com").first()
            self.assertFalse(user.verify_password("wrongpassword"))
 
 
# ---------------------------------------------------------------------------
# Task 2 — JWT Authentication
# ---------------------------------------------------------------------------
 
class TestJWT(unittest.TestCase):
 
    def test_01_login_valid_credentials(self):
        """Valid credentials must return a JWT access token."""
        r = _post("/api/v1/auth/login", json={"email": "admin@hbnb.io", "password": "admin1234"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("access_token", r.json)
 
    def test_02_login_wrong_password(self):
        """Wrong password must return 401."""
        r = _post("/api/v1/auth/login", json={"email": "admin@hbnb.io", "password": "wrong"})
        self.assertEqual(r.status_code, 401)
 
    def test_03_login_unknown_email(self):
        """Unknown email must return 401."""
        r = _post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "x"})
        self.assertEqual(r.status_code, 401)
 
    def test_04_protected_endpoint_no_token(self):
        """Creating a place without token must return 401."""
        r = _post("/api/v1/places/", json={"title": "No auth", "price": 10.0, "latitude": 0.0, "longitude": 0.0})
        self.assertEqual(r.status_code, 401)
 
    def test_05_protected_endpoint_invalid_token(self):
        """Creating a place with a fake token must return 401 or 422."""
        r = _post("/api/v1/places/", json={"title": "Bad", "price": 10.0, "latitude": 0.0, "longitude": 0.0},
                  token="faketoken")
        self.assertIn(r.status_code, (401, 422))
 
 
# ---------------------------------------------------------------------------
# Task 3 — Authenticated user endpoints
# ---------------------------------------------------------------------------
 
class TestAuthenticatedEndpoints(unittest.TestCase):
 
    def test_01_create_place_authenticated(self):
        """Authenticated user can create a place."""
        r = _post("/api/v1/places/", json={
            "title": "Another Place", "description": "Test",
            "price": 50.0, "latitude": 45.0, "longitude": 3.0
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 201)
 
    def test_02_update_place_as_owner(self):
        """Owner can update their place."""
        r = _put(f"/api/v1/places/{_state['place_id']}", json={"title": "Updated Studio"},
                 token=_state["user_token"])
        self.assertEqual(r.status_code, 200)
 
    def test_03_update_place_as_non_owner(self):
        """Non-owner cannot update a place — must return 403."""
        r = _put(f"/api/v1/places/{_state['place_id']}", json={"title": "Hacked"},
                 token=_state["user2_token"])
        self.assertEqual(r.status_code, 403)
 
    def test_04_get_places_public(self):
        """GET /places/ is accessible without token."""
        self.assertEqual(_get("/api/v1/places/").status_code, 200)
 
    def test_05_get_place_detail_public(self):
        """GET /places/<id> is accessible without token."""
        self.assertEqual(_get(f"/api/v1/places/{_state['place_id']}").status_code, 200)
 
    def test_06_create_review_own_place(self):
        """Owner cannot review their own place — must return 400."""
        r = _post("/api/v1/reviews/", json={
            "text": "My own place", "rating": 5, "place_id": _state["place_id"]
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_07_create_review_duplicate(self):
        """User cannot review the same place twice — must return 400."""
        r = _post("/api/v1/reviews/", json={
            "text": "Again!", "rating": 3, "place_id": _state["place_id"]
        }, token=_state["user2_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_08_update_review_as_author(self):
        """Author can update their review."""
        r = _put(f"/api/v1/reviews/{_state['review_id']}", json={"text": "Updated!", "rating": 3},
                 token=_state["user2_token"])
        self.assertEqual(r.status_code, 200)
 
    def test_09_update_review_as_non_author(self):
        """Non-author cannot update a review — must return 403."""
        r = _put(f"/api/v1/reviews/{_state['review_id']}", json={"text": "Hacked", "rating": 1},
                 token=_state["user_token"])
        self.assertEqual(r.status_code, 403)
 
    def test_10_delete_review_as_non_author(self):
        """Non-author cannot delete a review — must return 403."""
        r = _delete(f"/api/v1/reviews/{_state['review_id']}", token=_state["user_token"])
        self.assertEqual(r.status_code, 403)
 
    def test_11_delete_review_as_author(self):
        """Author can delete their own review."""
        r = _delete(f"/api/v1/reviews/{_state['review_id']}", token=_state["user2_token"])
        self.assertEqual(r.status_code, 200)
 
    def test_12_update_own_user(self):
        """User can update their own first/last name."""
        from app.models.user import User
        with _app.app_context():
            user_id = User.query.filter_by(email="john@example.com").first().id
        r = _put(f"/api/v1/users/{user_id}", json={"first_name": "Johnny"}, token=_state["user_token"])
        self.assertEqual(r.status_code, 200)
 
    def test_13_update_user_email_forbidden(self):
        """Regular user cannot change their email — must return 400."""
        from app.models.user import User
        with _app.app_context():
            user_id = User.query.filter_by(email="john@example.com").first().id
        r = _put(f"/api/v1/users/{user_id}", json={"email": "new@example.com"}, token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_14_update_user_password_forbidden(self):
        """Regular user cannot change their password — must return 400."""
        from app.models.user import User
        with _app.app_context():
            user_id = User.query.filter_by(email="john@example.com").first().id
        r = _put(f"/api/v1/users/{user_id}", json={"password": "newpass"}, token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_15_update_other_user_forbidden(self):
        """User cannot modify another user's data — must return 403."""
        from app.models.user import User
        with _app.app_context():
            other = User.query.filter_by(email="jane@example.com").first() or User.query.filter_by(email="jane_updated@example.com").first()
            other_id = other.id
        r = _put(f"/api/v1/users/{other_id}", json={"first_name": "Hacked"}, token=_state["user_token"])
        self.assertEqual(r.status_code, 403)
 
 
# ---------------------------------------------------------------------------
# Task 4 — Admin endpoints
# ---------------------------------------------------------------------------
 
class TestAdminEndpoints(unittest.TestCase):
 
    def test_01_create_user_as_admin(self):
        """Admin can create a new user."""
        r = _post("/api/v1/users/", json={
            "first_name": "New", "last_name": "User",
            "email": "newuser@example.com", "password": "pass123"
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 201)
 
    def test_02_create_user_as_regular_user(self):
        """Regular user cannot create a user — must return 403."""
        r = _post("/api/v1/users/", json={
            "first_name": "X", "last_name": "Y",
            "email": "xy@example.com", "password": "pass"
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 403)
 
    def test_03_create_user_duplicate_email(self):
        """Admin cannot create two users with the same email — must return 400."""
        r = _post("/api/v1/users/", json={
            "first_name": "Dup", "last_name": "User",
            "email": "john@example.com", "password": "pass"
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_04_create_amenity_as_admin(self):
        """Admin can create an amenity."""
        r = _post("/api/v1/amenities/", json={"name": "Pool"}, token=_state["admin_token"])
        self.assertEqual(r.status_code, 201)
 
    def test_05_create_amenity_as_regular_user(self):
        """Regular user cannot create an amenity — must return 403."""
        r = _post("/api/v1/amenities/", json={"name": "Jacuzzi"}, token=_state["user_token"])
        self.assertEqual(r.status_code, 403)
 
    def test_06_update_amenity_as_admin(self):
        """Admin can update an amenity."""
        r = _put(f"/api/v1/amenities/{_state['amenity_id']}", json={"name": "Fast WiFi"},
                 token=_state["admin_token"])
        self.assertEqual(r.status_code, 200)
 
    def test_07_update_amenity_as_regular_user(self):
        """Regular user cannot update an amenity — must return 403."""
        r = _put(f"/api/v1/amenities/{_state['amenity_id']}", json={"name": "Hacked"},
                 token=_state["user_token"])
        self.assertEqual(r.status_code, 403)
 
    def test_08_admin_can_update_any_place(self):
        """Admin can update any place, bypassing ownership check."""
        r = _put(f"/api/v1/places/{_state['place_id']}", json={"title": "Admin Updated"},
                 token=_state["admin_token"])
        self.assertEqual(r.status_code, 200)
 
    def test_09_admin_update_user_email(self):
        """Admin can change any user's email."""
        from app.models.user import User
        with _app.app_context():
            user_id = User.query.filter_by(email="jane@example.com").first().id
        r = _put(f"/api/v1/users/{user_id}", json={"email": "jane_updated@example.com"},
                 token=_state["admin_token"])
        self.assertEqual(r.status_code, 200)
 
    def test_10_admin_update_user_duplicate_email(self):
        """Admin cannot set an email already used by another user — must return 400."""
        from app.models.user import User
        with _app.app_context():
            user_id = User.query.filter_by(email="jane_updated@example.com").first().id
        r = _put(f"/api/v1/users/{user_id}", json={"email": "john@example.com"},
                 token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
 
# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
 
class TestValidation(unittest.TestCase):
 
    def test_01_create_place_invalid_price(self):
        """Negative price must return 400."""
        r = _post("/api/v1/places/", json={"title": "Bad", "price": -10.0, "latitude": 0.0, "longitude": 0.0},
                  token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_02_create_place_invalid_latitude(self):
        """Latitude out of range must return 400."""
        r = _post("/api/v1/places/", json={"title": "Bad", "price": 10.0, "latitude": 999.0, "longitude": 0.0},
                  token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_03_create_review_invalid_rating(self):
        """Rating outside 1-5 must return 400."""
        r = _post("/api/v1/reviews/", json={
            "text": "Bad", "rating": 10, "place_id": _state["place_id"]
        }, token=_state["user2_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_04_create_user_invalid_email(self):
        """Invalid email format must return 400."""
        r = _post("/api/v1/users/", json={
            "first_name": "Bad", "last_name": "Email",
            "email": "not-an-email", "password": "pass123"
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_05_get_nonexistent_place(self):
        """GET on a non-existent place must return 404."""
        self.assertEqual(_get("/api/v1/places/00000000-0000-0000-0000-000000000000").status_code, 404)
 
    def test_06_get_nonexistent_user(self):
        """GET on a non-existent user must return 404."""
        self.assertEqual(_get("/api/v1/users/00000000-0000-0000-0000-000000000000").status_code, 404)
 
 
# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
 
class TestPersistence(unittest.TestCase):
 
    def test_01_user_persists_in_db(self):
        """User created via API must be retrievable directly from DB."""
        from app.models.user import User
        with _app.app_context():
            user = User.query.filter_by(email="john@example.com").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.first_name, "Johnny")
 
    def test_02_place_persists_in_db(self):
        """Place created via API must be retrievable directly from DB."""
        from app.models.place import Place
        with _app.app_context():
            self.assertIsNotNone(Place.query.get(_state["place_id"]))
 
    def test_03_amenity_relationship(self):
        """Place must have its amenity linked via the many-to-many relationship."""
        from app.models.place import Place
        with _app.app_context():
            place = Place.query.get(_state["place_id"])
            self.assertGreater(len(place.amenities), 0)
 
 
# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
 
class TestEdgeCases(unittest.TestCase):
 
    def test_01_create_place_with_nonexistent_amenity(self):
        """Creating a place with a fake amenity ID must return 400."""
        r = _post("/api/v1/places/", json={
            "title": "Bad amenity", "price": 50.0, "latitude": 10.0, "longitude": 10.0,
            "amenities": ["00000000-0000-0000-0000-000000000000"]
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_02_create_review_on_nonexistent_place(self):
        """Creating a review on a fake place ID must return 400."""
        r = _post("/api/v1/reviews/", json={
            "text": "Ghost", "rating": 3,
            "place_id": "00000000-0000-0000-0000-000000000000"
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_03_create_review_rating_too_low(self):
        """Rating of 0 must return 400."""
        r = _post("/api/v1/reviews/", json={
            "text": "Too low", "rating": 0, "place_id": _state["place_id"]
        }, token=_state["user2_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_04_create_place_missing_title(self):
        """Missing required title field must return 400."""
        r = _post("/api/v1/places/", json={"price": 50.0, "latitude": 10.0, "longitude": 10.0},
                  token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_05_create_place_missing_price(self):
        """Missing required price field must return 400."""
        r = _post("/api/v1/places/", json={"title": "No price", "latitude": 10.0, "longitude": 10.0},
                  token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_06_create_user_missing_password(self):
        """Missing password field must return 400."""
        r = _post("/api/v1/users/", json={
            "first_name": "No", "last_name": "Password", "email": "nopwd2@example.com"
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_07_get_all_reviews_public(self):
        """GET /reviews/ is accessible without token."""
        r = _get("/api/v1/reviews/")
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.json, list)
 
    def test_08_get_all_amenities_public(self):
        """GET /amenities/ is accessible without token."""
        r = _get("/api/v1/amenities/")
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.json, list)
 
    def test_09_get_review_by_id_public(self):
        """GET /reviews/<id> is accessible without token."""
        r_create = _post("/api/v1/reviews/", json={
            "text": "For get test", "rating": 4, "place_id": _state["place_id"]
        }, token=_state["user2_token"])
        self.assertEqual(r_create.status_code, 201)
        review_id = r_create.json["id"]
        r = _get(f"/api/v1/reviews/{review_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["id"], review_id)
        _delete(f"/api/v1/reviews/{review_id}", token=_state["user2_token"])
 
    def test_10_get_nonexistent_review(self):
        """GET on a non-existent review must return 404."""
        self.assertEqual(_get("/api/v1/reviews/00000000-0000-0000-0000-000000000000").status_code, 404)
 
    def test_11_get_nonexistent_amenity(self):
        """GET on a non-existent amenity must return 404."""
        self.assertEqual(_get("/api/v1/amenities/00000000-0000-0000-0000-000000000000").status_code, 404)
 
    def test_12_update_place_owner_id_forbidden(self):
        """Trying to change owner_id of a place must return 400."""
        r = _put(f"/api/v1/places/{_state['place_id']}",
                 json={"owner_id": "00000000-0000-0000-0000-000000000000"},
                 token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_13_get_user_by_email_query(self):
        """GET /users/?email=... must return the matching user."""
        r = _get("/api/v1/users/?email=john@example.com")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json), 1)
        self.assertEqual(r.json[0]["email"], "john@example.com")
 
    def test_14_get_user_by_email_not_found(self):
        """GET /users/?email=unknown must return 404."""
        self.assertEqual(_get("/api/v1/users/?email=nobody@nowhere.com").status_code, 404)
 
    def test_15_place_response_contains_owner_id(self):
        """GET /places/<id> response must include owner_id."""
        r = _get(f"/api/v1/places/{_state['place_id']}")
        self.assertEqual(r.status_code, 200)
        self.assertIn("owner_id", r.json)
        self.assertIsNotNone(r.json["owner_id"])
 
    def test_16_admin_delete_review(self):
        """Admin can delete any review regardless of authorship."""
        r_create = _post("/api/v1/reviews/", json={
            "text": "Admin will delete this", "rating": 2, "place_id": _state["place_id"]
        }, token=_state["user2_token"])
        self.assertEqual(r_create.status_code, 201)
        r = _delete(f"/api/v1/reviews/{r_create.json['id']}", token=_state["admin_token"])
        self.assertEqual(r.status_code, 200)
 
 
# ---------------------------------------------------------------------------
# Model validation boundaries
# ---------------------------------------------------------------------------
 
class TestModelValidation(unittest.TestCase):
 
    def test_01_first_name_too_long(self):
        r = _post("/api/v1/users/", json={
            "first_name": "A" * 51, "last_name": "Doe",
            "email": "toolong_fn@example.com", "password": "pass123"
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_02_last_name_too_long(self):
        r = _post("/api/v1/users/", json={
            "first_name": "John", "last_name": "B" * 51,
            "email": "toolong_ln@example.com", "password": "pass123"
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_03_first_name_whitespace_only(self):
        r = _post("/api/v1/users/", json={
            "first_name": "   ", "last_name": "Doe",
            "email": "ws_fn@example.com", "password": "pass123"
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_04_place_title_too_long(self):
        r = _post("/api/v1/places/", json={
            "title": "T" * 101, "price": 50.0, "latitude": 10.0, "longitude": 10.0
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_05_place_title_whitespace_only(self):
        r = _post("/api/v1/places/", json={
            "title": "   ", "price": 50.0, "latitude": 10.0, "longitude": 10.0
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_06_place_price_zero(self):
        r = _post("/api/v1/places/", json={
            "title": "Zero price", "price": 0, "latitude": 10.0, "longitude": 10.0
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_07_place_latitude_boundary_valid(self):
        for lat in [90.0, -90.0]:
            r = _post("/api/v1/places/", json={
                "title": f"Lat {lat}", "price": 10.0, "latitude": lat, "longitude": 0.0
            }, token=_state["user_token"])
            self.assertEqual(r.status_code, 201, f"lat={lat} should be valid")
 
    def test_08_place_latitude_out_of_boundary(self):
        for lat in [90.1, -90.1]:
            r = _post("/api/v1/places/", json={
                "title": f"Lat {lat}", "price": 10.0, "latitude": lat, "longitude": 0.0
            }, token=_state["user_token"])
            self.assertEqual(r.status_code, 400, f"lat={lat} should be invalid")
 
    def test_09_place_longitude_boundary_valid(self):
        for lng in [180.0, -180.0]:
            r = _post("/api/v1/places/", json={
                "title": f"Lng {lng}", "price": 10.0, "latitude": 0.0, "longitude": lng
            }, token=_state["user_token"])
            self.assertEqual(r.status_code, 201, f"lng={lng} should be valid")
 
    def test_10_place_longitude_out_of_boundary(self):
        for lng in [180.1, -180.1]:
            r = _post("/api/v1/places/", json={
                "title": f"Lng {lng}", "price": 10.0, "latitude": 0.0, "longitude": lng
            }, token=_state["user_token"])
            self.assertEqual(r.status_code, 400, f"lng={lng} should be invalid")
 
    def test_11_place_lat_lng_zero_valid(self):
        r = _post("/api/v1/places/", json={
            "title": "Null island", "price": 10.0, "latitude": 0.0, "longitude": 0.0
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 201)
 
    def test_12_amenity_name_too_long(self):
        r = _post("/api/v1/amenities/", json={"name": "A" * 51}, token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_13_amenity_name_whitespace_only(self):
        r = _post("/api/v1/amenities/", json={"name": "   "}, token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_14_review_text_empty(self):
        r = _post("/api/v1/reviews/", json={
            "text": "   ", "rating": 3, "place_id": _state["place_id"]
        }, token=_state["user2_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_15_review_rating_above_max(self):
        r = _post("/api/v1/reviews/", json={
            "text": "Too high", "rating": 6, "place_id": _state["place_id"]
        }, token=_state["user2_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_16_place_description_optional(self):
        r = _post("/api/v1/places/", json={
            "title": "No description", "price": 30.0, "latitude": 5.0, "longitude": 5.0
        }, token=_state["user_token"])
        self.assertEqual(r.status_code, 201)
 
 
# ---------------------------------------------------------------------------
# Response structure
# ---------------------------------------------------------------------------
 
class TestResponseStructure(unittest.TestCase):
 
    def test_01_place_list_fields(self):
        """GET /places/ must return id, title, latitude, longitude, owner_id."""
        r = _get("/api/v1/places/")
        self.assertEqual(r.status_code, 200)
        place = next((p for p in r.json if p["id"] == _state["place_id"]), None)
        self.assertIsNotNone(place)
        for field in ["id", "title", "latitude", "longitude", "owner_id"]:
            self.assertIn(field, place)
 
    def test_02_place_detail_fields(self):
        """GET /places/<id> must return full fields including amenities."""
        r = _get(f"/api/v1/places/{_state['place_id']}")
        self.assertEqual(r.status_code, 200)
        for field in ["id", "title", "description", "price", "latitude", "longitude", "owner_id", "amenities"]:
            self.assertIn(field, r.json)
 
    def test_03_user_response_fields(self):
        """POST /users/ response must contain expected fields, no password."""
        r = _post("/api/v1/users/", json={
            "first_name": "Field", "last_name": "Check",
            "email": "fieldcheck@example.com", "password": "pass123"
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 201)
        for field in ["id", "first_name", "last_name", "email", "is_admin", "created_at", "updated_at"]:
            self.assertIn(field, r.json)
        self.assertNotIn("password", r.json)
 
    def test_04_review_response_fields(self):
        """POST /reviews/ response must contain expected fields."""
        r = _post("/api/v1/reviews/", json={
            "text": "Field check", "rating": 4, "place_id": _state["place_id"]
        }, token=_state["user2_token"])
        self.assertEqual(r.status_code, 201)
        for field in ["id", "text", "rating", "user_id", "place_id"]:
            self.assertIn(field, r.json)
        _delete(f"/api/v1/reviews/{r.json['id']}", token=_state["user2_token"])
 
    def test_05_login_response_fields(self):
        """POST /auth/login response must contain access_token."""
        r = _post("/api/v1/auth/login", json={"email": "admin@hbnb.io", "password": "admin1234"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("access_token", r.json)
        self.assertIsInstance(r.json["access_token"], str)
        self.assertGreater(len(r.json["access_token"]), 20)
 
    def test_06_updated_at_changes_after_update(self):
        """updated_at must change after a PUT update."""
        from app.models.user import User
        with _app.app_context():
            user = User.query.filter_by(email="john@example.com").first()
            user_id = user.id
            before = user.updated_at
        time.sleep(0.1)
        _put(f"/api/v1/users/{user_id}", json={"first_name": "Updated"}, token=_state["user_token"])
        with _app.app_context():
            user = User.query.filter_by(email="john@example.com").first()
            self.assertGreater(user.updated_at, before)
 
    def test_07_amenities_cleared_on_update(self):
        """Updating place with empty amenities list must clear all amenities."""
        r = _put(f"/api/v1/places/{_state['place_id']}", json={"amenities": []},
                 token=_state["user_token"])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["amenities"], [])
 
    def test_08_place_amenities_restored(self):
        """Re-adding an amenity after clearing must work."""
        r = _put(f"/api/v1/places/{_state['place_id']}",
                 json={"amenities": [_state["amenity_id"]]},
                 token=_state["user_token"])
        self.assertEqual(r.status_code, 200)
        self.assertIn(_state["amenity_id"], r.json["amenities"])
 
 
# ---------------------------------------------------------------------------
# Auth edge cases
# ---------------------------------------------------------------------------
 
class TestAuthEdgeCases(unittest.TestCase):
 
    def test_01_create_admin_user_via_admin(self):
        """Admin can create another admin user with is_admin=True."""
        r = _post("/api/v1/users/", json={
            "first_name": "Super", "last_name": "Admin",
            "email": "admin2@example.com", "password": "adminpass", "is_admin": True
        }, token=_state["admin_token"])
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.json["is_admin"])
 
    def test_02_new_admin_can_create_amenity(self):
        """Newly created admin user must be able to create amenities."""
        r = _post("/api/v1/auth/login", json={"email": "admin2@example.com", "password": "adminpass"})
        self.assertEqual(r.status_code, 200)
        r = _post("/api/v1/amenities/", json={"name": "Sauna"}, token=r.json["access_token"])
        self.assertEqual(r.status_code, 201)
 
    def test_03_email_normalized_to_lowercase(self):
        """Login with uppercase email must fail (email stored lowercase)."""
        _post("/api/v1/users/", json={
            "first_name": "Case", "last_name": "Test",
            "email": "casetest@example.com", "password": "pass123"
        }, token=_state["admin_token"])
        r = _post("/api/v1/auth/login", json={"email": "CASETEST@EXAMPLE.COM", "password": "pass123"})
        self.assertEqual(r.status_code, 401)
 
    def test_04_login_missing_email_field(self):
        """Login without email field must return 400."""
        self.assertEqual(_post("/api/v1/auth/login", json={"password": "pass123"}).status_code, 400)
 
    def test_05_login_missing_password_field(self):
        """Login without password field must return 400."""
        self.assertEqual(_post("/api/v1/auth/login", json={"email": "admin@hbnb.io"}).status_code, 400)
 
    def test_06_partial_review_update(self):
        """Updating only the text of a review must preserve the rating."""
        # Create a fresh place owned by admin so user2 can review it
        r_place = _post("/api/v1/places/", json={
            "title": "Partial update test place", "price": 10.0,
            "latitude": 1.0, "longitude": 1.0
        }, token=_state["admin_token"])
        self.assertEqual(r_place.status_code, 201)
        test_place_id = r_place.json["id"]
        r_create = _post("/api/v1/reviews/", json={
            "text": "Original", "rating": 5, "place_id": test_place_id
        }, token=_state["user2_token"])
        self.assertEqual(r_create.status_code, 201)
        review_id = r_create.json["id"]
        r = _put(f"/api/v1/reviews/{review_id}", json={"text": "Updated text"},
                 token=_state["user2_token"])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["text"], "Updated text")
        self.assertEqual(r.json["rating"], 5)
        _delete(f"/api/v1/reviews/{review_id}", token=_state["user2_token"])
        _delete(f"/api/v1/places/{test_place_id}", token=_state["admin_token"]) if hasattr(self, '_') else None
 
    def test_07_update_nonexistent_place(self):
        """PUT on a non-existent place must return 404."""
        r = _put("/api/v1/places/00000000-0000-0000-0000-000000000000",
                 json={"title": "Ghost"}, token=_state["user_token"])
        self.assertEqual(r.status_code, 404)
 
    def test_08_update_nonexistent_review(self):
        """PUT on a non-existent review must return 404."""
        r = _put("/api/v1/reviews/00000000-0000-0000-0000-000000000000",
                 json={"text": "Ghost", "rating": 3}, token=_state["user_token"])
        self.assertEqual(r.status_code, 404)
 
    def test_09_update_nonexistent_user(self):
        """PUT on a non-existent user returns 403 or 404."""
        r = _put("/api/v1/users/00000000-0000-0000-0000-000000000000",
                 json={"first_name": "Ghost"}, token=_state["user_token"])
        self.assertIn(r.status_code, (403, 404))
 
    def test_10_duplicate_amenity_name(self):
        """Creating two amenities with the same name must return 400."""
        _post("/api/v1/amenities/", json={"name": "UniqueName"}, token=_state["admin_token"])
        r = _post("/api/v1/amenities/", json={"name": "UniqueName"}, token=_state["admin_token"])
        self.assertEqual(r.status_code, 400)
 
    def test_11_place_update_partial_fields(self):
        """Updating only price must not affect other fields."""
        title_before = _get(f"/api/v1/places/{_state['place_id']}").json["title"]
        r = _put(f"/api/v1/places/{_state['place_id']}", json={"price": 999.0},
                 token=_state["user_token"])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["price"], 999.0)
        self.assertEqual(r.json["title"], title_before)
 
 
if __name__ == "__main__":
    unittest.main(verbosity=2)