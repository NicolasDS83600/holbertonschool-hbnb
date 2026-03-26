#!/bin/bash
BASE="http://127.0.0.1:5000/api/v1"
PASS=0
FAIL=0
 
check() {
    local description="$1"
    local expected="$2"
    local actual="$3"
    if [ "$actual" -eq "$expected" ] 2>/dev/null; then
        echo "  PASS — $description"
        PASS=$((PASS + 1))
    else
        echo "  FAIL — $description (expected $expected, got $actual)"
        FAIL=$((FAIL + 1))
    fi
}
 
echo ""
echo "================================================"
echo " HBnB cURL Test Suite"
echo "================================================"
 
# ---------------------------------------------------------------------------
# Setup: seed admin user directly via DB before starting
# (requires flask shell or initial_data.sql already applied)
# ---------------------------------------------------------------------------
 
echo ""
echo "[ Task 2 — JWT Authentication ]"
 
# Login with valid credentials
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@hbnb.io", "password": "admin1234"}')
check "Login with valid credentials returns 200" 200 "$STATUS"
 
# Capture admin token
ADMIN_TOKEN=$(curl -s -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@hbnb.io", "password": "admin1234"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
 
# Login with wrong password
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@hbnb.io", "password": "wrongpass"}')
check "Login with wrong password returns 401" 401 "$STATUS"
 
# Login with unknown email
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "nobody@example.com", "password": "whatever"}')
check "Login with unknown email returns 401" 401 "$STATUS"
 
# Access protected endpoint without token
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/places/" \
    -H "Content-Type: application/json" \
    -d '{"title": "No auth", "price": 10, "latitude": 0, "longitude": 0}')
check "POST /places/ without token returns 401" 401 "$STATUS"
 
# ---------------------------------------------------------------------------
echo ""
echo "[ Task 1 — Password hashing ]"
 
# Create a user as admin and check no password in response
RESPONSE=$(curl -s -X POST "$BASE/users/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"first_name": "John", "last_name": "Doe", "email": "john_curl@example.com", "password": "password123"}')
STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(200 if 'id' in d else 400)" 2>/dev/null)
check "POST /users/ returns user object" 200 "$STATUS"
 
HAS_PWD=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(1 if 'password' in d else 0)" 2>/dev/null)
check "POST /users/ response does not contain password field" 0 "$HAS_PWD"
 
USER_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
 
# GET user and check no password
RESPONSE=$(curl -s "$BASE/users/$USER_ID")
HAS_PWD=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(1 if 'password' in d else 0)" 2>/dev/null)
check "GET /users/<id> response does not contain password field" 0 "$HAS_PWD"
 
# Get user token
USER_TOKEN=$(curl -s -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "john_curl@example.com", "password": "password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
 
# Create second user
curl -s -X POST "$BASE/users/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"first_name": "Jane", "last_name": "Doe", "email": "jane_curl@example.com", "password": "password456"}' > /dev/null
 
USER2_TOKEN=$(curl -s -X POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "jane_curl@example.com", "password": "password456"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
 
# ---------------------------------------------------------------------------
echo ""
echo "[ Task 4 — Admin endpoints ]"
 
# Regular user cannot create a user
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/users/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"first_name": "X", "last_name": "Y", "email": "xy_curl@example.com", "password": "pass"}')
check "POST /users/ as regular user returns 403" 403 "$STATUS"
 
# Duplicate email
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/users/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"first_name": "Dup", "last_name": "User", "email": "john_curl@example.com", "password": "pass"}')
check "POST /users/ with duplicate email returns 400" 400 "$STATUS"
 
# Admin creates amenity
AMENITY_RESPONSE=$(curl -s -X POST "$BASE/amenities/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"name": "WiFi_curl"}')
STATUS=$(echo "$AMENITY_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(201 if 'id' in d else 400)" 2>/dev/null)
check "POST /amenities/ as admin returns 201" 201 "$STATUS"
AMENITY_ID=$(echo "$AMENITY_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
 
# Regular user cannot create amenity
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/amenities/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"name": "Jacuzzi_curl"}')
check "POST /amenities/ as regular user returns 403" 403 "$STATUS"
 
# Admin updates amenity
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/amenities/$AMENITY_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"name": "Fast WiFi_curl"}')
check "PUT /amenities/<id> as admin returns 200" 200 "$STATUS"
 
# Regular user cannot update amenity
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/amenities/$AMENITY_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"name": "Hacked"}')
check "PUT /amenities/<id> as regular user returns 403" 403 "$STATUS"
 
# ---------------------------------------------------------------------------
echo ""
echo "[ Task 3 — Authenticated endpoints — Places ]"
 
# Create place as authenticated user
PLACE_RESPONSE=$(curl -s -X POST "$BASE/places/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d "{\"title\": \"Cozy Studio\", \"description\": \"Nice\", \"price\": 80, \"latitude\": 48.85, \"longitude\": 2.35, \"amenities\": [\"$AMENITY_ID\"]}")
STATUS=$(echo "$PLACE_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(201 if 'id' in d else 400)" 2>/dev/null)
check "POST /places/ as authenticated user returns 201" 201 "$STATUS"
PLACE_ID=$(echo "$PLACE_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
 
# GET places is public
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/places/")
check "GET /places/ without token returns 200" 200 "$STATUS"
 
# GET place detail is public
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/places/$PLACE_ID")
check "GET /places/<id> without token returns 200" 200 "$STATUS"
 
# Owner can update place
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/places/$PLACE_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"title": "Updated Studio"}')
check "PUT /places/<id> as owner returns 200" 200 "$STATUS"
 
# Non-owner cannot update place
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/places/$PLACE_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER2_TOKEN" \
    -d '{"title": "Hacked"}')
check "PUT /places/<id> as non-owner returns 403" 403 "$STATUS"
 
# Admin can update any place
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/places/$PLACE_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"title": "Admin Updated"}')
check "PUT /places/<id> as admin returns 200" 200 "$STATUS"
 
# ---------------------------------------------------------------------------
echo ""
echo "[ Task 3 — Authenticated endpoints — Reviews ]"
 
# Owner cannot review their own place
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/reviews/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d "{\"text\": \"My own place\", \"rating\": 5, \"place_id\": \"$PLACE_ID\"}")
check "POST /reviews/ on own place returns 400" 400 "$STATUS"
 
# user2 can review a place they don't own
REVIEW_RESPONSE=$(curl -s -X POST "$BASE/reviews/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER2_TOKEN" \
    -d "{\"text\": \"Great!\", \"rating\": 5, \"place_id\": \"$PLACE_ID\"}")
STATUS=$(echo "$REVIEW_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(201 if 'id' in d else 400)" 2>/dev/null)
check "POST /reviews/ as non-owner returns 201" 201 "$STATUS"
REVIEW_ID=$(echo "$REVIEW_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
 
# Duplicate review
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/reviews/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER2_TOKEN" \
    -d "{\"text\": \"Again\", \"rating\": 3, \"place_id\": \"$PLACE_ID\"}")
check "POST /reviews/ duplicate returns 400" 400 "$STATUS"
 
# Non-author cannot update review
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/reviews/$REVIEW_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"text": "Hacked", "rating": 1}')
check "PUT /reviews/<id> as non-author returns 403" 403 "$STATUS"
 
# Author can update review
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/reviews/$REVIEW_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER2_TOKEN" \
    -d '{"text": "Updated!", "rating": 4}')
check "PUT /reviews/<id> as author returns 200" 200 "$STATUS"
 
# Non-author cannot delete review
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE/reviews/$REVIEW_ID" \
    -H "Authorization: Bearer $USER_TOKEN")
check "DELETE /reviews/<id> as non-author returns 403" 403 "$STATUS"
 
# Author can delete review
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE/reviews/$REVIEW_ID" \
    -H "Authorization: Bearer $USER2_TOKEN")
check "DELETE /reviews/<id> as author returns 200" 200 "$STATUS"
 
# ---------------------------------------------------------------------------
echo ""
echo "[ Task 3 — Authenticated endpoints — Users ]"
 
# User updates own name
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/users/$USER_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"first_name": "Johnny"}')
check "PUT /users/<id> own name returns 200" 200 "$STATUS"
 
# User cannot change own email
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/users/$USER_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"email": "new@example.com"}')
check "PUT /users/<id> own email returns 400" 400 "$STATUS"
 
# User cannot change own password
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/users/$USER_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"password": "newpass"}')
check "PUT /users/<id> own password returns 400" 400 "$STATUS"
 
# User cannot modify another user
USER2_ID=$(curl -s "$BASE/users/?email=jane_curl@example.com" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')" 2>/dev/null)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/users/$USER2_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"first_name": "Hacked"}')
check "PUT /users/<other_id> as regular user returns 403" 403 "$STATUS"
 
# Admin can change email
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE/users/$USER2_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"email": "jane_updated_curl@example.com"}')
check "PUT /users/<id> email as admin returns 200" 200 "$STATUS"
 
# ---------------------------------------------------------------------------
echo ""
echo "[ Validation ]"
 
# Invalid price
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/places/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"title": "Bad", "price": -10, "latitude": 0, "longitude": 0}')
check "POST /places/ with negative price returns 400" 400 "$STATUS"
 
# Invalid latitude
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/places/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -d '{"title": "Bad", "price": 10, "latitude": 999, "longitude": 0}')
check "POST /places/ with invalid latitude returns 400" 400 "$STATUS"
 
# Invalid email format
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/users/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -d '{"first_name": "X", "last_name": "Y", "email": "not-an-email", "password": "pass"}')
check "POST /users/ with invalid email returns 400" 400 "$STATUS"
 
# Non-existent place
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/places/00000000-0000-0000-0000-000000000000")
check "GET /places/<bad_id> returns 404" 404 "$STATUS"
 
# Non-existent user
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/users/00000000-0000-0000-0000-000000000000")
check "GET /users/<bad_id> returns 404" 404 "$STATUS"
 
# ---------------------------------------------------------------------------
echo ""
echo "================================================"
echo " Results: $PASS passed, $FAIL failed"
echo "================================================"
echo ""
 
[ "$FAIL" -eq 0 ] && exit 0 || exit 1