import streamlit as st
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
        SELECT 
        id as "User ID",
        username as "Username",
        email as "E-Mail",
        created_at as "Erstellt am",
        updated_at as "Aktualisiert am",
        is_active as "Aktiv",
        is_premium as "Premium",
        key_openai as "OpenAI Key"
        FROM user
        """
    user_info, error_code = sqlite.execute_query(user_info_query)
    if error_code:
        st.error(f"Ein Fehler ist aufgetreten!")

    if user_info and len(user_info) > 0:
        st.dataframe(user_info)

    st.subheader("Datensatz aktualisieren")
    def update_user(column, value, userID):
        query = f"UPDATE user SET {column} = ? WHERE ID = ?"
        result, error_code = sqlite.execute_query(query, (value, userID))
        if error_code:
            st.toast(error_code)
        else:
            st.toast("Erfolgreich!")

    def delete_user(userID):
        query = f"DELETE FROM user WHERE ID = ?"
        result, error_code = sqlite.execute_query(query, (userID,))
        if error_code:
            st.toast(error_code)
        else:
            st.toast("Erfolgreich!")


    userID = st.number_input("Welche User ID soll aktualisiert werden?", step=1, format="%d")

    # Zwei Spalten für Buttons nebeneinander
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        if st.button("Account löschen", use_container_width=True, type="primary"):
            update_user("is_active", 0, userID)
        if st.button("Account auf Basis", use_container_width=True, type="primary"):
            update_user("is_premium", 0, userID)
        if st.button("Datensatz löschen", use_container_width=True, type="primary"):
            delete_user(userID)

    with btn_col2:
        if st.button("Account wiederherstellen", use_container_width=True, type="primary"):
            update_user("is_active", 1, userID)
        if st.button("Account auf Premium", use_container_width=True, type="primary"):
            update_user("is_premium", 1, userID)