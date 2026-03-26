-- Inserts the initial admin user and amenities into the HBnB database
 
-- Administrator user (fixed UUID, password: admin1234)
INSERT INTO users (id, first_name, last_name, email, password, is_admin, created_at, updated_at)
VALUES (
    '36c9050e-ddd3-4c3b-9731-9f487208bbc1',
    'Admin',
    'HBnB',
    'admin@hbnb.io',
    '$2b$12$TWb1CjdhXX2MX3ShZaXPIeQDbNdXE.gKROzKYjhklhl4vN8DWHHfC',
    1,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO amenities (id, name, created_at, updated_at) VALUES
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567801', 'WiFi', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567802', 'Swimming Pool', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567803', 'Air Conditioning', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);