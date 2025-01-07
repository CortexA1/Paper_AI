import pandas as pd
import streamlit as st
import Core.functions as func
import importlib
importlib.reload(func)
import os
from pandasai import SmartDataframe
from pandasai import SmartDatalake
from pandasai.llm.openai import OpenAI
from pandasai.helpers.openai_info import get_openai_callback
from pandasai.responses.response_parser import ResponseParser

st.title("AI Chat")

userID = func.decrypt_message(st.session_state.ppai_usid, st.secrets["auth_token"])
doc_intelli_endpoint = func.decrypt_message(st.session_state.doc_intelli_endpoint, st.secrets["auth_token"])
doc_intelli_key = func.decrypt_message(st.session_state.doc_intelli_key, st.secrets["auth_token"])
openAI_endpoint = func.decrypt_message(st.session_state.openAI_endpoint, st.secrets["auth_token"])
openAI_key = func.decrypt_message(st.session_state.openAI_key, st.secrets["auth_token"])
chart_dir = func.decrypt_message(st.session_state.working_directory_user_chart, st.secrets["auth_token"])

llm = OpenAI(api_token=openAI_key)


# Funktion zur Überprüfung und Bereinigung der Dataframes ob ein Zeilenumbruch vorhanden ist => \n
# Dieser Zeilenumbruch kann von pandasai SmartDatalake nicht verarbeitet werden und wird als Liste erkannt
# Daher muss der Zeilenumbr. raus, entweder durch eine Leerstelle oder durch ein anderes Zeichen
# Eine Darstellung in Streamlit via st.dataframe funktioniert auch mit Zeilenumbruch
def check_and_clean_newlines(ai_object):
    for column in df.columns:
        if df[column].dtype == 'object':
            # Konvertiere die Spalte in Strings, um sicherzustellen, dass wir .str verwenden können
            df[column] = df[column].astype(str)
            if df[column].str.contains('\n').any():
                #print(f"Spalte '{column}' hat Zeilenumbrüche, die entfernt werden:")
                #print(df[column][df[column].str.contains('\n')])
                df[column] = df[column].str.replace('\n', ' ', regex=False)
    #print(f"Bereinigter DataFrame:\n{df}\n")

# Initialisiere den Session State für die Chat-Nachrichten und das DataFrame
# Sorgt dafür, dass es initialisiert wird, aber nicht geleert wird wenn es bereits voll ist
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.ai_object is not None:
    ai_object = st.session_state.ai_object
    # Daten anpassen für pandasai => wird direkt im DF durchgeführt
    #check_and_clean_newlines(ai_object)

    with st.chat_message("assistant"):
        # for doc_type, combined_result in ai_object:
        #     st.write(f"Datenvorschau für Typ: {doc_type}")
        #     st.dataframe(combined_result.head(50))
        for df in ai_object:
            check_and_clean_newlines(pd.DataFrame(df))
            st.dataframe(pd.DataFrame(df))

    # Zeige die bisherigen Nachrichten an (Chat-Log)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["type"] == "Dataframe":
                st.dataframe(message["content"])
            elif message["type"] == "Image":
                if os.path.exists(message["content"]):
                    st.image(message["content"], caption="Generiertes Chart")
                else:
                    st.markdown("Chart konnte nicht mehr gefunden werden ...")
            else:
                st.markdown(message["content"])

    prompt = st.chat_input("Prompt eingeben ...")

    if prompt:
        # Füge den Benutzer-Prompt in das Chat-Element ein
        st.session_state.messages.append({"role": "user", "type":"Text", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Generiere Antwort..."):
            # Erstelle den SmartDataframe mit den PandasAI-Einstellungen
            # Wenn nur ein Dataframe vorhanden ist, dann dieses hier verweden
            # sdf = SmartDataframe(df, 
            #         config={
            #                 "llm": llm,
            #                 "auto_generate_charts": True,
            #                 "save_charts": True,
            #                 "save_charts_path": chart_dir,
            #                 "enable_cache": True,
            #             }
            #         )

            # Extrahiere nur die DataFrames und füge sie einer Liste hinzu
            # dataframes_only = []
            # for label, df in ai_object:
            #     if isinstance(df, pd.DataFrame):
            #         dataframes_only.append(pd.DataFrame(df))
            #     else:
            #         print(f"Warnung: Ein Element ist kein DataFrame - {type(df)}")

            # Wenn mehrere Dataframes existieren, dann SmartDatalake verwenden
            # Achtung ggf. hier die Dataframes anpassen
            # Siehe Funktion check_and_clean_newlines, diese bereinigt das Problem mit Zeilenumbrüchen !!
            sdf = SmartDatalake([*ai_object],   
                config={
                    "llm": llm,
                    "auto_generate_charts": True,
                    "save_charts": True,
                    "save_charts_path": chart_dir,
                    "enable_cache": True,
                    "custom_whitelisted_dependencies": ["ast"]
                }                
            )
            
            # Verarbeite den Prompt
            with get_openai_callback() as cb:
                response = sdf.chat(prompt)                   
                
                # Prüfe, ob ein Chart generiert wurde
                if sdf.last_prompt_id:
                    chart_path = os.path.join(chart_dir, f"{sdf.last_prompt_id}.png")
                    
                    # Prüfe, ob die Datei existiert, wenn ja => chart, wenn nein => Text oder Dataframe
                    with st.chat_message("assistant"):
                        if os.path.exists(chart_path):
                            st.image(chart_path, caption="Generiertes Chart")
                            answer = chart_path
                            type = "Image"
                        else:
                            answer = response
                            # Prüfe, ob die Antwort ein DataFrame, eine Liste oder Text ist
                            if isinstance(response, pd.DataFrame):                                
                                # Zeige das gesamte DataFrame im Chat an
                                st.dataframe(response)  # Zeige das DataFrame als interaktive Tabelle an
                                type = "Dataframe"                           
                            else:
                                st.markdown(response)  # Zeige Text an
                                type = "Text"                           

                    # Füge die Antwort in das Chat-Element ein
                    st.session_state.messages.append({"role": "assistant", "type":type, "content": answer})

                st.write("💰 Verwendete Tokens / Kosten für diesen Prompt:")
                st.write(cb)
else:
    st.write("Keine Daten verfügbar. Bitte kehren Sie zur Übersicht zurück und wählen Sie Dokumente aus.")