import streamlit as st
import Core.sqlite_functions as sqlite
import Core.functions as func
from shutil import rmtree
import os

st.set_page_config(layout="centered")
st.title("Account")

userID = func.decrypt_message(st.session_state.ppai_usid, st.secrets["auth_token"])
chart_dir = func.decrypt_message(st.session_state.working_directory_user_chart, st.secrets["auth_token"])

#st.header(f"Ihre UserID: {userID}")

#
# Adresse wurde deaktiviert, hat aktuell keinen nutzen
#
if 1 == 0:
    with st.expander("Adressverwaltung"):
        tab_current, tab_history = st.tabs(["Aktuell", "Historie"])
        with tab_current:
            # Benutzerinformationen abrufen und anzeigen
            user_info_query = """
            SELECT u.username, u.email, 
               COALESCE(a.firstname, '') as firstname, 
               COALESCE(a.surename, '') as surename, 
               COALESCE(a.street, '') as street, 
               COALESCE(a.postal_code, '') as postal_code, 
               COALESCE(a.city, '') as city, 
               COALESCE(a.country, '') as country, 
               COALESCE(a.phonenumber, '') as phonenumber
            FROM user u
            LEFT JOIN address a ON u.id = a.user_id AND a.is_current = TRUE
            WHERE u.id = ?
            """
            user_info, error_code = sqlite.execute_query(user_info_query, params=(userID,))
            if error_code:
                st.error(f"Ein Fehler ist aufgetreten!")
            elif user_info and len(user_info) > 0:
                with st.form('form_refresh'):
                    user_info = user_info[0]
                    st.header("Adresse aktualisieren")
                    username = st.text_input("*Benutzername", user_info.get('username', ''), disabled=True).strip()
                    email = st.text_input("*E-Mail", user_info.get('email', ''), disabled=True).strip()
                    firstname = st.text_input("*Vorname", user_info.get('firstname', '')).strip()
                    surename = st.text_input("*Nachname", user_info.get('surename', '')).strip()
                    street = st.text_input("*Straße / Hausnummer", user_info.get('street', '')).strip()
                    postal_code = st.text_input("*Postleitzahl", user_info.get('postal_code', '')).strip()
                    city = st.text_input("*Stadt", user_info.get('city', '')).strip()
                    country = st.text_input("*Land", user_info.get('country', '')).strip()
                    phonenumber = st.text_input("*Telefonnummer", user_info.get('phonenumber', '')).strip()

                    st.write("Die mit einem * markierten Felder sind Pflichtfelder.")
                    refresh_submitted = st.form_submit_button("Aktualisieren")

                    if refresh_submitted:

                        # Überprüfen der Validierung und Anzeigen von Fehlern
                        errors = func.validate_form(fields_to_check=["firstname", "surename", "street", "postal_code", "city", "country", "phonenumber"]
                                                        , firstname=firstname, surename=surename, street=street, postal_code=postal_code
                                                        , city=city, country=country, phonenumber=phonenumber)
                        if errors:
                            for error in errors:
                                st.error(error)
                        else:
                            transaction_queries = [
                                """ UPDATE address 
                                    SET is_current = FALSE, valid_to = CURRENT_TIMESTAMP 
                                    WHERE user_id = ? AND is_current = TRUE AND EXISTS (
                                        SELECT 1 FROM address WHERE user_id = ? AND is_current = TRUE
                                    )""",
                                """INSERT INTO address (user_id, firstname, surename, street, postal_code, city, country, phonenumber)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                                """
                            ]

                            transaction_params = [
                                (userID, userID),
                                (userID,
                                firstname, surename, street, postal_code, city, country, phonenumber)
                            ]

                            affected_rows, error_code = sqlite.execute_transaction(transaction_queries, transaction_params)

                            if error_code:
                                st.error(f"Fehlercode: {error_code}")
                            else:
                                st.success("Die Adresse wurde erfolgreich aktualisiert!")
            else:
                st.error("Fehler beim Abrufen der Benutzerinformationen.")
        with tab_history:
            user_info_query = """
                SELECT 
                a.valid_from as 'Gültig ab', 
                u.username as Benutzername, 
                u.email as 'E-Mail', 
                a.firstname as Vorname, 
                a.surename as Name, 
                a.street as Straße, 
                a.postal_code as Postleitzahl, 
                a.city as Stadt, 
                a.country as Land, 
                a.phonenumber as Telefonnummer
                FROM user u
                LEFT JOIN address a ON u.id = a.user_id
                WHERE u.id = ?
                order by a.valid_from desc
                """
            user_info, error_code = sqlite.execute_query(user_info_query, params=(userID,), as_dataframe=True)
            if error_code:
                st.error(f"Ein Fehler ist aufgetreten!")
            else:
                st.dataframe(user_info)

with st.expander("Keyverwaltung"):
    user_info_query = """
    SELECT doc_intelli_endpoint, doc_intelli_key, openAI_endpoint, openAI_key
    FROM api_key
    WHERE user_id = ?
    AND is_valid = TRUE
    """
    user_info, error_code = sqlite.execute_query(user_info_query, params=(userID,))
    if error_code:
        st.error(f"Ein Fehler ist aufgetreten!")

    with st.form("form_key"):    
        if user_info and len(user_info) > 0:
            ## UPDATEN
                st.header("Keys aktualisieren")
                user_info = user_info[0]
                doc_intelli_endpoint = st.text_input("*Endpoint - Dokumentenanalyse", user_info['doc_intelli_endpoint']).strip()
                doc_intelli_key = st.text_input("*Key - Dokumentenanalyse", user_info['doc_intelli_key'], type="password").strip()
                openAI_endpoint = st.text_input("Endpoint - OpenAI", user_info['openAI_endpoint']).strip()
                openAI_key = st.text_input("*Key - OpenAI", user_info['openAI_key'], type="password").strip()
        else:
            ## EINFÜGEN
                st.header("Keys erstmalig erstellen")
                doc_intelli_endpoint = st.text_input("*Endpoint - Dokumentenanalyse", func.decrypt_message(st.session_state.doc_intelli_endpoint, st.secrets["auth_token"])).strip()
                doc_intelli_key = st.text_input("*Key - Dokumentenanalyse", func.decrypt_message(st.session_state.doc_intelli_key, st.secrets["auth_token"]), type="password").strip()
                openAI_endpoint = st.text_input("Endpoint - OpenAI").strip()
                openAI_key = st.text_input("*Key - OpenAI", type="password").strip()

        st.info("Kontaktieren Sie uns <info@duesselai.de> um den produktiven Key zum auslesen der Dokumente zu erhalten."
                   "Mit diesem können Sie unbegrenzt viele Dokumente analysieren, erhalten mehr performance und eine "
                   "deutlich bessere Wahrscheinlichkeitsermittlung des Typs.")
        #st.info("Der OpenAI Endpoint kann bereits definiert werden, hat allerdings noch keine Auswirkung, da sich dieser noch in der Entwicklung befindet. Bis dahin wird der Endpoint von OpenAI selber 'https://openai.com' genutzt. Später kann hier der eigens gehostete Endpoint genutzt werden.")
        key_submitted = st.form_submit_button("Aktualisieren")

        if key_submitted:
            # Prüfung, ob alle Felder ausgefüllt sind
            # Erstmal ohne openAI_endpoint
            if not doc_intelli_endpoint.strip() or not doc_intelli_key.strip() or not openAI_key.strip():
                st.warning("Bitte füllen Sie alle Felder aus, bevor Sie fortfahren!")
            else:

                transaction_queries = [
                    "UPDATE api_key SET is_valid = FALSE WHERE user_id = ? AND is_valid = TRUE;",
                    "INSERT INTO api_key (user_id, doc_intelli_endpoint, doc_intelli_key, openAI_endpoint, openAI_key) VALUES (?, ?, ?, ?, ?);"
                ]

                transaction_params = [
                    (userID,),
                    (userID, doc_intelli_endpoint, doc_intelli_key, openAI_endpoint, openAI_key)
                ]

                affected_rows, error_code = sqlite.execute_transaction(transaction_queries, transaction_params)

                if error_code:
                    st.error(f"Fehlercode: {error_code}")
                else:
                    st.session_state.doc_intelli_endpoint = func.encrypt_message(doc_intelli_endpoint, st.secrets["auth_token"])
                    st.session_state.doc_intelli_key = func.encrypt_message(doc_intelli_key, st.secrets["auth_token"])
                    st.session_state.openAI_endpoint = func.encrypt_message(openAI_endpoint, st.secrets["auth_token"])
                    st.session_state.openAI_key = func.encrypt_message(openAI_key, st.secrets["auth_token"])

                    st.success("Erfolgreich aktualisiert!")

if st.button("Chart Cache leeren", type="primary"):
    if os.path.exists(chart_dir):
        rmtree(chart_dir)  # Lösche den Ordner und alle Inhalte
    os.makedirs(chart_dir)  # Erstelle den Ordner neu
    st.session_state.messages = [] 

# Mail und PW kommt separat
