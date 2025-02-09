import streamlit as st
import pandas as pd
import Core.sqlite_functions as sqlite
import Core.functions as func
import importlib
importlib.reload(func)

st.set_page_config(layout="wide")
st.title("Monitoring")

admin = func.decrypt_message(st.session_state.ppai_admin_user, st.secrets["auth_token"])
if admin == st.secrets["admin_user"]:

    st.subheader("User")
    user_info_query = """
        SELECT *
        FROM user
        """
    user_info, error_code = sqlite.execute_query(user_info_query)
    if error_code:
        st.error(f"Ein Fehler ist aufgetreten!")

    if user_info and len(user_info) > 0:
        st.dataframe(user_info)


    st.subheader("API-Keys")
    api_key_query = """
            SELECT *
            FROM api_key
            """
    api_info, error_code = sqlite.execute_query(api_key_query)
    if error_code:
        st.error(f"Ein Fehler ist aufgetreten!")

    if api_info and len(api_info) > 0:
        st.dataframe(api_info)
