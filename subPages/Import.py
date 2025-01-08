import streamlit as st
import Core.functions as func
import Core.mysql_functions as mysql
import importlib

importlib.reload(func)
importlib.reload(mysql)
import Core.AzureDocumentProcessor as adp
import pandas as pd


st.set_page_config(layout="centered")
st.title("Import")

userID = func.decrypt_message(st.session_state.ppai_usid, st.secrets["auth_token"])
doc_intelli_endpoint = func.decrypt_message(st.session_state.doc_intelli_endpoint, st.secrets["auth_token"])
doc_intelli_key = func.decrypt_message(st.session_state.doc_intelli_key, st.secrets["auth_token"])
openAI_endpoint = func.decrypt_message(st.session_state.openAI_endpoint, st.secrets["auth_token"])
openAI_key = func.decrypt_message(st.session_state.openAI_key, st.secrets["auth_token"])

def document_process(all_uploads):
    if all_uploads:
        all_results = []
        for uploaded_file in all_uploads:
            # Vorher kein uploaded_file.read() durchführen, weil die Dateiobjekte von st.file_uploader() in einem
            # Zustand sind, der nicht für die mehrfache Verarbeitung geeignet ist. In Streamlit sind die
            # hochgeladenen Dateien BytesIO-Objekte, die nur einmal gelesen werden können. Wenn du sie bereits einmal
            # eingelesen hast, sind sie „leer“ für nachfolgende Leseoperationen.
            result_df = doc_processor.process_upload(uploaded_file)
            all_results.append(result_df)
        return all_results

# Zustand der Session initialisieren
if 'df_all_uploads_result' not in st.session_state:
    st.session_state.df_all_uploads_result = None

if not doc_intelli_endpoint.strip() or not doc_intelli_key.strip():
    st.warning(
        "Die Keys konnten nicht geladen werden, oder existieren nicht nicht. Legen Sie diese an, um die Services "
        "nutzen zu können. Zu finden unter: Mein Account => Keyverwaltung")
    if st.button("Keys überprüfen", use_container_width=True):
        st.switch_page("subPages/Account.py")
else:
    # Erstelle eine Instanz der AzureDocumentProcessor Klasse
    doc_processor = adp.AzureDocumentProcessor(endpoint=doc_intelli_endpoint, key=doc_intelli_key)

    st.write(
        "Jedes Dateiformat kann hochgeladen werden. Handgeschriebene Dokumente als Bilddatei oder im PDF Format sind "
        "ebenfalls willkommen!")

    if st.secrets["demo_modus"] == 1:
        st.warning("Achtung! Der Demomodus erlaubt nur das Hochladen von wenigen Dokumenten. Probieren Sie das Tool mit maximal 5 verschiedenen Dokumenten, um einen Eindruck zu erhalten.")

    all_uploads = st.file_uploader("Dateien auswählen ...", accept_multiple_files=True)
    if all_uploads:
        if st.button("Dateien verarbeiten", use_container_width=True):
            with st.spinner('Dateien werden verarbeitet ...'):
                new_data = document_process(all_uploads)
                new_data_df = pd.DataFrame(new_data)

                if 'df_all_uploads_result' not in st.session_state or st.session_state.df_all_uploads_result is None:
                    # Wenn keine vorherigen Daten existieren, initialisiere das Ergebnis
                    st.session_state.df_all_uploads_result = new_data_df
                else:
                    # Wenn bereits Daten existieren, hänge die neuen Daten an
                    st.session_state.df_all_uploads_result = pd.concat(
                        [st.session_state.df_all_uploads_result, new_data_df], ignore_index=True)

    if st.session_state.df_all_uploads_result is not None:
        if st.button("Ergebnisse anzeigen", type="primary", use_container_width=True):
            st.switch_page("subPages/Daten.py")