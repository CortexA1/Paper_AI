import streamlit as st
import Core.mysql_functions as mysql
import re
import Core.functions as func


def check_existence(username, email):
    user_query = "SELECT COUNT(*) AS count FROM user WHERE username = %s"
    email_query = "SELECT COUNT(*) AS count FROM user WHERE email = %s"

    user_exists_result, _ = mysql.execute_query(user_query, params=(username,))
    email_exists_result, _ = mysql.execute_query(email_query, params=(email,))

    # Schutz vor None
    user_exists = (user_exists_result[0]['count'] if user_exists_result else 0) > 0
    email_exists = (email_exists_result[0]['count'] if email_exists_result else 0) > 0

    return user_exists, email_exists


# Initialisiere den Session State
if 'ppai_usid' not in st.session_state:
    st.session_state.ppai_usid = None
    st.session_state.doc_intelli_endpoint = None
    st.session_state.doc_intelli_key = None
    st.session_state.openAI_endpoint = None
    st.session_state.openAI_key = None

if st.secrets["demo_modus"] == 1:
    # Im Demomodus gibt es kein "Mein Account"
    pages = {
        "Generell": [
            st.Page("subPages/Dashboard.py", title="Dashboard")
            #st.Page("subPages/Account.py", title="Mein Account")
        ],
        "Rechnungsanalyse": [
            st.Page("subPages/Import.py", title="Import"),
            st.Page("subPages/Daten.py", title="Datenübersicht"),
            # st.Page("subPages/Analyse.py", title="Auswertungen"),
            st.Page("subPages/DocIntelli_Chat.py", title="AI Chat")
        ],
    }
    pg = st.navigation(pages)
    pg.run()
else:
    if st.session_state.ppai_usid:
        # Pages in SubPages Folder geschoben, damit nicht automatisch eine Sidebar Navigation erstellt wird
        pages = {
            "Generell": [
                st.Page("subPages/Dashboard.py", title="Dashboard"),
                st.Page("subPages/Account.py", title="Mein Account")
            ],
            "Rechnungsanalyse": [
                st.Page("subPages/Import.py", title="Import"),
                st.Page("subPages/Daten.py", title="Datenübersicht"),
                # st.Page("subPages/Analyse.py", title="Auswertungen"),
                st.Page("subPages/DocIntelli_Chat.py", title="AI Chat")
            ],
        }
        pg = st.navigation(pages)
        pg.run()
    else:
        tb_login, tb_register = st.tabs(["Login", "Registrieren"])
        with tb_login:
            with st.form('form_login'):
                st.header("Login")
                login_username = st.text_input("Username oder E-Mail").strip()
                login_password = st.text_input("Passwort", type="password").strip()
                login_submitted = st.form_submit_button("Anmelden")
                if login_submitted:
                    if login_username or login_password:
                        login_query = """SELECT a.id FROM user a
                                        WHERE (a.username = %s OR a.email = %s) 
                                        AND a.password = %s 
                                        AND a.is_active = TRUE;"""
                        result, error_code = mysql.execute_query(login_query, params=(
                        login_username, login_username, func.auth_make_hashes(login_password)))

                        if error_code:
                            st.error(f"Fehlercode: {error_code}")
                        elif result and len(result) > 0:
                            st.session_state.ppai_usid = func.encrypt_message(result[0]["id"],
                                                                                   st.secrets["auth_token"])
                            st.rerun()
                        else:
                            st.error("Username (E-Mail) oder Passwort falsch.")
                    else:
                        st.error("Es müssen Login Credentials eingegeben werden!")

        with tb_register:
            with st.form('form_register'):
                st.header("Registrieren")

                # Felder für die Registrierung
                username = st.text_input("*Benutzername").strip()
                email = st.text_input("*E-Mail").strip()
                password = st.text_input("*Passwort", type="password").strip()
                password_confirmation = st.text_input("*Passwort bestätigen", type="password").strip()
                firstname = st.text_input("*Vorname").strip()
                surename = st.text_input("*Nachname").strip()
                street = st.text_input("*Straße / Hausnummer").strip()
                postal_code = st.text_input("*Postleitzahl").strip()
                city = st.text_input("*Stadt").strip()
                country = st.text_input("*Land", value="Deutschland").strip()
                phonenumber = st.text_input("*Telefonnummer", value="+49").strip()

                st.write("Die mit einem * markierten Felder sind Pflichtfelder.")
                # Submit-Button
                submitted = st.form_submit_button("Registrieren")

                if submitted:
                    # Überprüfen der Validierung und Anzeigen von Fehlern
                    errors = func.validate_form(username=username,
                                                     email=email,
                                                     password=password,
                                                     password_confirmation=password_confirmation,
                                                     firstname=firstname,
                                                     surename=surename,
                                                     street=street,
                                                     postal_code=postal_code,
                                                     city=city, country=country,
                                                     phonenumber=phonenumber)
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        user_exists, email_exists = check_existence(username, email)

                        if user_exists:
                            st.error("Benutzername ist bereits vergeben.")
                        elif email_exists:
                            st.error("E-Mail-Adresse ist bereits vergeben.")
                        else:
                            transaction_queries = [
                                "INSERT INTO user (username, email, password) VALUES (%s, %s, %s)",
                                "INSERT INTO address (user_id, firstname, surename, street, postal_code, city, country, phonenumber) VALUES (LAST_INSERT_ID(), %s, %s, %s, %s, %s, %s, %s)"
                            ]

                            transaction_params = [
                                (username, email, func.auth_make_hashes(password)),
                                (firstname, surename, street, postal_code, city, country, phonenumber)
                            ]

                            affected_rows, error_code = mysql.execute_transaction(transaction_queries, transaction_params)

                            if error_code:
                                st.error(f"Fehlercode: {error_code}")
                            else:
                                st.success("Registrierung erfolgreich!")