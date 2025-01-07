-- Erklärungen zu den Tabellen:

-- user Tabelle:
-- Enthält die Basisinformationen über den Benutzer. Das is_active-Feld wird verwendet, um den Benutzerstatus zu verwalten.

-- address Tabelle:
-- Diese Tabelle speichert Adressinformationen mit Versionierung, um den Verlauf von Adressänderungen zu erfassen. valid_from und valid_to bestimmen die Gültigkeit, während is_current anzeigt, ob die Adresse aktuell ist.

-- service Tabelle:
-- Speichert die verschiedenen Dienstleistungen. Das is_active-Feld ermöglicht es, Services zu deaktivieren, ohne sie zu löschen.

-- user_service Tabelle:
-- Verknüpft Benutzer mit abonnierten Services und verfolgt den Abonnementstatus. Versionierungsfelder wie start_date, end_date und is_active sind enthalten.

-- api_key Tabelle:
-- Enthält API-Schlüssel für Benutzer. Das is_valid-Feld wird verwendet, um den Status des Schlüssels zu verwalten.

-- Erstellen der 'user' Tabelle
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

ALTER TABLE user AUTO_INCREMENT=100000;

-- Erstellen der 'address' Tabelle mit Versionierung
CREATE TABLE address (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    firstname VARCHAR(100) NOT NULL,
    surename VARCHAR(100) NOT NULL,
    street VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) NOT NULL,
    phonenumber VARCHAR(30) NOT NULL,
    valid_from DATETIME DEFAULT CURRENT_TIMESTAMP,
    valid_to DATETIME,
    is_current BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Erstellen der 'service' Tabelle mit Soft Deletes
CREATE TABLE service (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Erstellen der 'user_service' Tabelle mit Versionierung
CREATE TABLE user_service (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    service_id INT,
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    has_paid_this_month BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES service(id) ON DELETE CASCADE
);

-- Erstellen der 'api_key' Tabelle mit Soft Deletes
CREATE TABLE api_key (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    is_valid BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Metatabelle für Dokumente
CREATE TABLE documents (
    doc_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    doc_type VARCHAR(50),
    doc_type_confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    successful BOOLEAN DEFAULT TRUE,
    archived BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- Tabelle für Rechnungsbasisinformationen
CREATE TABLE Invoices (
    invoice_base_id INT AUTO_INCREMENT PRIMARY KEY,
    doc_id INT,
    invoice_id VARCHAR(255),
    vendor_name VARCHAR(255),
    vendor_name_confidence FLOAT,
    vendor_address TEXT,
    vendor_address_confidence FLOAT,
    vendor_address_recipient VARCHAR(255),
    vendor_address_recipient_confidence FLOAT,
    customer_name VARCHAR(255),
    customer_name_confidence FLOAT,
    customer_id VARCHAR(255),
    customer_id_confidence FLOAT,
    customer_address TEXT,
    customer_address_confidence FLOAT,
    customer_address_recipient VARCHAR(255),
    customer_address_recipient_confidence FLOAT,
    invoice_date VARCHAR(255),
    invoice_date_confidence FLOAT,
    invoice_total DECIMAL(15, 2),
    invoice_total_confidence FLOAT,
    invoice_total_clean DECIMAL(15, 2),
    due_date VARCHAR(255),
    due_date_confidence FLOAT,
    purchase_order VARCHAR(255),
    purchase_order_confidence FLOAT,
    billing_address TEXT,
    billing_address_confidence FLOAT,
    shipping_address TEXT,
    shipping_address_confidence FLOAT,
    subtotal DECIMAL(15, 2),
    subtotal_confidence FLOAT,
    subtotal_clean DECIMAL(15, 2),
    total_tax DECIMAL(15, 2),
    total_tax_confidence FLOAT,
    total_tax_clean DECIMAL(15, 2),
    amount_due DECIMAL(15, 2),
    amount_due_confidence FLOAT
);

-- Tabelle für Rechnungspositionen
CREATE TABLE InvoiceItems (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_base_id INT,
    item_description TEXT,
    item_description_confidence FLOAT,
    item_quantity INT,
    item_quantity_confidence FLOAT,
    unit VARCHAR(255),
    unit_confidence FLOAT,
    unit_price DECIMAL(15, 2),
    unit_price_confidence FLOAT,
    unit_price_code VARCHAR(255),
    product_code VARCHAR(255),
    product_code_confidence FLOAT,
    item_date VARCHAR(255),
    item_date_confidence FLOAT,
    tax DECIMAL(15, 2),
    tax_confidence FLOAT,
    amount DECIMAL(15, 2),
    amount_confidence FLOAT,
    amount_clean DECIMAL(15, 2),
    FOREIGN KEY (invoice_base_id) REFERENCES Invoices(invoice_base_id)
);



-- Tabelle für Kassenbons
CREATE TABLE receipts (
    receipt_id VARCHAR(100) PRIMARY KEY,
    doc_id VARCHAR(50),
    merchant_name VARCHAR(255),
    merchant_name_confidence FLOAT,
    transaction_date DATE,
    transaction_date_confidence FLOAT,
    subtotal DECIMAL(15, 2),
    subtotal_confidence FLOAT,
    total_tax DECIMAL(15, 2),
    total_tax_confidence FLOAT,
    tip DECIMAL(15, 2),
    tip_confidence FLOAT,
    total DECIMAL(15, 2),
    total_confidence FLOAT,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
);

-- Tabelle für Kassenbon-Positionen
CREATE TABLE receipt_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    receipt_id VARCHAR(100),
    item_description TEXT,
    item_description_confidence FLOAT,
    item_quantity FLOAT,
    item_quantity_confidence FLOAT,
    individual_item_price DECIMAL(15, 2),
    individual_item_price_confidence FLOAT,
    total_item_price DECIMAL(15, 2),
    total_item_price_confidence FLOAT,
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
);
