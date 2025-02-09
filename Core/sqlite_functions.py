import sqlite3
import streamlit as st
import pandas as pd

# Funktion zum Testen der DB-Verbindung
def test_db_connection():
    try:
        connection = sqlite3.connect(st.secrets["db_name"])
        cursor = connection.cursor()
        cursor.execute("SELECT 1")  # Einfache Abfrage zum Testen der Verbindung
        st.success("Verbindung zur Datenbank erfolgreich!")
        connection.close()
    except sqlite3.Error as err:
        st.error(f"Fehler bei der Verbindung zur Datenbank: {err}")

# Funktion zum Abrufen der DB-Verbindung
def get_db_connection():
    try:
        connection = sqlite3.connect(st.secrets["db_name"])
        connection.row_factory = sqlite3.Row  # Ergebnisse als Dictionary
        return connection
    except sqlite3.Error:
        return None

# Funktion zum Ausführen von Abfragen
def execute_query(query, params=None, as_dataframe=False):
    connection = get_db_connection()
    if connection is None:
        return None, "Verbindung nicht hergestellt"

    try:
        cursor = connection.cursor()

        if query.strip().upper().startswith('SELECT'):
            cursor.execute(query, params or ())
            result = [dict(row) for row in cursor.fetchall()]

            if as_dataframe:
                return pd.DataFrame(result), None
            else:
                return result, None
        else:
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.rowcount, None
    except sqlite3.Error as err:
        return None, str(err)
    finally:
        cursor.close()
        connection.close()

# Funktion für Transaktionen
def execute_transaction(queries, params_list):
    connection = get_db_connection()
    if connection is None:
        return None, "Verbindung nicht hergestellt"

    try:
        cursor = connection.cursor()
        connection.execute("BEGIN TRANSACTION")

        for query, params in zip(queries, params_list):
            cursor.execute(query, params or ())

        connection.commit()
        return cursor.rowcount, None
    except sqlite3.Error as err:
        connection.rollback()
        return None, str(err)
    finally:
        cursor.close()
        connection.close()

def get_license(userID):
    query = """
                SELECT is_premium
                FROM user
                WHERE id = ?
                AND is_active = TRUE
                """

    license_info, license_error_code = execute_query(query, params=(userID,))

    if license_error_code:
        st.error(f"Ein Fehler beim abrufen der Lizenz ist aufgetreten!")
    elif license_info and len(license_info) > 0:
        license_info = license_info[0]
        return license_info["is_premium"]  # Wert wie in der DB, entweder 0 oder 1 (0 Basis, 1 Premium)
    else:
        st.error("Das laden der Lizenz für die Dokumentenverarbeitung ist fehlgeschlagen.")

    return 0

def create_tables():

    # Mittlerweile ist lediglich die user Tabelle notwendig

    # SQL-Befehl zum Erstellen der 'user' Tabelle
    user_table_query = """
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        is_premium BOOLEAN DEFAULT FALSE,
        key_openai VARCHAR(255) DEFAULT NULL
    );
    """

    # Ausführen der Abfragen zum Erstellen der Tabellen
    _, err = execute_query(user_table_query)
    if err:
        st.error(f"Fehler beim Erstellen der Tabelle 'user': {err}")
        return

# Aufruf der Funktion zum Erstellen der Tabellen
create_tables()
