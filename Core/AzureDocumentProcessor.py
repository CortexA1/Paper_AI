import pandas as pd
import time
import re
from uuid import uuid4
from datetime import datetime
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF

#
# Noch nicht getestet:
# => Idenitiy (modell für klassifizierung trainieren)
# => Kreditkarte (modell für klassifizierung trainieren)
# 
# Fall: Mehrere Typen in einem Dokument, z.B. 3x Rechnung und 1x Kreditkarte (Was passiert dann?)
#



def compress_image(image_bytes, quality=75, max_size=(2000, 2000)):
    """
    Komprimiert ein Bild, konvertiert es zu RGB (falls nötig) und reduziert Größe bei guter Qualität.
    """
    image = Image.open(BytesIO(image_bytes))

    # Falls das Bild Transparenz hat (z. B. PNG), konvertieren wir es in RGB
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # Falls das Bild zu groß ist, skalieren wir es herunter
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Komprimieren und speichern als JPEG
    output = BytesIO()
    image.save(output, format="JPEG", quality=quality, optimize=True)
    return output.getvalue()

def compress_pdf(pdf_bytes):
    """
    Komprimiert ein PDF mit PyMuPDF, reduziert Bilder und optimiert Speicherplatz.
    """
    input_pdf = fitz.open("pdf", pdf_bytes)
    output = BytesIO()

    # Speichert das PDF mit Kompression
    input_pdf.save(output, garbage=4, deflate=True)
    return output.getvalue()

class AzureDocumentProcessor:
    def __init__(self, endpoint, key, classifier_id):
        # Initialisierung des Azure Clients mit dem neuen Document Intelligence SDK
        self.client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        self.classifier_id = classifier_id

    def classify_document(self, bytes_data):
        """
        Klassifiziere das Dokument basierend auf dem Byte-Stream.
        """
        poller = self.client.begin_classify_document(self.classifier_id, AnalyzeDocumentRequest(bytes_source=bytes_data))
        result = poller.result()
        for doc in result.documents:
            if doc.confidence < 0.25: #25 Prozent sind minimum, ansonsten wurde schrott hochgeladen
                return "Unbekannt", doc.confidence
            else:
                # print(f"Dokumenttyp erkannt: '{doc.doc_type}' mit {doc.confidence * 100}% Vertrauen")
                return doc.doc_type, doc.confidence  # Den erkannten Dokumenttyp zurückgeben

    def analyze_identity_doc(self, bytes_data, file_name, doc_type):
        """
        Analysiere ein Dokument vom Typ 'Identity' mit Azure Document Intelligence.
        """
        poller = self.client.begin_analyze_document("prebuilt-idDocument",
                                                    AnalyzeDocumentRequest(bytes_source=bytes_data))
        id_documents = poller.result()

        result = []
        if id_documents.documents:
            for idx, id_document in enumerate(id_documents.documents):
                # Basisinformationen des ID-Dokuments sammeln
                id_document_result = {
                    f"{doc_type}_ID": (file_name + "_" + datetime.now().strftime('%f')[:6]).lower(),
                    # Am Ende noch die millisekunden nutzen für die ID
                    "first_name": id_document.fields.get("FirstName").get('value') if id_document.fields.get(
                        "FirstName") else None,
                    "first_name_confidence": id_document.fields.get("FirstName").get(
                        'confidence') if id_document.fields.get("FirstName") else None,
                    "last_name": id_document.fields.get("LastName").get('value') if id_document.fields.get(
                        "LastName") else None,
                    "last_name_confidence": id_document.fields.get("LastName").get(
                        'confidence') if id_document.fields.get("LastName") else None,
                    "document_number": id_document.fields.get("DocumentNumber").get('value') if id_document.fields.get(
                        "DocumentNumber") else None,
                    "document_number_confidence": id_document.fields.get("DocumentNumber").get(
                        'confidence') if id_document.fields.get("DocumentNumber") else None,
                    "dob": id_document.fields.get("DateOfBirth").get('value') if id_document.fields.get(
                        "DateOfBirth") else None,
                    "dob_confidence": id_document.fields.get("DateOfBirth").get('confidence') if id_document.fields.get(
                        "DateOfBirth") else None,
                    "doe": id_document.fields.get("DateOfExpiration").get('value') if id_document.fields.get(
                        "DateOfExpiration") else None,
                    "doe_confidence": id_document.fields.get("DateOfExpiration").get(
                        'confidence') if id_document.fields.get("DateOfExpiration") else None,
                    "sex": id_document.fields.get("Sex").get('value') if id_document.fields.get("Sex") else None,
                    "sex_confidence": id_document.fields.get("Sex").get('confidence') if id_document.fields.get(
                        "Sex") else None,
                    "address": id_document.fields.get("Address").get('value') if id_document.fields.get(
                        "Address") else None,
                    "address_confidence": id_document.fields.get("Address").get('confidence') if id_document.fields.get(
                        "Address") else None,
                    "country_region": id_document.fields.get("CountryRegion").get('value') if id_document.fields.get(
                        "CountryRegion") else None,
                    "country_region_confidence": id_document.fields.get("CountryRegion").get(
                        'confidence') if id_document.fields.get("CountryRegion") else None,
                    "region": id_document.fields.get("Region").get('value') if id_document.fields.get(
                        "Region") else None,
                    "region_confidence": id_document.fields.get("Region").get('confidence') if id_document.fields.get(
                        "Region") else None
                }

                # Das Ergebnis in die Ergebnisliste hinzufügen
                result.append(id_document_result)

        # Rückgabe als DataFrame für bessere tabellarische Darstellung
        return pd.DataFrame(result)

    def analyze_receipt(self, bytes_data, file_name, doc_type):
        """
        Analysiere ein Dokument vom Typ 'Kassenbon' mit Azure Document Intelligence.
        """
        poller = self.client.begin_analyze_document("prebuilt-receipt", AnalyzeDocumentRequest(bytes_source=bytes_data))
        receipts = poller.result()

        result = []
        if receipts.documents:
            for idx, receipt in enumerate(receipts.documents):
                # Basisinformationen des Kassenbons sammeln
                receipt_base = {
                    f"{doc_type}_ID": (file_name + "_" + datetime.now().strftime('%f')[:6]).lower(),
                    # Am Ende noch die millisekunden nutzen für die ID
                    # "receipt_type": receipt.doc_type or None,
                    # "receipt_type_confidence": getattr(receipt, 'confidence', None),  # Prüfen auf das Vorhandensein des Attributes
                    "merchant_name": receipt.fields.get("MerchantName").get('content') if receipt.fields.get(
                        "MerchantName") else None,
                    "merchant_name_confidence": receipt.fields.get("MerchantName").get(
                        'confidence') if receipt.fields.get("MerchantName") else None,
                    "transaction_date": receipt.fields.get("TransactionDate").get('content') if receipt.fields.get(
                        "TransactionDate") else None,
                    "transaction_date_confidence": receipt.fields.get("TransactionDate").get(
                        'confidence') if receipt.fields.get("TransactionDate") else None,
                    "subtotal": receipt.fields.get("Subtotal").get('content') if receipt.fields.get(
                        "Subtotal") else None,
                    "subtotal_confidence": receipt.fields.get("Subtotal").get('confidence') if receipt.fields.get(
                        "Subtotal") else None,
                    "subtotal_clean": receipt.fields.get("Subtotal") and self.convert_currency_to_float(
                        receipt.fields.get("Subtotal").get('content')) or None,
                    "total_tax": receipt.fields.get("TotalTax").get('content') if receipt.fields.get(
                        "TotalTax") else None,
                    "total_tax_confidence": receipt.fields.get("TotalTax").get('confidence') if receipt.fields.get(
                        "TotalTax") else None,
                    "total_tax_clean": receipt.fields.get("TotalTax") and self.convert_currency_to_float(
                        receipt.fields.get("TotalTax").get('content')) or None,
                    "tip": receipt.fields.get("Tip").get('content') if receipt.fields.get("Tip") else None,
                    "tip_confidence": receipt.fields.get("Tip").get('confidence') if receipt.fields.get(
                        "Tip") else None,
                    "total": receipt.fields.get("Total").get('content') if receipt.fields.get("Total") else None,
                    "total_confidence": receipt.fields.get("Total").get('confidence') if receipt.fields.get(
                        "Total") else None,
                    "total_clean": receipt.fields.get("Total") and self.convert_currency_to_float(
                        receipt.fields.get("Total").get('content')) or None,
                    "positionen": []  # Platzhalter für Positionen
                }

                # Positionen sammeln
                if receipt.fields.get("Items") and receipt.fields.get("Items").get("valueArray"):
                    for item in receipt.fields.get("Items").get("valueArray"):
                        item_data = item.get("valueObject", {})

                        receipt_result_item = {
                            "item_description": item_data.get("Description").get('content') if item_data.get(
                                "Description") else None,
                            "item_description_confidence": item_data.get("Description").get(
                                'confidence') if item_data.get("Description") else None,
                            "item_quantity": item_data.get("Quantity").get('content') if item_data.get(
                                "Quantity") else None,
                            "item_quantity_confidence": item_data.get("Quantity").get('confidence') if item_data.get(
                                "Quantity") else None,
                            "individual_item_price": item_data.get("Price").get('content') if item_data.get(
                                "Price") else None,
                            "individual_item_price_confidence": item_data.get("Price").get(
                                'confidence') if item_data.get("Price") else None,
                            "individual_item_price_clean": item_data.get("Price") and self.convert_currency_to_float(
                                item_data.get("Price").get('content')) or None,
                            "total_item_price": item_data.get("TotalPrice").get('content') if item_data.get(
                                "TotalPrice") else None,
                            "total_item_price_confidence": item_data.get("TotalPrice").get(
                                'confidence') if item_data.get("TotalPrice") else None,
                            "total_item_price_clean": item_data.get("TotalPrice") and self.convert_currency_to_float(
                                item_data.get("TotalPrice").get('content')) or None

                        }

                        # Positionen zur Liste im Basis-Dictionary hinzufügen
                        receipt_base["positionen"].append(receipt_result_item)

                # Basisdaten mit Positionen als eine Zeile hinzufügen
                result.append(receipt_base)

        # Rückgabe als DataFrame für bessere tabellarische Darstellung
        return pd.DataFrame(result)

    def analyze_invoice(self, bytes_data, file_name, doc_type):
        """
        Analysiere ein Dokument vom Typ 'Rechnung' mit Azure Document Intelligence.
        """
        poller = self.client.begin_analyze_document("prebuilt-invoice", AnalyzeDocumentRequest(bytes_source=bytes_data))
        invoices = poller.result()

        result = []
        if invoices.documents:
            for idx, invoice in enumerate(invoices.documents):
                # Basisinformationen der Rechnung sammeln / Reihenfolge angepasst!
                invoice_base = {
                    f"{doc_type}_ID": ((invoice.fields.get("InvoiceId") and invoice.fields.get("InvoiceId").get(
                        'content') or None) + "_" + file_name + "_" + datetime.now().strftime('%f')[:6]).lower(),
                    # Am Ende noch die millisekunden nutzen für die ID
                    "invoice_id": invoice.fields.get("InvoiceId") and invoice.fields.get("InvoiceId").get(
                        'content') or None,
                    "vendor_name": invoice.fields.get("VendorName") and invoice.fields.get("VendorName").get(
                        'content') or None,
                    "vendor_name_confidence": invoice.fields.get("VendorName") and invoice.fields.get("VendorName").get(
                        'confidence') or None,
                    "vendor_address": invoice.fields.get("VendorAddress") and invoice.fields.get("VendorAddress").get(
                        'content') or None,
                    "vendor_address_confidence": invoice.fields.get("VendorAddress") and invoice.fields.get(
                        "VendorAddress").get('confidence') or None,
                    "vendor_address_recipient": invoice.fields.get("VendorAddressRecipient") and invoice.fields.get(
                        "VendorAddressRecipient").get('content') or None,
                    "vendor_address_recipient_confidence": invoice.fields.get(
                        "VendorAddressRecipient") and invoice.fields.get("VendorAddressRecipient").get(
                        'confidence') or None,
                    "customer_name": invoice.fields.get("CustomerName") and invoice.fields.get("CustomerName").get(
                        'content') or None,
                    "customer_name_confidence": invoice.fields.get("CustomerName") and invoice.fields.get(
                        "CustomerName").get('confidence') or None,
                    "customer_id": invoice.fields.get("CustomerId") and invoice.fields.get("CustomerId").get(
                        'content') or None,
                    "customer_id_confidence": invoice.fields.get("CustomerId") and invoice.fields.get("CustomerId").get(
                        'confidence') or None,
                    "customer_address": invoice.fields.get("CustomerAddress") and invoice.fields.get(
                        "CustomerAddress").get('content') or None,
                    "customer_address_confidence": invoice.fields.get("CustomerAddress") and invoice.fields.get(
                        "CustomerAddress").get('confidence') or None,
                    "customer_address_recipient": invoice.fields.get("CustomerAddressRecipient") and invoice.fields.get(
                        "CustomerAddressRecipient").get('content') or None,
                    "customer_address_recipient_confidence": invoice.fields.get(
                        "CustomerAddressRecipient") and invoice.fields.get("CustomerAddressRecipient").get(
                        'confidence') or None,
                    "invoice_id_confidence": invoice.fields.get("InvoiceId") and invoice.fields.get("InvoiceId").get(
                        'confidence') or None,
                    "invoice_date": invoice.fields.get("InvoiceDate") and invoice.fields.get("InvoiceDate").get(
                        'content') or None,
                    "invoice_date_confidence": invoice.fields.get("InvoiceDate") and invoice.fields.get(
                        "InvoiceDate").get('confidence') or None,
                    "invoice_total": invoice.fields.get("InvoiceTotal") and invoice.fields.get("InvoiceTotal").get(
                        'content') or None,
                    "invoice_total_confidence": invoice.fields.get("InvoiceTotal") and invoice.fields.get(
                        "InvoiceTotal").get('confidence') or None,
                    "invoice_total_clean": invoice.fields.get("InvoiceTotal") and self.convert_currency_to_float(
                        invoice.fields.get("InvoiceTotal").get('content')) or None,
                    "due_date": invoice.fields.get("DueDate") and invoice.fields.get("DueDate").get('content') or None,
                    "due_date_confidence": invoice.fields.get("DueDate") and invoice.fields.get("DueDate").get(
                        'confidence') or None,
                    "purchase_order": invoice.fields.get("PurchaseOrder") and invoice.fields.get("PurchaseOrder").get(
                        'content') or None,
                    "purchase_order_confidence": invoice.fields.get("PurchaseOrder") and invoice.fields.get(
                        "PurchaseOrder").get('confidence') or None,
                    "billing_address": invoice.fields.get("BillingAddress") and invoice.fields.get(
                        "BillingAddress").get('content') or None,
                    "billing_address_confidence": invoice.fields.get("BillingAddress") and invoice.fields.get(
                        "BillingAddress").get('confidence') or None,
                    "shipping_address": invoice.fields.get("ShippingAddress") and invoice.fields.get(
                        "ShippingAddress").get('content') or None,
                    "shipping_address_confidence": invoice.fields.get("ShippingAddress") and invoice.fields.get(
                        "ShippingAddress").get('confidence') or None,
                    "subtotal": invoice.fields.get("SubTotal") and invoice.fields.get("SubTotal").get(
                        'content') or None,
                    "subtotal_confidence": invoice.fields.get("SubTotal") and invoice.fields.get("SubTotal").get(
                        'confidence') or None,
                    "subtotal_clean": invoice.fields.get("SubTotal") and self.convert_currency_to_float(
                        invoice.fields.get("SubTotal").get('content')) or None,
                    "total_tax": invoice.fields.get("TotalTax") and invoice.fields.get("TotalTax").get(
                        'content') or None,
                    "total_tax_confidence": invoice.fields.get("TotalTax") and invoice.fields.get("TotalTax").get(
                        'confidence') or None,
                    "total_tax_clean": invoice.fields.get("TotalTax") and self.convert_currency_to_float(
                        invoice.fields.get("TotalTax").get('content')) or None,
                    "amount_due": invoice.fields.get("AmountDue") and invoice.fields.get("AmountDue").get(
                        'content') or None,
                    "amount_due_confidence": invoice.fields.get("AmountDue") and invoice.fields.get("AmountDue").get(
                        'confidence') or None,
                    "positionen": []  # Platzhalter, falls es keine Positionen gibt
                }

                # Positionen der Rechnung in die Positionen-Liste sammeln
                if invoice.fields.get("Items") and invoice.fields.get("Items").get("valueArray"):
                    for item in invoice.fields.get("Items").get("valueArray"):
                        invoice_result_position = {
                            "item_description": item.get("valueObject").get("Description") and item.get(
                                "valueObject").get("Description").get('content') or None,
                            "item_description_confidence": item.get("valueObject").get("Description") and item.get(
                                "valueObject").get("Description").get('confidence') or None,
                            "item_quantity": item.get("valueObject").get("Quantity") and item.get("valueObject").get(
                                "Quantity").get('content') or None,
                            "item_quantity_confidence": item.get("valueObject").get("Quantity") and item.get(
                                "valueObject").get("Quantity").get('confidence') or None,
                            "unit": item.get("valueObject").get("unit") and item.get("valueObject").get("unit").get(
                                'content') or None,
                            "unit_confidence": item.get("valueObject").get("unit") and item.get("valueObject").get(
                                "unit").get('confidence') or None,
                            "unit_price": item.get("valueObject").get("UnitPrice") and item.get("valueObject").get(
                                "UnitPrice").get('content') or None,
                            "unit_price_confidence": item.get("valueObject").get("UnitPrice") and item.get(
                                "valueObject").get("UnitPrice").get('confidence') or None,
                            "unit_price_code": item.get("valueObject").get("UnitPrice") and item.get("valueObject").get(
                                "UnitPrice").get("valueCurrency").get("currencyCode") or None,
                            "product_code": item.get("valueObject").get("ProductCode") and item.get("valueObject").get(
                                "ProductCode").get('content') or None,
                            "product_code_confidence": item.get("valueObject").get("ProductCode") and item.get(
                                "valueObject").get("ProductCode").get('confidence') or None,
                            "item_date": item.get("valueObject").get("Date") and item.get("valueObject").get(
                                "Date").get('content') or None,
                            "item_date_confidence": item.get("valueObject").get("Date") and item.get("valueObject").get(
                                "Date").get('confidence') or None,
                            "tax": item.get("valueObject").get("Tax") and item.get("valueObject").get("Tax").get(
                                'content') or None,
                            "tax_confidence": item.get("valueObject").get("Tax") and item.get("valueObject").get(
                                "Tax").get('confidence') or None,
                            "amount": item.get("valueObject").get("Amount") and item.get("valueObject").get(
                                "Amount").get('content') or None,
                            "amount_confidence": item.get("valueObject").get("Amount") and item.get("valueObject").get(
                                "Amount").get('confidence') or None,
                            "amount_clean": item.get("valueObject").get("Amount") and self.convert_currency_to_float(
                                item.get("valueObject").get("Amount").get('content')) or None
                        }
                        # Füge Position zur Liste hinzu
                        invoice_base["positionen"].append(invoice_result_position)

                # Ergebnisliste füllen
                result.append(invoice_base)

        # Rückgabe als DataFrame für bessere tabellarische Darstellung
        return pd.DataFrame(result)

    def analyze_with_azure(self, bytes_data, doc_type, file_name):
        """
        Wähle die korrekte Azure-Analyse-Methode basierend auf dem Dokumententyp.
        """
        if doc_type == "Rechnung":
            return self.analyze_invoice(bytes_data, file_name, doc_type)
        elif doc_type == "Kassenbon":
            return self.analyze_receipt(bytes_data, file_name, doc_type)
        elif doc_type == "Identity":
            return self.analyze_identity_doc(bytes_data, file_name, doc_type)
        else:
            # Typ "Unbekannt"
            return pd.DataFrame([{"error": f"Dokumenttyp '{doc_type}' wird nicht unterstützt."}])

    def convert_currency_to_float(self, currency_str):
        """
        Konvertiere eine Währungszeichenkette in eine Fließkommazahl.
        Entfernt das Tausendertrennzeichen und übernimmt das Dezimaltrennzeichen.
        Rundet auf zwei Dezimalstellen, wenn Nachkommastellen vorhanden sind.
        """
        # Regulärer Ausdruck, um nur den numerischen Teil und das Dezimaltrennzeichen zu erfassen
        pattern = r'[\d.,]+'

        match = re.search(pattern, currency_str)
        if match:
            value_str = match.group(0)

            # Falls Komma als Dezimaltrennzeichen vorhanden ist, entferne nur Tausenderpunkte
            if ',' in value_str:
                clean_str = value_str.replace(".", "").replace(",", ".")
            else:
                # Andernfalls, wenn Punkt Dezimaltrennzeichen ist, entferne Kommas
                clean_str = value_str.replace(",", "")

            try:
                # Konvertiere in Float und runde, falls Nachkommastellen existieren
                value = float(clean_str)
                return round(value, 2) if value % 1 != 0 else int(value)
            except ValueError:
                return None

        return None

    def process_upload(self, uploaded_file):
        """
        Hauptmethode, um eine hochgeladene Datei zu analysieren. 
        Identifiziert den Dateityp und führt die entsprechende Analyse durch.
        """

        result = None  # Variable für das Ergebnis initialisieren
        doc_type = "-"
        doc_type_confidence = 1.00
        file_type = uploaded_file.type  # Bestimme den MIME-Typ
        file_name = uploaded_file.name

        try:

            # CSV
            if file_type == "text/csv":
                doc_type = "csv"
                doc_type_confidence = 1.00
                result = pd.read_csv(uploaded_file)

            # Excel (XLSX und XLS)
            # Kann man noch weiter entwickeln zB in Bezug auf Sheets
            elif file_type in [
                "application/vnd.ms-excel"
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ]:
                doc_type = "excel"
                doc_type_confidence = 1.00
                result = pd.read_excel(uploaded_file)

            # Bilder (JPEG, PNG, BMP) und PDF
            elif file_type in ["image/jpeg", "image/png", "image/bmp", "application/pdf"]:
                bytes_data = uploaded_file.read()

                # Komprimierung für Bilder oder PDFs
                if file_type in ["image/jpeg", "image/png", "image/bmp"]:
                    bytes_data = compress_image(bytes_data, quality=75)
                elif file_type == "application/pdf":
                    bytes_data = compress_pdf(bytes_data)

                doc_type, doc_type_confidence = self.classify_document(bytes_data)
                result = self.analyze_with_azure(bytes_data, doc_type, file_name)
            else:
                result = pd.DataFrame([{"error": "Nicht unterstützter Dateityp."}])

            # Rückgabe als Dictionary
            return {
                "doc_id": str(uuid4()),
                "file_name": file_name,
                "file_type": file_type,
                "doc_type": doc_type,
                "doc_type_confidence": doc_type_confidence,
                "result": result,
                "successful": 1
                # Datei speichern? Testen ob man das uploaded_file Objekt nochmal lesen kann
            }

        except Exception as e:
            return {
                "doc_id": str(uuid4()),
                "file_name": file_name,
                "file_type": file_type,
                "doc_type": doc_type,
                "doc_type_confidence": doc_type_confidence,
                "result": str(e),
                "successful": 0
                # Datei speichern? Testen ob man das uploaded_file Objekt nochmal lesen kann
            }
