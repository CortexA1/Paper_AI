import streamlit as st
import psutil
import os
import pandas as pd
from datetime import datetime
import Core.functions as func
import importlib
importlib.reload(func)

st.title("Live Monitoring der Streamlit-App")

admin = func.decrypt_message(st.session_state.ppai_admin_user, st.secrets["auth_token"])
if admin == st.secrets["admin_user"]:
    # Funktion, um die CPU- und RAM-Informationen der Streamlit-App zu holen
    def get_streamlit_app_info():
        pid = os.getpid()  # Holen der aktuellen Prozess-ID
        process = psutil.Process(pid)  # Holen des Prozesses basierend auf der PID
        cpu_usage = process.cpu_percent(interval=1)  # CPU Nutzung der Streamlit-App in %
        memory_usage = process.memory_info().rss / (1024 ** 2)  # RAM Nutzung in MB
        return cpu_usage, memory_usage

    # Platzhalter für die Diagramme und Variablen im Session-State
    if 'cpu_data' not in st.session_state:
        st.session_state.cpu_data = []
        st.session_state.ram_data = []
        st.session_state.timestamps = []  # Liste für Zeitstempel

    # Streamlit Layout
    st.write("Aktuelle CPU- und RAM-Nutzung der Streamlit-Anwendung:")

    # Holen der Streamlit-App Informationen
    cpu_usage, memory_usage = get_streamlit_app_info()

    # Aktuellen Zeitstempel der Messung holen
    timestamp = datetime.now()

    # Daten und Zeitstempel hinzufügen
    st.session_state.cpu_data.append(cpu_usage)
    st.session_state.ram_data.append(memory_usage)
    st.session_state.timestamps.append(timestamp)

    # Begrenzen der Anzahl von Punkten im Diagramm, um es übersichtlich zu halten
    if len(st.session_state.cpu_data) > 50:
        st.session_state.cpu_data = st.session_state.cpu_data[-50:]
        st.session_state.ram_data = st.session_state.ram_data[-50:]
        st.session_state.timestamps = st.session_state.timestamps[-50:]

    # Erstellen eines DataFrames mit Zeitstempeln
    df_cpu = pd.DataFrame({
        'Timestamp': st.session_state.timestamps,
        'CPU Nutzung (%)': st.session_state.cpu_data
    })
    df_ram = pd.DataFrame({
        'Timestamp': st.session_state.timestamps,
        'RAM Nutzung (MB)': st.session_state.ram_data
    })

    # Anzeigen des CPU-Diagramms
    st.subheader("CPU Nutzung (%)")
    st.line_chart(df_cpu.set_index('Timestamp'))

    # Anzeigen des RAM-Diagramms
    st.subheader("RAM Nutzung (MB)")
    st.line_chart(df_ram.set_index('Timestamp'))

    # Anzeige der aktuellen Systemnutzung
    st.markdown(f"""
    **Aktuelle CPU Nutzung der Streamlit-App**: {cpu_usage}%  
    **Aktuelle RAM Nutzung der Streamlit-App**: {memory_usage:.2f} MB
    """)

    # Neu-Laden der Seite alle 5 Sekunden, um die Daten zu aktualisieren
    st.rerun()
