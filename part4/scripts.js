document.addEventListener('DOMContentLoaded', () => {

    const API = 'http://127.0.0.1:5000/api/v1';

    // ─── Utilities ────────────────────────────────────────────────────────────

    function getCookie(name) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [key, value] = cookie.trim().split('=');
            if (key === name) return value;
        }
        return null;
    }

    function deleteCookie(name) {
        document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
    }

    function getPlaceIdFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('id');
    }

    function isClientMode() {
        const params = new URLSearchParams(window.location.search);
        return params.get('mode') === 'client';
    }

    function parseJWT(token) {
        try {
            const base64Payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
            return JSON.parse(atob(base64Payload));
        } catch {
            return null;
        }
    }

    function cloneTemplate(templateId) {
        return document.getElementById(templateId).content.cloneNode(true);
    }

    function showToast(message, isError = false) {
        const toast = document.createElement('div');
        toast.className = 'toast' + (isError ? ' toast-error' : '');
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ─── Header: user info + login/logout + mode switch ───────────────────────

    function setupHeader() {
        const token = getCookie('token');
        const loginLink = document.getElementById('login-link');
        const userInfoSpan = document.getElementById('user-info');
        const modeSwitchBtn = document.getElementById('btn-mode-switch');

        if (!token) {
            if (loginLink) {
                loginLink.textContent = 'Login';
                loginLink.href = 'login.html';
                loginLink.style.display = 'inline-block';
            }
            if (userInfoSpan) userInfoSpan.style.display = 'none';
            if (modeSwitchBtn) modeSwitchBtn.style.display = 'none';
            return null;
        }

        const claims = parseJWT(token);
        if (!claims) return null;

        fetch(`${API}/users/${claims.sub}`)
            .then(response => response.ok ? response.json() : null)
            .then(user => {
                if (!user) return;
                const role = user.is_admin ? 'Admin' : 'Client';
                if (userInfoSpan) {
                    userInfoSpan.textContent = `${user.first_name} ${user.last_name} — ${role}`;
                    userInfoSpan.style.display = 'inline-block';
                }
            });

        if (loginLink) {
            loginLink.textContent = 'Logout';
            loginLink.href = '#';
            loginLink.style.display = 'inline-block';
            loginLink.onclick = (clickEvent) => {
                clickEvent.preventDefault();
                deleteCookie('token');
                window.location.href = 'index.html';
            };
        }

        if (modeSwitchBtn && claims.is_admin) {
            modeSwitchBtn.style.display = 'inline-block';
            if (isClientMode()) {
                modeSwitchBtn.textContent = '⚙️ Admin view';
                modeSwitchBtn.href = 'index.html';
            } else {
                modeSwitchBtn.textContent = '👤 Client view';
                modeSwitchBtn.href = 'index.html?mode=client';
            }
        }

        return { token, claims };
    }

    const auth = setupHeader();
    const token = auth ? auth.token : null;
    const claims = auth ? auth.claims : null;
    const isAdmin = claims ? claims.is_admin === true : false;
    const currentUserId = claims ? claims.sub : null;

    // ─── Admin Panel ──────────────────────────────────────────────────────────

    function buildAdminPanel() {
        const panel = document.getElementById('admin-panel');
        if (!panel) return;

        if (!isAdmin || isClientMode()) {
            panel.style.display = 'none';
            return;
        }
        panel.style.display = 'block';

        panel.appendChild(cloneTemplate('tpl-admin-panel'));

        panel.querySelectorAll('.tab-btn').forEach(tabButton => {
            tabButton.addEventListener('click', () => {
                panel.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                panel.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                tabButton.classList.add('active');
                panel.querySelector(`#tab-${tabButton.dataset.tab}`).classList.add('active');
                if (tabButton.dataset.tab === 'users') loadUsers();
                if (tabButton.dataset.tab === 'amenities') loadAmenities();
                if (tabButton.dataset.tab === 'places') loadAdminPlaces();
            });
        });

        panel.querySelector('#btn-create-user').addEventListener('click', createUser);
        panel.querySelector('#btn-create-amenity').addEventListener('click', createAmenity);
        panel.querySelector('#btn-create-place').addEventListener('click', createPlace);

        loadUsers();
        loadAmenityChecklist();
    }

    async function apiPost(endpoint, body) {
        const response = await fetch(`${API}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(body)
        });
        return response;
    }

    async function apiDelete(endpoint) {
        const response = await fetch(`${API}${endpoint}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return response;
    }

    async function createUser() {
        const userData = {
            first_name: document.getElementById('u-fname').value.trim(),
            last_name: document.getElementById('u-lname').value.trim(),
            email: document.getElementById('u-email').value.trim(),
            password: document.getElementById('u-password').value,
            is_admin: document.getElementById('u-admin').checked
        };
        const response = await apiPost('/users/', userData);
        if (response.ok) {
            showToast('User created!');
            ['u-fname', 'u-lname', 'u-email', 'u-password'].forEach(fieldId => {
                document.getElementById(fieldId).value = '';
            });
            document.getElementById('u-admin').checked = false;
            loadUsers();
        } else {
            const error = await response.json();
            showToast('Error: ' + (error.message || response.statusText), true);
        }
    }

    async function createAmenity() {
        const name = document.getElementById('a-name').value.trim();
        const response = await apiPost('/amenities/', { name });
        if (response.ok) {
            showToast('Amenity created!');
            document.getElementById('a-name').value = '';
            loadAmenities();
            loadAmenityChecklist();
        } else {
            const error = await response.json();
            showToast('Error: ' + (error.message || response.statusText), true);
        }
    }

    async function createPlace() {
        const checklistContainer = document.getElementById('p-amenities-list');
        const checkedBoxes = checklistContainer
            ? checklistContainer.querySelectorAll('input[type="checkbox"]:checked')
            : [];
        const amenityIds = Array.from(checkedBoxes).map(checkbox => checkbox.dataset.id);

        const latitude = parseFloat(document.getElementById('p-lat').value);
        const longitude = parseFloat(document.getElementById('p-lng').value);

        if (latitude < -90 || latitude > 90) {
            showToast('Latitude must be between -90 and 90.', true);
            return;
        }
        if (longitude < -180 || longitude > 180) {
            showToast('Longitude must be between -180 and 180.', true);
            return;
        }

        const placeData = {
            title: document.getElementById('p-title').value.trim(),
            description: document.getElementById('p-desc').value.trim(),
            price: parseFloat(document.getElementById('p-price').value),
            latitude,
            longitude,
            amenities: amenityIds
        };
        const response = await fetch(`${API}/places/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(placeData)
        });
        if (response.ok) {
            showToast('Place created!');
            ['p-title', 'p-desc', 'p-price', 'p-lat', 'p-lng'].forEach(fieldId => {
                document.getElementById(fieldId).value = '';
            });
            if (checklistContainer) {
                checklistContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            }
            loadAdminPlaces();
        } else {
            const error = await response.json();
            showToast('Error: ' + (error.message || response.statusText), true);
        }
    }

    async function loadUsers() {
        const usersList = document.getElementById('users-list');
        if (!usersList) return;
        const response = await fetch(`${API}/users/`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (!response.ok) return;
        const users = await response.json();

        usersList.innerHTML = '';
        if (!users.length) {
            usersList.innerHTML = '<p class="admin-list-empty">No users yet.</p>';
            return;
        }
        users.forEach(user => {
            const node = cloneTemplate('tpl-user-item');
            const badge = node.querySelector('[data-field="badge"]');
            node.querySelector('[data-field="name"]').textContent  = `${user.first_name} ${user.last_name}`;
            node.querySelector('[data-field="email"]').textContent = user.email;
            badge.textContent = user.is_admin ? 'Admin' : 'Client';
            badge.className = user.is_admin ? 'badge-admin' : 'badge-client';
            usersList.appendChild(node);
        });
    }

    async function loadAmenities() {
        const amenitiesList = document.getElementById('amenities-list');
        if (!amenitiesList) return;
        const response = await fetch(`${API}/amenities/`);
        if (!response.ok) return;
        const amenities = await response.json();

        amenitiesList.innerHTML = '';
        if (!amenities.length) {
            amenitiesList.innerHTML = '<p class="admin-list-empty">No amenities yet.</p>';
            return;
        }
        amenities.forEach(amenity => {
            const node = cloneTemplate('tpl-amenity-item');
            node.querySelector('[data-field="name"]').textContent = amenity.name;
            node.querySelector('.btn-action-delete').addEventListener('click', async () => {
                if (!confirm(`Delete amenity "${amenity.name}"?`)) return;
                const deleteResponse = await apiDelete(`/amenities/${amenity.id}`);
                if (deleteResponse.ok) {
                    showToast('Amenity deleted.');
                    loadAmenities();
                    loadAmenityChecklist();
                } else {
                    showToast('Failed to delete amenity.', true);
                }
            });
            amenitiesList.appendChild(node);
        });
    }

    async function loadAdminPlaces() {
        const placesList = document.getElementById('places-list-admin');
        if (!placesList) return;
        const response = await fetch(`${API}/places/`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (!response.ok) return;
        const places = await response.json();

        placesList.innerHTML = '';
        if (!places.length) {
            placesList.innerHTML = '<p class="admin-list-empty">No places yet.</p>';
            return;
        }
        places.forEach(place => {
            const node = cloneTemplate('tpl-place-item');
            node.querySelector('[data-field="title"]').textContent = place.title;
            node.querySelector('[data-field="price"]').textContent = place.price ? `$${place.price} / night` : 'No price set';
            node.querySelector('[data-field="link"]').href = `place.html?id=${place.id}`;
            placesList.appendChild(node);
        });
    }

    async function loadAmenityChecklist() {
        const checklistContainer = document.getElementById('p-amenities-list');
        if (!checklistContainer) return;
        const response = await fetch(`${API}/amenities/`);
        if (!response.ok) return;
        const amenities = await response.json();

        checklistContainer.innerHTML = '';
        if (!amenities.length) {
            checklistContainer.innerHTML = '<p class="admin-list-empty" style="padding:0.75rem;">No amenities available.</p>';
            return;
        }
        amenities.forEach(amenity => {
            const item = document.createElement('label');
            item.className = 'amenity-checklist-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.dataset.id = amenity.id;

            const nameSpan = document.createElement('span');
            nameSpan.textContent = amenity.name;

            item.appendChild(checkbox);
            item.appendChild(nameSpan);
            checklistContainer.appendChild(item);
        });
    }

    // ─── Login page ───────────────────────────────────────────────────────────

    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (submitEvent) => {
            submitEvent.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const response = await fetch(`${API}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            if (response.ok) {
                const data = await response.json();
                document.cookie = `token=${data.access_token}; path=/`;
                window.location.href = 'index.html';
            } else {
                showToast('Login failed', true);
            }
        });
    }

    // ─── Index page ───────────────────────────────────────────────────────────

    if (document.getElementById('places-list')) {
        const priceFilter = document.getElementById('price-filter');
        if (priceFilter) {
            ['10', '50', '100', 'All'].forEach(priceValue => {
                const option = document.createElement('option');
                option.value = priceValue;
                option.textContent = priceValue === 'All' ? 'All' : `$${priceValue}`;
                priceFilter.appendChild(option);
            });
            priceFilter.addEventListener('change', (changeEvent) => {
                const selectedPrice = changeEvent.target.value;
                document.querySelectorAll('.place-card').forEach(card => {
                    const isVisible = selectedPrice === 'All' || parseFloat(card.dataset.price) <= parseFloat(selectedPrice);
                    card.style.display = isVisible ? 'block' : 'none';
                });
            });
        }

        fetchPlaces();
        buildAdminPanel();
    }

    async function fetchPlaces() {
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        const response = await fetch(`${API}/places/`, { headers });
        if (response.ok) displayPlaces(await response.json());
    }

    function displayPlaces(places) {
        const placesList = document.getElementById('places-list');
        placesList.innerHTML = '';
        if (!places.length) {
            placesList.textContent = 'No places available.';
            return;
        }
        places.forEach(place => {
            const node = cloneTemplate('tpl-place-card');
            const card = node.querySelector('.place-card');
            card.dataset.price = place.price || 0;
            node.querySelector('[data-field="title"]').textContent = place.title;
            node.querySelector('[data-field="price"]').textContent = `$${place.price || '—'} / night`;
            node.querySelector('[data-field="link"]').href = `place.html?id=${place.id}`;
            placesList.appendChild(node);
        });
    }

    // ─── Place Details page ────────────────────────────────────────────────────

    if (document.getElementById('place-details')) {
        const placeId = getPlaceIdFromURL();
        if (!placeId) {
            document.getElementById('place-details').textContent = 'Place not found.';
        } else {
            fetchPlaceDetails(placeId);
        }

        const addReviewSection = document.getElementById('add-review');
        if (addReviewSection) addReviewSection.style.display = token ? 'block' : 'none';
    }

    async function fetchPlaceDetails(placeId) {
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        const response = await fetch(`${API}/places/${placeId}`, { headers });
        if (response.ok) displayPlaceDetails(await response.json());
        else document.getElementById('place-details').textContent = 'Failed to load this place.';
    }

    function displayPlaceDetails(place) {
        const section = document.getElementById('place-details');
        const isOwner = currentUserId && place.owner_id === currentUserId;
        const canEdit = isAdmin || isOwner;

        const amenitiesText = place.amenities && place.amenities.length > 0
            ? place.amenities.map(amenity => typeof amenity === 'object' ? amenity.name : amenity).join(', ')
            : 'N/A';

        const ownerName = place.owner
            ? `${place.owner.first_name} ${place.owner.last_name}`
            : place.owner_id;

        const node = cloneTemplate('tpl-place-details');
        node.querySelector('[data-field="title"]').textContent = place.title;
        node.querySelector('[data-field="owner"]').textContent = ownerName;
        node.querySelector('[data-field="price"]').textContent = `$${place.price} / night`;
        node.querySelector('[data-field="description"]').textContent = place.description || 'No description available.';
        node.querySelector('[data-field="amenities"]').textContent = amenitiesText;

        const editButton = node.querySelector('#toggle-edit-place');
        const editForm = node.querySelector('#edit-place-form');

        if (canEdit) {
            editButton.style.display = 'inline-block';
            node.querySelector('#ep-title').value = place.title;
            node.querySelector('#ep-desc').value  = place.description || '';
            node.querySelector('#ep-price').value = place.price;
            editButton.addEventListener('click', async () => {
                editForm.style.display = 'block';
                await loadEditAmenityChecklist(place, editForm);
            });
            node.querySelector('#btn-cancel-place').addEventListener('click', () => editForm.style.display = 'none');
            node.querySelector('#btn-save-place').addEventListener('click', () => submitEditPlace(place.id));
        }

        section.innerHTML = '';
        section.appendChild(node);

        displayReviews(place);
    }

    async function loadEditAmenityChecklist(place, editForm) {
        const checklistContainer = editForm.querySelector('#ep-amenities-list');
        if (!checklistContainer) return;
        const response = await fetch(`${API}/amenities/`);
        if (!response.ok) return;
        const allAmenities = await response.json();

        const currentIds = new Set(
            (place.amenities || []).map(amenity => typeof amenity === 'object' ? amenity.id : amenity)
        );

        checklistContainer.innerHTML = '';
        if (!allAmenities.length) {
            checklistContainer.innerHTML = '<p style="padding:0.5rem; font-size:0.82rem; color:#aaa;">No amenities available.</p>';
            return;
        }
        allAmenities.forEach(amenity => {
            const item = document.createElement('label');
            item.className = 'amenity-checklist-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.dataset.id = amenity.id;
            checkbox.checked = currentIds.has(amenity.id);

            const nameSpan = document.createElement('span');
            nameSpan.textContent = amenity.name;

            item.appendChild(checkbox);
            item.appendChild(nameSpan);
            checklistContainer.appendChild(item);
        });
    }

    async function submitEditPlace(placeId) {
        const editChecklist = document.querySelector('#place-details #ep-amenities-list');
        const checkedBoxes = editChecklist ? editChecklist.querySelectorAll('input[type="checkbox"]:checked') : [];
        const amenityIds = Array.from(checkedBoxes).map(checkbox => checkbox.dataset.id);

        const updatedPlaceData = {
            title: document.getElementById('ep-title').value,
            description: document.getElementById('ep-desc').value,
            price: parseFloat(document.getElementById('ep-price').value),
            amenities: amenityIds
        };
        const response = await fetch(`${API}/places/${placeId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(updatedPlaceData)
        });
        if (response.ok) {
            showToast('Place updated!');
            fetchPlaceDetails(placeId);
        } else {
            const error = await response.json();
            showToast('Error: ' + (error.message || response.statusText), true);
        }
    }

    // ─── Reviews ──────────────────────────────────────────────────────────────

    function displayReviews(place) {
        const reviewsSection = document.getElementById('reviews');
        if (!reviewsSection) return;
        reviewsSection.innerHTML = '';

        const sectionTitle = document.createElement('h2');
        sectionTitle.textContent = 'Reviews';
        reviewsSection.appendChild(sectionTitle);

        const reviews = place.reviews || [];
        if (!reviews.length) {
            const emptyMessage = document.createElement('p');
            emptyMessage.textContent = 'No reviews yet.';
            reviewsSection.appendChild(emptyMessage);
            return;
        }

        reviews.forEach(review => {
            const isReviewOwner = currentUserId && review.user_id === currentUserId;
            const canEdit = isAdmin || isReviewOwner;
            const canDelete = isAdmin;

            const node = cloneTemplate('tpl-review-card');
            const card = node.querySelector('.review-card');
            card.id = `review-${review.id}`;

            node.querySelector('[data-field="user"]').textContent = review.user_name || review.user_id;
            node.querySelector('[data-field="rating"]').textContent = `Rating: ${review.rating}/5`;
            node.querySelector('[data-field="text"]').textContent = review.text;

            const editForm = node.querySelector('.review-edit-form');
            const editTextarea = node.querySelector('[data-field="edit-text"]');
            const ratingSelect = node.querySelector('[data-field="edit-rating"]');

            editTextarea.value = review.text;
            [1, 2, 3, 4, 5].forEach(ratingValue => {
                const option = document.createElement('option');
                option.value = ratingValue;
                option.textContent = `${ratingValue} - ${['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][ratingValue - 1]}`;
                if (review.rating === ratingValue) option.selected = true;
                ratingSelect.appendChild(option);
            });

            const editButton = node.querySelector('.btn-edit-review');
            const deleteButton = node.querySelector('.btn-delete-review');

            if (canEdit) {
                editButton.style.display = 'inline-block';
                editButton.addEventListener('click', () => editForm.style.display = 'block');
                node.querySelector('.btn-cancel-review').addEventListener('click', () => editForm.style.display = 'none');
                node.querySelector('.btn-save-review').addEventListener('click', () => submitEditReview(review.id, place.id));
            }

            if (canDelete) {
                deleteButton.style.display = 'inline-block';
                deleteButton.addEventListener('click', () => deleteReview(review.id, place.id));
            }

            reviewsSection.appendChild(node);
        });
    }

    async function submitEditReview(reviewId, placeId) {
        const reviewCard = document.getElementById(`review-${reviewId}`);
        const updatedText = reviewCard.querySelector('[data-field="edit-text"]').value;
        const updatedRating = parseInt(reviewCard.querySelector('[data-field="edit-rating"]').value);
        const response = await fetch(`${API}/reviews/${reviewId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ text: updatedText, rating: updatedRating })
        });
        if (response.ok) {
            showToast('Review updated!');
            fetchPlaceDetails(placeId);
        } else {
            const error = await response.json();
            showToast('Error: ' + (error.message || response.statusText), true);
        }
    }

    async function deleteReview(reviewId, placeId) {
        if (!confirm('Delete this review?')) return;
        const response = await fetch(`${API}/reviews/${reviewId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            showToast('Review deleted.');
            fetchPlaceDetails(placeId);
        } else {
            showToast('Failed to delete review.', true);
        }
    }

    // ─── Submit review inline (place.html) ───────────────────────────────────

    const reviewForm = document.getElementById('review-form');
    if (reviewForm && document.title !== 'Add Review') {
        reviewForm.addEventListener('submit', async (submitEvent) => {
            submitEvent.preventDefault();
            if (!token) { showToast('You must be logged in.', true); return; }
            const placeId = getPlaceIdFromURL();
            const reviewText = document.getElementById('review-text').value;
            const rating = parseInt(document.getElementById('rating').value);
            const response = await fetch(`${API}/reviews/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ text: reviewText, rating, place_id: placeId })
            });
            if (response.ok) {
                showToast('Review submitted!');
                reviewForm.reset();
                fetchPlaceDetails(placeId);
            } else {
                const error = await response.json();
                showToast('Error: ' + (error.message || response.statusText), true);
            }
        });
    }

    // ─── Add Review page ──────────────────────────────────────────────────────

    if (reviewForm && document.title === 'Add Review') {
        if (!token) { window.location.href = 'index.html'; }
        const placeId = getPlaceIdFromURL();
        reviewForm.addEventListener('submit', async (submitEvent) => {
            submitEvent.preventDefault();
            const reviewText = document.getElementById('review').value;
            const rating = parseInt(document.getElementById('rating').value);
            const response = await fetch(`${API}/reviews/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ text: reviewText, rating, place_id: placeId })
            });
            if (response.ok) {
                showToast('Review submitted!');
                reviewForm.reset();
            } else {
                const error = await response.json();
                showToast('Error: ' + (error.message || response.statusText), true);
            }
        });
    }

});