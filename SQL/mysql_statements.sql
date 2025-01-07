-- ##############################
-- # USER TABLE OPERATIONS
-- ##############################

-- Einfügen eines neuen Benutzers
INSERT INTO user (username, email, password)
VALUES ('[USERNAME]', '[EMAIL]', '[HASHED_PASSWORD]');

-- Überprüfen, ob ein Benutzername oder eine E-Mail existiert
SELECT * FROM user WHERE (username = '[USERNAME]' OR email = '[EMAIL]') AND is_active = TRUE;

-- Überprüfen der Benutzeranmeldedaten (Login)
SELECT * FROM user 
WHERE (username = '[USERNAME]' OR email = '[EMAIL]') 
AND password = '[HASHED_PASSWORD]' 
AND is_active = TRUE;

-- Aktualisieren eines Benutzers (z.B. E-Mail ändern)
UPDATE user
SET email = '[NEW_EMAIL]', updated_at = CURRENT_TIMESTAMP
WHERE id = [USER_ID] AND is_active = TRUE;

-- Soft Delete eines Benutzers
UPDATE user
SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
WHERE id = [USER_ID] AND is_active = TRUE;

-- Abfragen aller aktiven Benutzer
SELECT * FROM user WHERE is_active = TRUE;

-- ##############################
-- # ADDRESS TABLE OPERATIONS
-- ##############################

-- Einfügen einer neuen Adresse (Versionierung)
INSERT INTO address (user_id, firstname, surename, street, postal_code, city, country, phonenumber)
VALUES ([USER_ID], '[FIRSTNAME]', '[SURENAME]', '[STREET]', '[POSTAL_CODE]', '[CITY]', '[COUNTRY]', '[PHONENUMBER]');

-- Alte Adresse als nicht aktuell markieren
UPDATE address
SET is_current = FALSE, valid_to = CURRENT_TIMESTAMP
WHERE user_id = [USER_ID] AND is_current = TRUE;

-- Abfragen der aktuellen Adresse eines Benutzers
SELECT * FROM address 
WHERE user_id = [USER_ID] AND is_current = TRUE;

-- Abfragen aller Adressen eines Benutzers (historisch)
SELECT * FROM address 
WHERE user_id = [USER_ID] ORDER BY valid_from DESC;

-- ##############################
-- # SERVICE TABLE OPERATIONS
-- ##############################

-- Einfügen eines neuen Services
INSERT INTO service (name, description, price)
VALUES ('[SERVICE_NAME]', '[DESCRIPTION]', [PRICE]);

-- Aktualisieren eines Services
UPDATE service
SET description = '[NEW_DESCRIPTION]', price = [NEW_PRICE]
WHERE id = [SERVICE_ID] AND is_active = TRUE;

-- Soft Delete eines Services
UPDATE service
SET is_active = FALSE
WHERE id = [SERVICE_ID] AND is_active = TRUE;

-- Abfragen aller aktiven Services
SELECT * FROM service WHERE is_active = TRUE;

-- ##############################
-- # USER_SERVICE TABLE OPERATIONS
-- ##############################

-- Einfügen einer neuen Service-Buchung
INSERT INTO user_service (user_id, service_id, start_date, is_active)
VALUES ([USER_ID], [SERVICE_ID], CURRENT_DATE, TRUE);

-- Aktualisieren einer Service-Buchung (z.B. Verlängerung oder Kündigung)
UPDATE user_service
SET end_date = '[END_DATE]', is_active = FALSE
WHERE user_id = [USER_ID] AND service_id = [SERVICE_ID] AND is_active = TRUE;

-- Abfragen aller aktiven Services eines Benutzers
SELECT s.id, s.name, s.description, s.price, us.start_date, us.end_date
FROM service s
JOIN user_service us ON s.id = us.service_id
WHERE us.user_id = [USER_ID] AND us.is_active = TRUE;

-- ##############################
-- # API_KEY TABLE OPERATIONS
-- ##############################

-- Einfügen eines neuen API-Schlüssels
INSERT INTO api_key (user_id, api_key)
VALUES ([USER_ID], '[API_KEY]');

-- Deaktivieren eines API-Schlüssels
UPDATE api_key
SET is_valid = FALSE
WHERE user_id = [USER_ID] AND api_key = '[API_KEY]' AND is_valid = TRUE;

-- Abfragen aller aktiven API-Schlüssel eines Benutzers
SELECT * FROM api_key 
WHERE user_id = [USER_ID] AND is_valid = TRUE;

-- ##############################
-- # BEISPIEL: VERKNÜPFTE ABFRAGEN
-- ##############################

-- Zeige alle aktuellen API-Keys von User X an
SELECT * FROM api_key 
WHERE user_id = [USER_ID] AND is_valid = TRUE;

-- Zeige alle gebuchten Services von User X an
SELECT s.id, s.name, s.description, s.price, us.start_date, us.end_date
FROM service s
JOIN user_service us ON s.id = us.service_id
WHERE us.user_id = [USER_ID] AND us.is_active = TRUE;
