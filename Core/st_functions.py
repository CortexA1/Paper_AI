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


def sync_session_state():
    sync_session_state_daten_kpi()
