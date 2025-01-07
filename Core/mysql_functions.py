import mysql.connector
import streamlit as st
import pandas as pd
from mysql.connector import errorcode
from datetime import datetime

def test_db_connection():
    try:
        connection = mysql.connector.connect(
            host=st.secrets["db_host"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            database=st.secrets["db_name"]
        )

        if connection.is_connected():
            st.success("Verbindung zur Datenbank erfolgreich!")
            connection.close()
        else:
            st.error("Verbindung zur Datenbank fehlgeschlagen.")
    except mysql.connector.Error as err:
        # st.error(f"Fehler bei der Verbindung zur Datenbank: {err}")
        st.error(f"Fehler bei der Verbindung zur Datenbank.")


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=st.secrets["db_host"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            database=st.secrets["db_name"]
        )
        return connection
    except mysql.connector.Error as err:
        return None


def execute_query(query, params=None, as_dataframe=False):
    connection = get_db_connection()
    if connection is None:
        return None, errorcode.CR_SERVER_GONE_ERROR  # Verbindung nicht hergestellt

    try:
        cursor = connection.cursor(dictionary=True)

        if query.strip().upper().startswith('SELECT'):
            cursor.execute(query, params)
            result = cursor.fetchall()

            # Debug-Ausgabe

            if as_dataframe:
                df_result = pd.DataFrame(result)
                return df_result, None
            else:
                return result, None

        else:
            cursor.execute(query, params)
            connection.commit()

            return cursor.rowcount, None

    except mysql.connector.Error as err:
        # Fehlercode zurückgeben
        return None, err.errno

    finally:
        cursor.close()
        connection.close()


def execute_transaction(queries, params_list):
    connection = get_db_connection()
    if connection is None:
        return None, errorcode.CR_SERVER_GONE_ERROR  # Verbindung nicht hergestellt

    try:
        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()

        for query, params in zip(queries, params_list):
            cursor.execute(query, params)

        connection.commit()
        return cursor.rowcount, None

    except mysql.connector.Error as err:
        connection.rollback()  # Rollback bei Fehler
        return None, err.errno

    finally:
        cursor.close()
        connection.close()

# Bsp.:
#  # Benutzerdefinierte Abfrage
#     with st.form(key='query_form'):
#         query = st.text_area("Geben Sie Ihre SQL-Abfrage ein:")
#         params_input = st.text_input("Geben Sie Parameter ein (durch Kommas getrennt):")
#         submit_button = st.form_submit_button(label='Abfrage ausführen')

#     if submit_button:
#         params = tuple(params_input.split(',')) if params_input else None
#         result, error_code = execute_query(query, params=params, as_dataframe=True)

#         if error_code:
#             st.error(f"Fehlercode: {error_code}")

#             if error_code == errorcode.ER_DUP_ENTRY:
#                 # Beispiel: Benutzer kann eine andere Abfrage versuchen
#                 st.write("Versuchen Sie eine andere Abfrage oder korrigieren Sie die vorhandene.")
#                 # Weitere Aktionen oder eine andere Abfrage
#                 # Example: Alternative Insert Query
#                 alternative_query = "INSERT INTO your_table (username) VALUES (%s)"
#                 alternative_params = ('alternative_user',)
#                 affected_rows, alt_error_code = execute_query(alternative_query, params=alternative_params)
#                 if alt_error_code:
#                     st.error(f"Fehlercode: {alt_error_code}")
#                 else:
#                     st.write(f"Anzahl der eingefügten Zeilen: {affected_rows}")

#         else:
#             if result is not None and not result.empty:
#                 st.write("Abfrageergebnisse:")
#                 st.write(result)
#             else:
#                 st.write("Keine Daten gefunden oder Abfrage erfolgreich ohne Rückgabewerte.")

def save_to_database(uploaded_data, user_id):
    """
    Speichert die hochgeladenen Daten (Rechnungen, Kassenbons) in die Datenbank.
    Für die Datenbank werden eigene IDs herangezogen.
    Falls die Dataframes gedownloadet werden, können die von der App zugewiesenen nützlich sein.

    :param uploaded_data: Eine Liste von Dictionaries mit den Ergebnissen der Verarbeitung
    :param user_id: ID des Benutzers, der die Daten hochgeladen hat
    :return: True bei Erfolg, False bei Fehler
    """
    queries = []
    params_list = []

    # Metadaten speichern
    for doc_idx, doc_row in uploaded_data.iterrows():
        file_name = doc_row['file_name']
        file_type = doc_row['file_type']
        doc_type = doc_row['doc_type']
        doc_type_confidence = doc_row['doc_type_confidence']
        successful = doc_row['successful']
        created_at = datetime.now()

        # Haupt-Metadaten-Insert
        queries.append(
            """
            INSERT INTO documents (user_id, file_name, file_type, doc_type, doc_type_confidence, successful, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
        )
        params_list.append(
            (user_id, file_name, file_type, doc_type, doc_type_confidence, successful, created_at))

        # Ergebnisse (Rechnungen oder Kassenbons) speichern
        for res_idx, res_row in doc_row['result'].iterrows():
            if doc_type == "Rechnung":
                queries.append(
                    """
                    INSERT INTO Invoices (
                        doc_id, invoice_id, vendor_name, vendor_name_confidence, vendor_address,
                        vendor_address_confidence, customer_name, customer_name_confidence, customer_id,
                        customer_id_confidence, invoice_date, invoice_date_confidence, invoice_total,
                        invoice_total_confidence, subtotal, subtotal_confidence, total_tax, total_tax_confidence,
                        due_date, due_date_confidence, purchase_order, purchase_order_confidence, billing_address,
                        billing_address_confidence, shipping_address, shipping_address_confidence, amount_due, amount_due_confidence
                    ) VALUES (
                        LAST_INSERT_ID(), %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """
                )
                params_list.append((
                    res_row['invoice_id'], res_row['vendor_name'],
                    res_row['vendor_name_confidence'], res_row['vendor_address'], res_row['vendor_address_confidence'],
                    res_row['customer_name'], res_row['customer_name_confidence'], res_row['customer_id'],
                    res_row['customer_id_confidence'], res_row['invoice_date'], res_row['invoice_date_confidence'],
                    res_row['invoice_total_clean'], res_row['invoice_total_confidence'], res_row['subtotal_clean'],
                    res_row['subtotal_confidence'], res_row['total_tax_clean'], res_row['total_tax_confidence'],
                    res_row['due_date'], res_row['due_date_confidence'], res_row['purchase_order'],
                    res_row['purchase_order_confidence'], res_row['billing_address'],
                    res_row['billing_address_confidence'], res_row['shipping_address'],
                    res_row['shipping_address_confidence'], res_row['amount_due'], res_row['amount_due_confidence']
                ))

                # Positionen der Rechnung einfügen
                if 'positionen' in res_row: # Enumerate nach Prüfung, da Positionen kein DF sondern Liste / Dictionary sind ... Alternative wäre umwandeln in DF
                    for pos_idx, pos_row in enumerate(res_row['positionen']):
                        queries.append(
                            """
                            INSERT INTO InvoiceItems (
                                invoice_base_id, item_description, item_description_confidence, item_quantity, 
                                item_quantity_confidence, unit, unit_confidence, unit_price, 
                                unit_price_confidence, unit_price_code, product_code, 
                                product_code_confidence, item_date, item_date_confidence, tax, tax_confidence, 
                                amount, amount_confidence, amount_clean
                            ) VALUES (
                                LAST_INSERT_ID(), %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            """
                        )
                        params_list.append((
                            pos_row['item_description'], pos_row['item_description_confidence'],
                            pos_row['item_quantity'], pos_row['item_quantity_confidence'], pos_row['unit'],
                            pos_row['unit_confidence'], pos_row['unit_price'], pos_row['unit_price_confidence'],
                            pos_row['unit_price_code'], pos_row['product_code'], pos_row['product_code_confidence'],
                            pos_row['item_date'], pos_row['item_date_confidence'], pos_row['tax'],
                            pos_row['tax_confidence'], pos_row['amount'], pos_row['amount_confidence'],
                            pos_row['amount_clean']
                        ))


            # elif doc_type == "Kassenbon":
            #     queries.append(
            #         """
            #         INSERT INTO receipts (receipt_id, doc_id, merchant_name, transaction_date, total, created_at)
            #         VALUES (%s, %s, %s, %s, %s, %s)
            #         """
            #     )
            #     params_list.append((
            #         result[f"{doc_type}_ID"],
            #         doc_id,
            #         result["merchant_name"],
            #         result["transaction_date"],
            #         result["total_clean"],
            #         created_at
            #     ))
            #
            #     # Positionen des Kassenbons einfügen
            #     for position in result.get("positionen", []):
            #         queries.append(
            #             """
            #             INSERT INTO receipt_items (receipt_id, item_description, item_quantity, individual_item_price, total_item_price, created_at)
            #             VALUES (%s, %s, %s, %s, %s, %s)
            #             """
            #         )
            #         params_list.append((
            #             result[f"{doc_type}_ID"],
            #             position["item_description"],
            #             position["item_quantity"],
            #             position["individual_item_price_clean"],
            #             position["total_item_price_clean"],
            #             created_at
            #         ))

    # Transaktion ausführen
    rowcount, error = execute_transaction(queries, params_list)
    if error:
        print(f"Fehler beim Speichern in die Datenbank: {error}")
        return False
    return True