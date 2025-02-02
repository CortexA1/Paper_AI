import streamlit as st

def sync_session_state_daten_kpi():

    # All runs
    if 'df_all_uploads_result_kpi_rechnung' not in st.session_state:
        st.session_state.df_all_uploads_result_kpi_rechnung = None

    if 'df_all_uploads_result_kpi_kassenbon' not in st.session_state:
        st.session_state.df_all_uploads_result_kpi_kassenbon = None

    if 'df_all_uploads_result_kpi_duplikat' not in st.session_state:
        st.session_state.df_all_uploads_result_kpi_duplikat = None

    if 'df_all_uploads_result_kpi_unbekannt' not in st.session_state:
        st.session_state.df_all_uploads_result_kpi_unbekannt = None

    if 'df_all_uploads_result_kpi_wahrscheinlichkeit_doc_type' not in st.session_state:
        st.session_state.df_all_uploads_result_kpi_wahrscheinlichkeit_doc_type = None

    # Actual run
    if 'df_all_uploads_result_kpi_rechnung_actual' not in st.session_state:
        st.session_state.df_all_uploads_result_kpi_rechnung_old = None

    if 'df_all_uploads_result_kpi_kassenbon_actual' not in st.session_state:
        st.session_state.df_all_uploads_result_kpi_kassenbon_old = None

    if 'df_all_uploads_result_kpi_duplikat_actual' not in st.session_state:
        st.session_state.df_all_uploads_result_kpi_duplikat_old = None

    if 'df_all_uploads_result_kpi_unbekannt_actual' not in st.session_state:
        st.session_state.df_all_uploads_result_kpi_unbekannt_old = None

def sync_sessions_state_system():
    if 'ppai_usid' not in st.session_state:
        st.session_state.ppai_usid = None

    if 'doc_intelli_endpoint' not in st.session_state:
        st.session_state.doc_intelli_endpoint = None

    if 'doc_intelli_key' not in st.session_state:
        st.session_state.doc_intelli_key = None

    if 'openAI_endpoint' not in st.session_state:
        st.session_state.openAI_endpoint = None

    if 'openAI_key' not in st.session_state:
        st.session_state.openAI_key = None

    if 'working_directory_user_chart' not in st.session_state:
        st.session_state.working_directory_user_chart = None

    if 'df_all_uploads_result' not in st.session_state:
        st.session_state.df_all_uploads_result = None

    # Session-State für Upload-Zählung (Demomodus)
    if 'upload_timestamps' not in st.session_state:
        st.session_state.upload_timestamps = []

    if 'ai_object' not in st.session_state:
        st.session_state.ai_object = None

    # Initialisiere den Session State für die Chat-Nachrichten und das DataFrame
    # Sorgt dafür, dass es initialisiert wird, aber nicht geleert wird wenn es bereits voll ist
    if "messages" not in st.session_state:
        st.session_state.messages = []

def sync_session_state():
    sync_sessions_state_system()
    sync_session_state_daten_kpi()
