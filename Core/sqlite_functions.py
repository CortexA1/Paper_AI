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


def create_tables():
    # SQL-Befehl zum Erstellen der 'user' Tabelle
    user_table_query = """
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );
    """

    # SQL-Befehl zum Erstellen der 'address' Tabelle
    address_table_query = """
    CREATE TABLE IF NOT EXISTS address (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
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
    """

    # SQL-Befehl zum Erstellen der 'api_key' Tabelle
    api_key_table_query = """
    CREATE TABLE IF NOT EXISTS api_key (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        is_valid INTEGER DEFAULT 1,
        doc_intelli_endpoint TEXT DEFAULT NULL,
        doc_intelli_key TEXT DEFAULT NULL,
        openAI_endpoint TEXT DEFAULT NULL,
        openAI_key TEXT DEFAULT NULL,
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
    );
    """

    # Ausführen der Abfragen zum Erstellen der Tabellen
    _, err = execute_query(user_table_query)
    if err:
        st.error(f"Fehler beim Erstellen der Tabelle 'user': {err}")
        return

    _, err = execute_query(address_table_query)
    if err:
        st.error(f"Fehler beim Erstellen der Tabelle 'address': {err}")
        return

    # Erstellen der 'api_key' Tabelle
    _, err = execute_query(api_key_table_query)
    if err:
        st.error(f"Fehler beim Erstellen der Tabelle 'api_key': {err}")
        return


# Aufruf der Funktion zum Erstellen der Tabellen
create_tables()
