#
# Dies war ein Versuch mit AI den Code umzuwandeln, sodass SQLALchemy genutzt wird
# Hab es nie getestet, allerdings gefällt er mir auch nicht so
#
#

import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, text, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
import pandas as pd

# Create a SQLAlchemy engine
DATABASE_URL = f"mysql+pymysql://{st.secrets['db_user']}:{st.secrets['db_password']}@{st.secrets['db_host']}/{st.secrets['db_name']}"
engine = create_engine(DATABASE_URL)

def test_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            st.success("Connection to the database was successful!")
    except Exception as err:
        st.error(f"Error connecting to the database: {err}")

def execute_query(query, params=None, as_dataframe=False):
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params)

            if query.strip().upper().startswith('SELECT'):
                result_data = result.fetchall()
                if as_dataframe:
                    return pd.DataFrame(result_data), None
                return result_data, None
            else:
                return result.rowcount, None
    except Exception as err:
        return None, str(err)

def execute_transaction(queries, params_list):
    try:
        with engine.connect() as connection:
            with connection.begin():  # Automatically handles transaction
                for query, params in zip(queries, params_list):
                    connection.execute(text(query), params)
            return len(queries), None
    except Exception as err:
        return None, str(err)


Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    doc_id = Column(String)
    user_id = Column(Integer)
    file_name = Column(String)
    file_type = Column(String)
    doc_type = Column(String)
    doc_type_confidence = Column(Float)
    successful = Column(Integer)
    created_at = Column(DateTime)

class Invoice(Base):
    __tablename__ = 'Invoices'
    id = Column(Integer, primary_key=True)
    invoice_base_id = Column(String, ForeignKey('documents.doc_id'))
    doc_id = Column(String)
    invoice_id = Column(String)
    vendor_name = Column(String)
    vendor_name_confidence = Column(Float)
    vendor_address = Column(String)
    vendor_address_confidence = Column(Float)
    customer_name = Column(String)
    customer_name_confidence = Column(Float)
    customer_id = Column(String)
    customer_id_confidence = Column(Float)
    invoice_date = Column(DateTime)
    invoice_date_confidence = Column(Float)
    invoice_total = Column(Float)
    invoice_total_confidence = Column(Float)
    subtotal = Column(Float)
    subtotal_confidence = Column(Float)
    total_tax = Column(Float)
    total_tax_confidence = Column(Float)
    due_date = Column(DateTime)
    due_date_confidence = Column(Float)
    purchase_order = Column(String)
    purchase_order_confidence = Column(Float)
    billing_address = Column(String)
    billing_address_confidence = Column(Float)
    shipping_address = Column(String)
    shipping_address_confidence = Column(Float)
    amount_due = Column(Float)
    amount_due_confidence = Column(Float)

class InvoiceItem(Base):
    __tablename__ = 'InvoiceItems'
    id = Column(Integer, primary_key=True)
    invoice_base_id = Column(String, ForeignKey('Invoices.invoice_id'))
    item_description = Column(String)
    item_description_confidence = Column(Float)
    item_quantity = Column(Float)
    item_quantity_confidence = Column(Float)
    unit = Column(String)
    unit_confidence = Column(Float)
    unit_price = Column(Float)
    unit_price_confidence = Column(Float)
    unit_price_code = Column(String)
    product_code = Column(String)
    product_code_confidence = Column(Float)
    item_date = Column(DateTime)
    item_date_confidence = Column(Float)
    tax = Column(Float)
    tax_confidence = Column(Float)
    amount = Column(Float)
    amount_confidence = Column(Float)
    amount_clean = Column(Float)

def save_to_database(uploaded_data, user_id):
    """
    Saves the uploaded data (invoices, receipts) to the database.

    :param uploaded_data: A DataFrame containing the results of the processing
    :param user_id: ID of the user who uploaded the data
    :return: True on success, False on error
    """
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        for doc_idx, doc_row in uploaded_data.iterrows():
            document = Document(
                doc_id=doc_row['doc_id'],
                user_id=user_id,
                file_name=doc_row['file_name'],
                file_type=doc_row['file_type'],
                doc_type=doc_row['doc_type'],
                doc_type_confidence=doc_row['doc_type_confidence'],
                successful=doc_row['successful'],
                created_at=datetime.now()
            )
            session.add(document)
            session.flush()  # Ensure the document ID is available for the invoice

            for res_idx, res_row in doc_row['result'].iterrows():
                if doc_row['doc_type'] == "Rechnung":
                    invoice = Invoice(
                        invoice_base_id=res_row['Rechnung_ID'],
                        doc_id=doc_row['doc_id'],
                        invoice_id=res_row['invoice_id'],
                        vendor_name=res_row['vendor_name'],
                        vendor_name_confidence=res_row['vendor_name_confidence'],
                        vendor_address=res_row['vendor_address'],
                        vendor_address_confidence=res_row['vendor_address_confidence'],
                        customer_name=res_row['customer_name'],
                        customer_name_confidence=res_row['customer_name_confidence'],
                        customer_id=res_row['customer_id'],
                        customer_id_confidence=res_row['customer_id_confidence'],
                        invoice_date=res_row['invoice_date'],
                        invoice_date_confidence=res_row['invoice_date_confidence'],
                        invoice_total=res_row['invoice_total_clean'],
                        invoice_total_confidence=res_row['invoice_total_confidence'],
                        subtotal=res_row['subtotal_clean'],
                        subtotal_confidence=res_row['subtotal_confidence'],
                        total_tax=res_row['total_tax_clean'],
                        total_tax_confidence=res_row['total_tax_confidence'],
                        due_date=res_row['due_date'],
                        due_date_confidence=res_row['due_date_confidence'],
                        purchase_order=res_row['purchase_order'],
                        purchase_order_confidence=res_row['purchase_order_confidence'],
                        billing_address=res_row['billing_address'],
                        billing_address_confidence=res_row['billing_address_confidence'],
                        shipping_address=res_row['shipping_address'],
                        shipping_address_confidence=res_row['shipping_address_confidence'],
                        amount_due=res_row['amount_due'],
                        amount_due_confidence=res_row['amount_due_confidence']
                    )
                    session.add(invoice)
                    session.flush()  # Ensure the invoice ID is available for the invoice items

                    if 'positionen' in res_row:
                        for pos_row in res_row['positionen']:
                            invoice_item = InvoiceItem(
                                invoice_base_id=res_row['Rechnung_ID'],
                                item_description=pos_row['item_description'],
                                item_description_confidence=pos_row['item_description_confidence'],
                                item_quantity=pos_row['item_quantity'],
                                item_quantity_confidence=pos_row['item_quantity_confidence'],
                                unit=pos_row['unit'],
                                unit_confidence=pos_row['unit_confidence'],
                                unit_price=pos_row['unit_price'],
                                unit_price_confidence=pos_row['unit_price_confidence'],
                                unit_price_code=pos_row['unit_price_code'],
                                product_code=pos_row['product_code'],
                                product_code_confidence=pos_row['product_code_confidence'],
                                item_date=pos_row['item_date'],
                                item_date_confidence=pos_row['item_date_confidence'],
                                tax=pos_row['tax'],
                                tax_confidence=pos_row['tax_confidence'],
                                amount=pos_row['amount'],
                                amount_confidence=pos_row['amount_confidence'],
                                amount_clean=pos_row['amount_clean']
                            )
                            session.add(invoice_item)

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error saving to the database: {e}")
        return False
    finally:
        session.close()
