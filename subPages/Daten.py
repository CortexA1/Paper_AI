import streamlit as st
import pandas as pd
import Core.functions as func
import importlib
importlib.reload(func)

st.set_page_config(layout="wide")
st.title("Datenübersicht")

#
#
# Die Wahrscheinlichkeitsspalten werden nicht angezeigt.
# 
#

userID = func.decrypt_message(st.session_state.ppai_usid, st.secrets["auth_token"])
doc_intelli_endpoint = func.decrypt_message(st.session_state.doc_intelli_endpoint, st.secrets["auth_token"])
doc_intelli_key = func.decrypt_message(st.session_state.doc_intelli_key, st.secrets["auth_token"])
openAI_endpoint = func.decrypt_message(st.session_state.openAI_endpoint, st.secrets["auth_token"])
openAI_key = func.decrypt_message(st.session_state.openAI_key, st.secrets["auth_token"])
chart_dir = func.decrypt_message(st.session_state.working_directory_user_chart, st.secrets["auth_token"])

if not doc_intelli_endpoint.strip() or not doc_intelli_key.strip():
    st.switch_page("subPages/Dashboard.py")

if st.session_state.df_all_uploads_result is not None:

    st.write("Der Import war erfolgreich - hier sind die Ergebnisse:")

    all_results = pd.DataFrame(st.session_state.get('df_all_uploads_result'))

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(label="Rechnungen", value=st.session_state.df_all_uploads_result_kpi_rechnung,
                delta=int(st.session_state.df_all_uploads_result_kpi_rechnung_actual))

    col2.metric(label="Kassenbons", value=st.session_state.df_all_uploads_result_kpi_kassenbon,
                delta=int(st.session_state.df_all_uploads_result_kpi_kassenbon_actual))

    col3.metric(label="Duplikate", value=st.session_state.df_all_uploads_result_kpi_duplikat,
                delta=int(st.session_state.df_all_uploads_result_kpi_duplikat_actual))

    col4.metric(label="Fehlerhafte Analysen", value=st.session_state.df_all_uploads_result_kpi_unbekannt,
                delta=int(st.session_state.df_all_uploads_result_kpi_unbekannt_actual))

    col5.metric(label="Ø Wahrsch. in (%) der Dok. Typen", value=st.session_state.df_all_uploads_result_kpi_wahrscheinlichkeit_doc_type)



    # Konfiguriere die Spalteneinstellungen
    column_configuration = {
        "file_name": st.column_config.TextColumn(
            "Dateiname", help="Der Name der Datei", width="medium"
        ),
        "file_type": st.column_config.TextColumn(
            "Art der Datei"
        ),
        "doc_type": st.column_config.TextColumn(
            "Dokumententyp",
            help="Der ermittelte Dokumententyp",
            width="medium"
        ),
        "result": st.column_config.TextColumn(
            "Ergebnis",
            max_chars=0
        ),
        "doc_type_confidence": st.column_config.TextColumn(
            "%-Wahrscheinlichkeit",
            help="Die Wahrscheinlichkeit, dass dieser Dokumententyp richtig ermittelt wurde.",
            width="small"
        ),
        "successful": st.column_config.TextColumn(
            "Erfolgreich",
            width="small"
        ),
        "doc_id": st.column_config.TextColumn(
            "ID", help="Die Verarbeitungs ID des Objekts", width="small"
        )
    }

    # Zeige das DataFrame in einer interaktiven Tabelle mit Auswahlmöglichkeit
    event = st.dataframe(
        all_results,
        column_order=("file_name", "file_type", "doc_type", "doc_type_confidence"),
        column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
    )

    # Wähle die Zeilen basierend auf der Auswahl
    selection = event.selection.rows
    filtered_df = all_results.iloc[selection]

    # Erstelle eine leere Liste zur Sammlung von Ergebnissen nach `doc_type`
    combined_results_by_type = []

    # Iteriere über die eindeutigen Dokumententypen und filtere entsprechend
    doc_types = filtered_df['doc_type'].unique()
    for doc_type in doc_types:
        doc_type_selection = filtered_df[filtered_df['doc_type'] == doc_type]
        combined_result = pd.DataFrame() 

        for index, val in all_results.iterrows(): #itterrows, also DF Methoden verwenden, damit es funktioniert!
            if val["doc_id"] in doc_type_selection["doc_id"].values:
                # Vertikales Anhängen der result DataFrames
                combined_result = pd.concat([combined_result, val["result"]], ignore_index=True)

        combined_results_by_type.append((doc_type, pd.DataFrame(combined_result)))  # Tuple mit doc_type und combined_result

    ai_dataframes = []

    for doc_type, combined_result in combined_results_by_type:
        all_positions = []
        # Prüfen, ob die Spalte 'Positionen' vorhanden und nicht leer ist
        if 'positionen' in combined_result.columns and combined_result['positionen'].notna().any():
            for index, row in combined_result.iterrows():
                positionen = row['positionen']
                # invoice_id = row['invoice_id']  # Rechnungs-ID für die Verknüpfung
                # vendor_name = row['vendor_name'] 
                # customer_name = row['customer_name'] 
                parent_id = row[f"{doc_type}_ID"]

                # Für jede Position eine Zeile mit der Rechnungs-ID hinzufügen
                if positionen:  # Nur wenn Positionen vorhanden sind
                    for position in positionen:
                        #position_with_id = {"invoice_id": invoice_id, "vendor_name": vendor_name, "customer_name": customer_name, **position, "parent_id":parent_id}
                        position_with_id = {f"{doc_type}_ID":parent_id, **position, }  # Füge die Rechnungs-ID hinzu
                        all_positions.append(position_with_id)

        st.subheader(f"Vorschau für {doc_type}:")
        # Wahrscheinlichkeitsspalten ausblenden
        combined_result_cleaned = combined_result.loc[:, ~combined_result.columns.str.contains('_confidence')]
        # Alle Spalten außer "positionen" auswählen
        # DIe Positionen werden ja zuvor aufgeschlüsselt und in einem eigenne Dataframe zusammengefasst, daher knnen die hier raus
        # da diese sonst nur zu format fehlern führen können
        combined_result_cleaned = combined_result_cleaned.loc[:, combined_result_cleaned.columns != 'positionen']

        st.dataframe(combined_result_cleaned)
        ai_dataframes.append(pd.DataFrame(combined_result_cleaned))

        st.write(f"Positionen:")
        # Alle Positionen in ein einziges DataFrame umwandeln
        if all_positions:
            all_positions_df = pd.DataFrame(all_positions)
            # Wahrscheinlichkeitsspalten ausblenden
            all_positions_df_without_confidence = all_positions_df.loc[:, ~all_positions_df.columns.str.contains('_confidence')]
            st.dataframe(all_positions_df_without_confidence)
            ai_dataframes.append(pd.DataFrame(all_positions_df_without_confidence))
        else:
            st.write("Keine Positionen vorhanden.")

    if ai_dataframes:
        if st.button("Öffne AI Analyse Chat", type="primary"):
            st.session_state.ai_object = ai_dataframes  
            st.session_state.messages = []
            st.switch_page("subPages/panAI.py")
    else:
        st.warning("Auswählen welche Daten analysiert werden sollen (links von der Tabelle).")
else:
    st.markdown("Noch keine Daten vorhanden ...")