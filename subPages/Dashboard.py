import streamlit as st
import Core.sqlite_functions as sqlite
import Core.functions as func
import os
import shutil
import uuid
from streamlit_theme import st_theme

def get_folder_size(folder_path):
    """Berechnet die Größe des Ordners in Bytes."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    return total_size

def clear_folder(folder_path):
    """Löscht alle Dateien und Unterordner im angegebenen Ordner."""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Datei oder Symbolischen Link löschen
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Verzeichnis löschen
        except Exception as e:
            #print(f"Fehler beim Löschen von {file_path}: {e}")
            if not st.session_state.demo_modus:
                st.error("Temporärer Ordner ist zu groß und muss geleert werden. Dabei ist ein Fehler aufgetreten. Probieren Sie es manuell /Mein Account/Chart Cache leeren.")

def monitor_folder(folder_path, max_size_mb=5):
    """Überwacht den Ordner und leert ihn, wenn die Größe das Limit überschreitet."""
    max_size_bytes = max_size_mb * 1024 * 1024  # MB in Bytes umrechnen
    folder_size = get_folder_size(folder_path)
    if folder_size > max_size_bytes:
        if not st.session_state.demo_modus:
            st.info(f"Temporäre Ordnergröße ({folder_size / (1024 * 1024):.2f} MB) überschreitet das Limit von {max_size_mb} MB. Ordner wurde automatisch geleert.")
        clear_folder(folder_path)
    else:
        if not st.session_state.demo_modus:
            st.success(f"Temporäre Ordnergröße: {folder_size / (1024 * 1024):.2f} MB - innerhalb des Limits von {max_size_mb} MB.")

def manage_directory(specified_user_folder):
    if not st.session_state.demo_modus:
        st.subheader("Dateiverwaltung:")

    main_path = os.getcwd() + "/user_data/"
    user_path = main_path + str(specified_user_folder)
    chart_path = user_path + "/output_charts/"

    st.session_state.working_directory_user = func.encrypt_message(user_path, st.secrets["auth_token"])
    st.session_state.working_directory_user_chart = func.encrypt_message(chart_path, st.secrets["auth_token"])
    monitor_folder(user_path)

st.set_page_config(layout="centered")

if st.session_state.demo_modus:

    # Funktional
    manage_directory(str("demo_" + uuid.uuid4().hex))
    st.session_state.doc_intelli_endpoint = func.encrypt_message(st.secrets["demo_modus_document_api"],
                                                                 st.secrets["auth_token"])
    st.session_state.doc_intelli_key = func.encrypt_message(st.secrets["demo_modus_document_key"],
                                                            st.secrets["auth_token"])

    # Anzeige des Demomodus
    url_register = "https://paper-ai-dus.streamlit.app"
    st.title(f"Willkommen im Demomodus!")
    st.write("Der Demomodus ist limitiert, bietet jedoch eine gute Möglichkeit Paper AI kennen zu lernen. In diesem Modus ist ein eigener Key notwendig, wenn Sie den AI Chat zur Analyse der Daten nutzen möchten.")
    st.write("Um Ihre Keys dauerhaft zu speichern und von weiteren Vorteilen zu profitieren, können Sie sich auch registrieren.")
    if st.button("Verstanden, weiter zum Importer", type="primary", use_container_width=True):
        st.switch_page("subPages/Import.py")
    #openAI_key = st.text_input("Key - OpenAI", type="password").strip()
    #if st.button("Bestätigen und loslegen!", type="primary", use_container_width=True):
    #    st.session_state.openAI_key = func.encrypt_message(openAI_key, st.secrets["auth_token"])
    #    st.switch_page("subPages/Import.py")
else:
    userID = func.decrypt_message(st.session_state.ppai_usid, st.secrets["auth_token"])
    # Benutzerinformationen abrufen und anzeigen
    user_info_query = """
    SELECT u.username, u.email
    FROM user u
    WHERE u.id = ?
    """
    user_info, error_code = sqlite.execute_query(user_info_query, params=(userID,))
    if error_code:
        st.error(f"Ein Fehler ist aufgetreten!")
        st.stop()
    elif user_info and len(user_info) > 0:
        user_info = user_info[0]
        st.title(f"Hallo {user_info['username']}!")
        st.write("Hier erhalten Sie eine Übersicht über den aktuellen Status.")

        manage_directory(str(userID))

        st.subheader("Key Status:")
        user_info_query = """
        SELECT doc_intelli_endpoint, doc_intelli_key, openAI_endpoint, openAI_key
        FROM api_key
        WHERE user_id = ?
        AND is_valid = TRUE
        """
        user_info, error_code = sqlite.execute_query(user_info_query, params=(userID,))
        if error_code:
            st.error(f"Ein Fehler beim abrufen der Keys ist aufgetreten!")

        if user_info and len(user_info) > 0:

            st.session_state.doc_intelli_endpoint = func.encrypt_message(user_info[0]["doc_intelli_endpoint"], st.secrets["auth_token"])
            st.session_state.doc_intelli_key = func.encrypt_message(user_info[0]["doc_intelli_key"], st.secrets["auth_token"])
            st.session_state.openAI_endpoint = func.encrypt_message(user_info[0]["openAI_endpoint"], st.secrets["auth_token"])
            st.session_state.openAI_key = func.encrypt_message(user_info[0]["openAI_key"], st.secrets["auth_token"])

            st.success("Erfolgreich!")

            # st.write("Endpoint - Dokumentenanalyse: " + functions.decrypt_message(st.session_state.doc_intelli_endpoint, st.secrets["auth_token"]))
            # st.write("Key - Dokumentenanalyse: " + functions.decrypt_message(st.session_state.doc_intelli_key, st.secrets["auth_token"]))
            # st.write("Endpoint - OpenAI: " + functions.decrypt_message(st.session_state.openAI_endpoint, st.secrets["auth_token"]))
            # st.write("Key - OpenAI: " + functions.decrypt_message(st.session_state.openAI_key, st.secrets["auth_token"]))

        else:
            # Wenn keine Keys geladen werden können, werden hier erstmal die Demo / Dev Keys verwendet.
            if st.secrets.get("demo_modus_document_api"):
                # Der Wert existiert und ist nicht None, leer, oder False
                st.session_state.doc_intelli_endpoint = func.encrypt_message(st.secrets["demo_modus_document_api"], st.secrets["auth_token"])
            if st.secrets.get("demo_modus_document_key"):
                # Der Wert existiert und ist nicht None, leer, oder False
                st.session_state.doc_intelli_key = func.encrypt_message(st.secrets["demo_modus_document_key"], st.secrets["auth_token"])

            st.warning("Die Keys konnten nicht geladen werden, oder existieren noch nicht. Legen Sie diese an, um die Services nutzen zu können. Zu finden unter: Mein Account => Keyverwaltung")
            if st.button("Keys überprüfen", use_container_width=True, type="primary"):
                st.switch_page("subPages/Account.py")
    else:
        st.error("Fehler beim Abrufen der Benutzerinformationen.")
