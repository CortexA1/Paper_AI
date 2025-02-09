import streamlit as st
import Core.sqlite_functions as sqlite
import Core.functions as func
from shutil import rmtree
import os

st.set_page_config(layout="centered")
st.title("Account")

userID = func.decrypt_message(st.session_state.ppai_usid, st.secrets["auth_token"])
chart_dir = func.decrypt_message(st.session_state.working_directory_user_chart, st.secrets["auth_token"])
key_openai = func.decrypt_message(st.session_state.openAI_key, st.secrets["auth_token"])

license_val = sqlite.get_license(userID)
# Lizenz nochmal aktualisiere, falls diese gerade aktualisiert wurde (ansonsten ReLogin)
st.session_state.ppai_license = license_val

env = st.radio(
    "Ihr aktueller Lizenzstatus:",
    ("Basis", "Premium"),
    disabled=True,
    index=license_val  # Wert wie in der DB, entweder 0 oder 1 (0 Basis, 1 Premium)
)
if license_val == 0:
    st.info("Für Premium, kontaktieren Sie uns unter <info@duesselai.de>.")

with st.expander("Keyverwaltung"):
    with st.form("form_key"):
        openAI_key = st.text_input("*Key - OpenAI", key_openai, type="password").strip()
        key_submitted = st.form_submit_button("Aktualisieren")

        if key_submitted:
                query = "UPDATE user SET key_openai = ? WHERE id = ? AND is_active = TRUE"
                result, error_code = sqlite.execute_query(query, params=(openAI_key, userID))

                if error_code:
                    st.error(f"Ein Fehler ist aufgetreten!")
                else:
                    st.session_state.openAI_key = func.encrypt_message(openAI_key,st.secrets["auth_token"])
                    st.success("Erfolgreich aktualisiert!")


if st.button("Chart Cache leeren", type="primary"):
    if os.path.exists(chart_dir):
        rmtree(chart_dir)  # Lösche den Ordner und alle Inhalte
    os.makedirs(chart_dir)  # Erstelle den Ordner neu
    st.session_state.messages = [] 

# Mail und PW kommt separat
