import altair as alt
import re
import pandas as pd
import numpy as np
from dateutil.parser import parse
from geopy.geocoders import Nominatim
import streamlit as st
import hashlib
from cryptography.fernet import Fernet


def convert_to_datetime(date_str):
    # Liste von bekannten Datumsformaten
    date_formats = [
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d.%m.%y",
        "%Y.%m.%d",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y"
    ]

    # Versuchen, das Datum mit verschiedenen Formaten zu parsen
    for fmt in date_formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            pass

    # Wenn alle bekannten Formate fehlschlagen, versuche dateutil.parser.parse
    try:
        return parse(date_str)
    except ValueError as e:
        # print(f"Fehler beim Parsen des Datums: {e}")
        return None


# Funktion zur Bereinigung und Umwandlung
def convert_currency_to_float(currency_str):
    # Entferne Währungssymbole und Leerzeichen
    cleaned_str = re.sub(r'[^\d.,]', '', currency_str)

    # Prüfe, ob das Format deutsch (Komma als Dezimalzeichen) oder englisch (Punkt als Dezimalzeichen) ist
    if ',' in cleaned_str and '.' in cleaned_str:
        if cleaned_str.rfind(',') > cleaned_str.rfind('.'):
            # Wenn das letzte Komma nach dem letzten Punkt steht, gehen wir davon aus, dass es das deutsche Format ist
            cleaned_str = cleaned_str.replace('.', '')
            cleaned_str = cleaned_str.replace(',', '.')
        else:
            # Andernfalls gehen wir davon aus, dass es das englische Format ist
            cleaned_str = cleaned_str.replace(',', '')
    elif ',' in cleaned_str:
        # Wenn nur Komma vorhanden ist, gehen wir vom deutschen Format aus
        cleaned_str = cleaned_str.replace(',', '.')
    elif '.' in cleaned_str:
        # Wenn nur Punkt vorhanden ist, gehen wir vom englischen Format aus
        cleaned_str = cleaned_str.replace(',', '')

    return float(cleaned_str)


def validate_form(fields_to_check=None, **kwargs):
    errors = []

    # Definition aller erforderlichen Felder und deren Fehlermeldungen
    required_fields = {
        'username': "Benutzername ist erforderlich.",
        'email': "E-Mail-Adresse ist erforderlich.",
        'password': "Passwort ist erforderlich.",
        'password_confirmation': "Passwortbestätigung ist erforderlich.",
        'firstname': "Vorname ist erforderlich.",
        'surename': "Nachname ist erforderlich.",
        'street': "Straße / Hausnummer ist erforderlich.",
        'postal_code': "Postleitzahl ist erforderlich.",
        'city': "Stadt ist erforderlich.",
        'country': "Land ist erforderlich.",
        'phonenumber': "Telefonnummer ist erforderlich."
    }

    # Wenn fields_to_check nicht angegeben oder leer ist, prüfe alle Felder
    if not fields_to_check:
        fields_to_check = required_fields.keys()

    # Überprüfe nur die Felder, die in fields_to_check angegeben sind
    for field in fields_to_check:
        if field in required_fields:
            if field not in kwargs or not kwargs[field]:
                errors.append(required_fields[field])

    # Zusätzliche Validierungen
    if 'email' in kwargs and kwargs.get('email') and not is_valid_email(kwargs['email']):
        errors.append("Die eingegebene E-Mail-Adresse ist ungültig.")

    if 'password' in kwargs and 'password_confirmation' in kwargs:
        if kwargs.get('password') != kwargs.get('password_confirmation'):
            errors.append("Passwörter stimmen nicht überein.")

    return errors


def is_valid_email(email):
    """Validate the email address using a regular expression."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# Funktion zum hashen (Einweg)
def auth_make_hashes(value):
    return hashlib.sha256(str.encode(str(value))).hexdigest()


# Verschlüssele die Nachricht
def encrypt_message(message, key):
    if not message:  # Überprüfen, ob die Nachricht leer ist
        return b''  # Leere Byte-Zeichenfolge zurückgeben
    f = Fernet(key)
    encrypted_message = f.encrypt(str(message).encode())
    return encrypted_message


# Entschlüssele die Nachricht
def decrypt_message(encrypted_message, key):
    if not encrypted_message:  # Überprüfen, ob die verschlüsselte Nachricht leer ist
        return ''  # Leeren String zurückgeben
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message)
    return decrypted_message.decode()


# Funktion zur Geokodierung
def geocode_address(address):
    try:
        if address.strip():  # Überprüfen, ob die Adresse nicht leer ist
            geolocator = Nominatim(user_agent="streamlit-geocoder")
            location = geolocator.geocode(address)
            if location:
                latitude = location.latitude
                longitude = location.longitude
                address_details = geolocator.reverse((latitude, longitude), exactly_one=True)
                address_dict = address_details.raw['address']
                city = address_dict.get('city', np.nan)
                state = address_dict.get('state', np.nan)
                country = address_dict.get('country', np.nan)
                return latitude, longitude, city, state, country
        return None, None, None, None, None  # Rückgabe von None, wenn Adresse ungültig oder leer ist
    except:
        return None, None, None, None, None  # Rückgabe von None, wenn Adresse ungültig oder leer ist


def geocode_address(address):
    """
    Geokodiert eine Adresse und gibt Breitengrad, Längengrad, Stadt, Bundesstaat und Land zurück,
    oder None für jeden Wert, wenn die Adresse ungültig ist oder nicht gefunden wurde.
    """
    if address.strip():  # Überprüfen, ob die Adresse nicht leer ist
        geolocator = Nominatim(user_agent="streamlit-geocoder")
        location = geolocator.geocode(address)
        if location:
            latitude = location.latitude
            longitude = location.longitude
            address_details = geolocator.reverse((latitude, longitude), exactly_one=True)
            address_dict = address_details.raw['address']
            city = address_dict.get('city', np.nan)
            state = address_dict.get('state', np.nan)
            country = address_dict.get('country', np.nan)
            return latitude, longitude, city, state, country
    return None, None, None, None, None


def process_dataframe(dataframe, columns_to_keep=None, amount_column=None, percentage_column_name=None,
                      drop_na_columns=None, geocode_column=None, date_column=None, aggregate_column_sum=None):
    """
    Kopiert ein DataFrame, behält nur die angegebenen Spalten, berechnet den prozentualen Anteil des Betrags
    auf Basis des gesamten DataFrames, entfernt Zeilen mit fehlenden Werten in bestimmten Spalten,
    führt Geokodierung durch und erstellt Jahr-, Monat- und Tag-Spalten aus einer Date-Spalte.

    Args:
    - dataframe (pd.DataFrame): Das ursprüngliche DataFrame.
    - columns_to_keep (list, optional): Liste der Spaltennamen, die behalten werden sollen. Standard ist None.
    - amount_column (str, optional): Der Name der Spalte, deren Betrag für die prozentuale Berechnung verwendet wird. Standard ist None.
    - percentage_column_name (str, optional): Der Name der neuen Spalte für den prozentualen Anteil. Standard ist None.
    - drop_na_columns (list or str, optional): Liste oder Name der Spalte, bei denen Zeilen mit NaN-Werten entfernt werden sollen. Standard ist None.
    - geocode_column (str, optional): Name der Spalte, die für die Geokodierung verwendet werden soll. Standard ist None.
    - date_column (str, optional): Name der Datums-Spalte, die in Datetime konvertiert werden und Jahr-, Monat- und Tag-Spalten erzeugen soll. Standard ist None.
    - aggregate_column_sum (str, optional): Name der Spalte, nach der summiert aggregiert werden soll. Standard ist None.

    Returns:
    - pd.DataFrame: Das verarbeitete DataFrame mit den angegebenen und neuen Spalten.
    """
    # Kopiere das DataFrame, um die ursprünglichen Daten nicht zu verändern
    processed_df = dataframe.copy()

    # Überprüfe und konvertiere drop_na_columns in eine Liste, falls es ein String ist
    if isinstance(drop_na_columns, str):
        drop_na_columns = [drop_na_columns]

    # Entferne Zeilen mit fehlenden Werten in den angegebenen Spalten, falls angegeben
    if drop_na_columns:
        processed_df = processed_df.dropna(subset=drop_na_columns)

    # Konvertiere die Date-Spalte zu Datetime und erstelle Jahr-, Monat- und Tag-Spalten, falls angegeben
    if date_column:
        processed_df[date_column] = pd.to_datetime(processed_df[date_column], format='%d.%m.%Y', errors='coerce')
        processed_df['year'] = processed_df[date_column].dt.year.astype('Int64')
        processed_df['month'] = processed_df[date_column].dt.month.astype('Int64')
        processed_df['day'] = processed_df[date_column].dt.day.astype('Int64')

        # Füge die Datums-Spalten zu columns_to_keep hinzu
        if columns_to_keep:
            columns_to_keep.extend(['year', 'month', 'day'])
        else:
            columns_to_keep = ['year', 'month', 'day']

    # Filtere das DataFrame auf die angegebenen Spalten, falls angegeben
    if columns_to_keep:
        existing_columns = [col for col in columns_to_keep if col in processed_df.columns]
        processed_df = processed_df[existing_columns]

    # Aggregiere das DataFrame nach der angegebenen Spalte und fasse die restlichen Spalten zusammen, falls angegeben
    if aggregate_column_sum:
        # Finde die Spalten, die nicht aggregiert werden sollen
        other_columns = [col for col in processed_df.columns if col != aggregate_column_sum]
        # Aggregiere die Spalte und fasse die restlichen Spalten zusammen
        processed_df = processed_df.groupby(other_columns, as_index=False)[aggregate_column_sum].sum()

    # Berechne den prozentualen Anteil des Betrags auf Basis des gesamten DataFrames, falls angegeben
    if amount_column and percentage_column_name:
        total_amount = processed_df[amount_column].sum()
        processed_df[percentage_column_name] = (processed_df[amount_column] / total_amount * 100).round(2)

    # Führe die Geokodierung durch, falls angegeben
    if geocode_column:
        processed_df[['latitude', 'longitude', 'city', 'state', 'country']] = processed_df[geocode_column].apply(
            lambda x: pd.Series(geocode_address(x)))

        # Nur gültige Koordinaten / Stadt / State behalten
        # processed_df = processed_df.dropna(subset=['latitude', 'longitude', 'city', 'state', 'country'])       

    # Entferne Duplikate im DataFrame, erst am Ende
    processed_df = processed_df.drop_duplicates()

    return processed_df


def create_altair_chart(data, mark_type='bar', x_field=None, y_field=None, x_title=None, y_title=None, color_field=None,
                        tooltip_fields=None):
    if mark_type == 'bar':
        chart = alt.Chart(data).mark_bar().encode(
            x=alt.X(f'{x_field}', title=x_title, sort='-y'),
            y=alt.Y(f'{y_field}', title=y_title),
            color=alt.Color(f'{color_field}', legend=None) if color_field else alt.value('steelblue'),
            tooltip=[alt.Tooltip(field[0], title=field[1]) for field in tooltip_fields] if tooltip_fields else []
        )
    elif mark_type == 'line':
        chart = alt.Chart(data).mark_line().encode(
            x=alt.X(f'{x_field}', title=x_title, sort='x'),
            y=alt.Y(f'{y_field}', title=y_title),
            color=alt.Color(f'{color_field}', legend=None) if color_field else alt.value('steelblue')
        ).interactive()  # Optional: Make the line chart interactive

    elif mark_type == 'arc':
        chart = alt.Chart(data).mark_arc().encode(
            theta=alt.Theta(field=f'{y_field}', type='quantitative', stack=True),
            color=alt.Color(field=color_field, type='nominal', legend=alt.Legend(title=x_title)),
            tooltip=[alt.Tooltip(field[0], title=field[1]) for field in tooltip_fields] if tooltip_fields else []
        )
    elif mark_type == 'area':
        chart = alt.Chart(data).mark_area().encode(
            x=alt.X(f'{x_field}', title=x_title, sort='-y'),
            y=alt.Y(f'{y_field}', title=y_title),
            color=alt.Color(f'{color_field}', legend=None) if color_field else alt.value('steelblue'),
            tooltip=[alt.Tooltip(field[0], title=field[1]) for field in tooltip_fields] if tooltip_fields else []
        )
    elif mark_type == 'point':
        chart = alt.Chart(data).mark_point().encode(
            x=alt.X(f'{x_field}', title=x_title, sort='-y'),
            y=alt.Y(f'{y_field}', title=y_title),
            color=alt.Color(f'{color_field}', legend=None) if color_field else alt.value('steelblue'),
            tooltip=[alt.Tooltip(field[0], title=field[1]) for field in tooltip_fields] if tooltip_fields else []
        )
    elif mark_type == 'scatter':
        chart = alt.Chart(data).mark_circle().encode(
            x=alt.X(f'{x_field}', title=x_title),
            y=alt.Y(f'{y_field}', title=y_title),
            color=alt.Color(f'{color_field}', legend=None) if color_field else alt.value('steelblue'),
            tooltip=[alt.Tooltip(field[0], title=field[1]) for field in tooltip_fields] if tooltip_fields else []
        )
    else:
        raise ValueError(
            "Ungültiger Markierungs-Typ. Unterstützte Werte sind 'bar', 'line', 'arc', 'area', 'point' und 'scatter'.")

    return chart


def calculate_kpis(df: pd.DataFrame, selected_column: str) -> pd.DataFrame:
    # Überprüfen, ob das DataFrame leer ist
    if df.empty:
        return None

    kpi_results = []

    if selected_column in df.columns:
        if pd.api.types.is_numeric_dtype(df[selected_column]):
            # Konvertiere numerische Werte in float64 für bessere Arrow-Kompatibilität
            df[selected_column] = df[selected_column].astype('float64')
            min_value = df[selected_column].min()
            max_value = df[selected_column].max()
            mean_value = df[selected_column].mean()
            sum_value = df[selected_column].sum()
            median_value = df[selected_column].median()
            std_value = df[selected_column].std()
            count_value = df[selected_column].count()

            kpi_results.append({'Metric': 'Min', 'Value': str(min_value)})
            kpi_results.append({'Metric': 'Max', 'Value': str(max_value)})
            kpi_results.append({'Metric': 'Mean', 'Value': str(mean_value)})
            kpi_results.append({'Metric': 'Sum', 'Value': str(sum_value)})
            kpi_results.append({'Metric': 'Median', 'Value': str(median_value)})
            kpi_results.append({'Metric': 'Std', 'Value': str(std_value)})
            kpi_results.append({'Metric': 'Count', 'Value': str(count_value)})

        elif pd.api.types.is_datetime64_any_dtype(df[selected_column]):
            # Konvertiere Datumswerte in datetime64 für bessere Arrow-Kompatibilität
            df[selected_column] = df[selected_column].astype('datetime64[ns]')
            min_date = df[selected_column].min()
            max_date = df[selected_column].max()
            count_date = df[selected_column].count()

            kpi_results.append({'Metric': 'Min Date', 'Value': str(min_date)})
            kpi_results.append({'Metric': 'Max Date', 'Value': str(max_date)})
            kpi_results.append({'Metric': 'Count', 'Value': str(count_date)})

        else:
            # Konvertiere kategorische Werte in object für bessere Arrow-Kompatibilität
            df[selected_column] = df[selected_column].astype('object')
            top_value = df[selected_column].value_counts().idxmax()
            top_count = df[selected_column].value_counts().max()
            unique_count = df[selected_column].nunique()
            missing_count = df[selected_column].isnull().sum()

            kpi_results.append({'Metric': 'Most Common Value', 'Value': str(top_value)})
            kpi_results.append({'Metric': 'Most Common Count', 'Value': str(top_count)})
            kpi_results.append({'Metric': 'Unique Count', 'Value': str(unique_count)})
            kpi_results.append({'Metric': 'Missing Count', 'Value': str(missing_count)})

    kpi_df = pd.DataFrame(kpi_results)
    return kpi_df
