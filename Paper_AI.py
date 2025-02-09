import streamlit as st
import Core.sqlite_functions as sqlite
import Core.functions as func
from streamlit_theme import st_theme
import importlib
import Core.st_functions as st_func
importlib.reload(st_func)

st_func.sync_session_state()

def check_existence(username, email):
    # Abfragen zur Benutzer- und E-Mail-Überprüfung
    user_query = "SELECT COUNT(*) AS count FROM user WHERE username = ?"
    email_query = "SELECT COUNT(*) AS count FROM user WHERE email = ?"

    user_exists_result, _ = sqlite.execute_query(user_query, params=(username,))
    email_exists_result, _ = sqlite.execute_query(email_query, params=(email,))

    # Schutz vor None
    user_exists = (user_exists_result[0]['count'] if user_exists_result else 0) > 0
    email_exists = (email_exists_result[0]['count'] if email_exists_result else 0) > 0

    return user_exists, email_exists

def set_Logo():

    theme = st_theme()

    if theme is not None:
        for key, value in theme.items():
            if key == "base":
                if value == "dark":
                    st.logo("Static/PaperAI_Logo_Streamlit_weiß.png", size="large", link="https://duesselai.de",
                            icon_image="Static/PaperAI_Logo_Streamlit_weiß.png")
                else:
                    st.logo("Static/PaperAI_Logo_Streamlit_schwarz.png", size="large", link="https://duesselai.de",
                            icon_image="Static/PaperAI_Logo_Streamlit_schwarz.png")

if st.session_state.demo_modus:
    pages = {
        "Generell": [
            st.Page("subPages/Dashboard.py", title="Dashboard")
            #st.Page("subPages/Account.py", title="Mein Account")
        ],
        "Dokumentenanalyse": [
            st.Page("subPages/Import.py", title="Import"),
            st.Page("subPages/Daten.py", title="Datenübersicht"),
            # st.Page("subPages/Analyse.py", title="Auswertungen"),
            st.Page("subPages/PandasAI.py", title="AI-Analyse")
        ],
    }
    pg = st.navigation(pages)
    pg.run()
    set_Logo()
else:
    if st.session_state.ppai_usid:
        # Adminmodus
        if func.decrypt_message(st.session_state.ppai_admin_user, st.secrets["auth_token"]) == st.secrets["admin_user"]:
            pages = {
                "Generell": [
                    st.Page("subPages/Dashboard.py", title="Dashboard"),
                    st.Page("subPages/Account.py", title="Mein Account"),
                    st.Page("subPages/Monitor.py", title="Monitoring")
                ],
                "Dokumentenanalyse": [
                    st.Page("subPages/Import.py", title="Import"),
                    st.Page("subPages/Daten.py", title="Datenübersicht"),
                    # st.Page("subPages/Analyse.py", title="Auswertungen"),
                    st.Page("subPages/PandasAI.py", title="AI-Analyse")
                ],
            }
        else:
            # Pages in SubPages Folder geschoben, damit nicht automatisch eine Sidebar Navigation erstellt wird
            pages = {
                "Generell": [
                    st.Page("subPages/Dashboard.py", title="Dashboard"),
                    st.Page("subPages/Account.py", title="Mein Account")
                ],
                "Dokumentenanalyse": [
                    st.Page("subPages/Import.py", title="Import"),
                    st.Page("subPages/Daten.py", title="Datenübersicht"),
                    # st.Page("subPages/Analyse.py", title="Auswertungen"),
                    st.Page("subPages/PandasAI.py", title="AI-Analyse")
                ],
            }

        pg = st.navigation(pages)
        pg.run()
        set_Logo()
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
                        login_query = """SELECT a.id, a.username, a.is_premium, a.key_openai FROM user a
                                                        WHERE (a.username = ? OR a.email = ?) 
                                                        AND a.password = ? 
                                                        AND a.is_active = TRUE;"""
                        result, error_code = sqlite.execute_query(login_query, params=(
                            login_username, login_username, func.auth_make_hashes(login_password)))

                        if error_code:
                            st.error(f"Fehlercode: {error_code}")
                        elif result and len(result) > 0:

                            st.session_state.ppai_usid = func.encrypt_message(result[0]["id"], st.secrets["auth_token"])

                            if result[0]["username"] == st.secrets["admin_user"]:
                                st.session_state.ppai_admin_user = func.encrypt_message(result[0]["username"], st.secrets["auth_token"])

                            st.session_state.ppai_license = func.encrypt_message(result[0]["is_premium"], st.secrets["auth_token"])
                            if result[0]["is_premium"] == 1:
                                st.session_state.doc_intelli_endpoint = func.encrypt_message(st.secrets["premium_document_api"], st.secrets["auth_token"])
                                st.session_state.doc_intelli_key = func.encrypt_message(st.secrets["premium_document_key"],st.secrets["auth_token"])
                            else:
                                st.session_state.doc_intelli_endpoint = func.encrypt_message(st.secrets["free_document_api"], st.secrets["auth_token"])
                                st.session_state.doc_intelli_key = func.encrypt_message(st.secrets["free_modus_document_key"], st.secrets["auth_token"])

                            st.session_state.openAI_key = func.encrypt_message(result[0]["key_openai"],st.secrets["auth_token"])
                            st.session_state.demo_modus = False
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
                #firstname = st.text_input("*Vorname").strip()
                #surename = st.text_input("Nachname").strip()
                #street = st.text_input("Straße / Hausnummer").strip()
                #postal_code = st.text_input("Postleitzahl").strip()
                #city = st.text_input("Stadt").strip()
                #country = st.text_input("Land", value="Deutschland").strip()
                #phonenumber = st.text_input("Telefonnummer", value="+49").strip()

                st.write("Die mit einem * markierten Felder sind Pflichtfelder.")
                # Submit-Button
                submitted = st.form_submit_button("Registrieren")

                if submitted:
                    # Überprüfen der Validierung und Anzeigen von Fehlern
                    errors = func.validate_form(fields_to_check=["username", "email", "password", "password_confirmation"],
                                                     username=username,
                                                     email=email,
                                                     password=password,
                                                     password_confirmation=password_confirmation)
                                                     #firstname=firstname,
                                                     #surename=surename,
                                                     #street=street,
                                                     #postal_code=postal_code,
                                                     #city=city, country=country,
                                                     #phonenumber=phonenumber)
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
                                "INSERT INTO user (username, email, password) VALUES (?, ?, ?)",
                                #"INSERT INTO address (user_id, firstname, surename, street, postal_code, city, country, phonenumber) VALUES (last_insert_rowid(), ?, ?, ?, ?, ?, ?, ?)"
                            ]

                            transaction_params = [
                                (username, email, func.auth_make_hashes(password)),
                                #(firstname, surename, street, postal_code, city, country, phonenumber)
                            ]

                            affected_rows, error_code = sqlite.execute_transaction(transaction_queries, transaction_params)

                            if error_code:
                                st.toast(f"Fehlercode: {error_code}", icon="🚨")
                            else:
                                st.toast("Registrierung erfolgreich!", icon="🔥")

        st.markdown("---")
        if st.button("Demomodus ohne Login nutzen", use_container_width=True, type="primary"):
            st.session_state.demo_modus = True
            st.session_state.doc_intelli_endpoint = func.encrypt_message(st.secrets["prod_document_api"],st.secrets["auth_token"])
            st.session_state.doc_intelli_key = func.encrypt_message(st.secrets["prod_document_key"],st.secrets["auth_token"])
            st.rerun()