import streamlit as st
import Core.functions as func
import importlib
import time
importlib.reload(func)
import Core.AzureDocumentProcessor as adp
import pandas as pd
import email
from email import policy
from email.parser import BytesParser
import os

st.set_page_config(layout="centered")
st.title("Import")

userID = func.decrypt_message(st.session_state.ppai_usid, st.secrets["auth_token"])
doc_intelli_endpoint = func.decrypt_message(st.session_state.doc_intelli_endpoint, st.secrets["auth_token"])
doc_intelli_key = func.decrypt_message(st.session_state.doc_intelli_key, st.secrets["auth_token"])
openAI_endpoint = func.decrypt_message(st.session_state.openAI_endpoint, st.secrets["auth_token"])
openAI_key = func.decrypt_message(st.session_state.openAI_key, st.secrets["auth_token"])

def CalculateKPIs(all_results):
    # KPIs from whole Dataset
    all_results = pd.DataFrame(all_results)

    st.session_state.df_all_uploads_result_kpi_rechnung = (all_results["doc_type"] == "Rechnung").sum()
    st.session_state.df_all_uploads_result_kpi_kassenbon = (all_results["doc_type"] == "Kassenbon").sum()
    st.session_state.df_all_uploads_result_kpi_duplikat = (all_results.duplicated(subset=['file_name']).sum())
    st.session_state.df_all_uploads_result_kpi_unbekannt = (all_results["doc_type"] == "Unbekannt").sum()
    st.session_state.df_all_uploads_result_kpi_wahrscheinlichkeit_doc_type = f"{((all_results[all_results['doc_type'] != 'Unbekannt']['doc_type_confidence'].astype(float) / 100).mean()) * 100:.2f}%"

def CalculateKPIsActual(all_results):
    # KPIs from actual run
    all_results = pd.DataFrame(all_results)

    st.session_state.df_all_uploads_result_kpi_rechnung_actual = (all_results["doc_type"] == "Rechnung").sum()
    st.session_state.df_all_uploads_result_kpi_kassenbon_actual = (all_results["doc_type"] == "Kassenbon").sum()
    st.session_state.df_all_uploads_result_kpi_duplikat_actual = (all_results.duplicated(subset=['file_name']).sum())
    st.session_state.df_all_uploads_result_kpi_unbekannt_actual = (all_results["doc_type"] == "Unbekannt").sum()

def document_process(all_uploads):
    if all_uploads:
        all_results = []
        for uploaded_file in all_uploads:
            # Wenn es sich um eine Mail handelt
            if uploaded_file.type in ["message/rfc822"]:
                # Parsen der E-Mail
                email_bytes = uploaded_file.read()
                msg = BytesParser(policy=policy.default).parsebytes(email_bytes)
                # Durchsuchen der Teile der E-Mail
                for part in msg.walk():
                    # Prüfen, ob es sich um einen Anhang handelt
                    if part.get_filename():  # Dateiname vorhanden
                        attachment_filename = part.get_filename()
                        attachment_content = part.get_payload(decode=True)
                        attachment_type = part.get_content_type()

                        # Wrapper-Objekt für den Anhang erstellen
                        class AttachmentWrapper:
                            def __init__(self, content, name, type_):
                                self.content = content
                                self.name = name
                                self.type = type_

                            def read(self):
                                return self.content

                        attachment_wrapper = AttachmentWrapper(
                            content=attachment_content,
                            name=attachment_filename,
                            type_=attachment_type
                        )

                        result_df = doc_processor.process_upload(attachment_wrapper)
                        all_results.append(result_df)
            else:
                # Vorher kein uploaded_file.read() durchführen, weil die Dateiobjekte von st.file_uploader() in einem
                # Zustand sind, der nicht für die mehrfache Verarbeitung geeignet ist. In Streamlit sind die
                # hochgeladenen Dateien BytesIO-Objekte, die nur einmal gelesen werden können. Wenn du sie bereits einmal
                # eingelesen hast, sind sie „leer“ für nachfolgende Leseoperationen.
                result_df = doc_processor.process_upload(uploaded_file)
                all_results.append(result_df)

        return all_results

if not doc_intelli_endpoint.strip() or not doc_intelli_key.strip():
    if st.session_state.demo_modus:
        st.switch_page("subPages/Dashboard.py")
    else:
        st.warning(
            "Die Keys konnten nicht geladen werden, oder existieren nicht nicht. Legen Sie diese an, um die Services "
            "nutzen zu können. Zu finden unter: Mein Account => Keyverwaltung")
        if st.button("Keys überprüfen", use_container_width=True):
            st.switch_page("subPages/Account.py")
else:
    # Erstelle eine Instanz der AzureDocumentProcessor Klasse
    doc_processor = adp.AzureDocumentProcessor(endpoint=doc_intelli_endpoint, key=doc_intelli_key)

    st.write(
        "Laden Sie ihre Dokumente, E-Mails oder Bilder hoch. Der Importer erlaubt nahezu jedes Format!")

    if st.session_state.demo_modus:
        st.warning("Achtung! Der Demomodus erlaubt nur das Hochladen von wenigen Dokumenten. Probieren Sie das Tool mit maximal 5 verschiedenen Dokumenten, um einen Eindruck zu erhalten.")

        # Funktion zur Überprüfung der Upload-Beschränkungen
        def can_upload():
            # Aktuellen Zeitstempel abrufen
            current_time = time.time()
            # Alte Zeitstempel entfernen (älter als 5 Minuten)
            st.session_state.upload_timestamps = [t for t in st.session_state.upload_timestamps if
                                                  current_time - t <= 300]
            # Rückgabe: ob Upload erlaubt ist (weniger als 5 in der letzten Minute)
            return len(st.session_state.upload_timestamps) < 5


        all_uploads = st.file_uploader("Dateien auswählen ...", accept_multiple_files=True)
        if all_uploads:
            if len(all_uploads) > 5:
                st.error("Im Demomodus können Sie maximal 5 Dokumente gleichzeitig hochladen.")
            elif not can_upload():
                st.error(
                    "Im Demomodus können Sie maximal 5 Dokumente alle 5 Minuten hochladen. Bitte warten Sie einen Moment ...")
            else:
                if st.button("Dateien verarbeiten", use_container_width=True):
                    with st.spinner('Dateien werden verarbeitet ...'):
                        # Zeitstempel der Uploads hinzufügen
                        st.session_state.upload_timestamps.extend([time.time()] * len(all_uploads))
                        new_data = document_process(all_uploads)
                        new_data_df = pd.DataFrame(new_data)

                        CalculateKPIsActual(new_data_df)

                        if st.session_state.df_all_uploads_result is None:
                            # Wenn keine vorherigen Daten existieren, initialisiere das Ergebnis
                            st.session_state.df_all_uploads_result = new_data_df
                        else:
                            # Wenn bereits Daten existieren, hänge die neuen Daten an
                            st.session_state.df_all_uploads_result = pd.concat(
                                [st.session_state.df_all_uploads_result, new_data_df], ignore_index=True)

                        CalculateKPIs(st.session_state.df_all_uploads_result)
    else:
        all_uploads = st.file_uploader("Dateien auswählen ...", accept_multiple_files=True)
        if all_uploads:
            if st.button("Dateien verarbeiten", use_container_width=True):
                with st.spinner('Dateien werden verarbeitet ...'):
                    new_data = document_process(all_uploads)
                    new_data_df = pd.DataFrame(new_data)

                    CalculateKPIsActual(new_data_df)

                    if st.session_state.df_all_uploads_result is None:
                        st.session_state.df_all_uploads_result = new_data_df
                    else:
                        st.session_state.df_all_uploads_result = pd.concat(
                            [st.session_state.df_all_uploads_result, new_data_df], ignore_index=True)

                    CalculateKPIs(st.session_state.df_all_uploads_result)

    if st.session_state.df_all_uploads_result is not None:
        if st.button("Ergebnisse anzeigen", type="primary", use_container_width=True):
            st.switch_page("subPages/Daten.py")

    if st.session_state.demo_modus:
        #
        # Download von Testdateien im Demomodus
        #

        # Funktion zum Lesen einer Datei aus dem "static"-Ordner
        @st.cache_data
        def read_file(file_path, mode="rb"):
            with open(file_path, mode) as file:
                return file.read()


        st.markdown("---")
        st.subheader("📥 Demodateien:")
        st.write("Laden Sie unsere Testdateien herunter, um diese im Importer auszuprobieren!")

        cols = st.columns(2)  # Erstellt drei Spalten

        with cols[0]:
            pdf_path = "Static/PaperAI_Rechnung_PDF.pdf"
            pdf_content = read_file(pdf_path)
            st.download_button(label="Rechnung (PDF)",
                               data=pdf_content,
                               file_name="PaperAI_Rechnung_PDF.pdf",
                               mime="application/pdf",
                               type="secondary",
                               use_container_width=True)

            jpeg_path = "Static/PaperAI_Kassenbon_Image_1.jpg"
            jpeg_content = read_file(jpeg_path)
            st.download_button(label="Kassenbon Version 1 (JPEG)",
                               data=jpeg_content,
                               file_name="PaperAI_Kassenbon_Image_1.jpg",
                               mime="image/jpeg",
                               type="secondary",
                               use_container_width=True)

            excel_path = "Static/PaperAI_Datenset_Titanic_Excel.xlsx"
            excel_content = read_file(excel_path)
            st.download_button(label="Datensatz Titanic (Excel)",
                               data=excel_content,
                               file_name="PaperAI_Datenset_Titanic_Excel.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               type="secondary",
                               use_container_width=True)

        with cols[1]:
            pdf_path = "Static/PaperAI_Rechnung_PNG.png"
            pdf_content = read_file(pdf_path)
            st.download_button(label="Rechnung (PNG)",
                               data=pdf_content,
                               file_name="PaperAI_Rechnung_PNG.png",
                               mime="image/png",
                               type="secondary",
                               use_container_width=True)

            jpeg_path = "Static/PaperAI_Kassenbon_Image_2.jpg"
            jpeg_content = read_file(jpeg_path)
            st.download_button(label="Kassenbon Version 2 (JPEG)",
                               data=jpeg_content,
                               file_name="PaperAI_Kassenbon_Image_2.jpg",
                               mime="image/jpeg",
                               type="secondary",
                               use_container_width=True)