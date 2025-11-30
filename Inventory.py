import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import json

st.set_page_config(page_title="Inventory Input – Carpet Cleaner", layout="centered")
st.title("📦 Inventory Input – Carpet Cleaner (Móvil)")

# --- Google Sheets ---
SHEET_NAME = "inventory_carpet"
WORKSHEET_NAME = "inventory_test"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- Credenciales desde secretos ---
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"]["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

# --- Acceder hoja ---
try:
    sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
except gspread.SpreadsheetNotFound:
    st.error(f"No se encontró el archivo {SHEET_NAME} o la hoja {WORKSHEET_NAME}")
    st.stop()
except gspread.WorksheetNotFound:
    sheet = client.open(SHEET_NAME).add_worksheet(title=WORKSHEET_NAME, rows="100", cols="50")

# --- Leer datos existentes ---
data = sheet.get_all_records()
if data:
    df = pd.DataFrame(data)
else:
    productos = [
        ("Volume 40", "1 Gal / 3.78 L"),
        ("Defoamer", "6.5 Lbs / 2.95 Kg"),
        ("Avenge Pro", "1 Gal / 3.78 L"),
        ("Rob's Solvent Sealer", "1 Gal / 3.78 L"),
        ("Bio Break", "6 Lbs / 2.72 Kg"),
        # Agregar más productos según tu lista...
    ]
    df = pd.DataFrame([{"Item": i+1, "Description": desc, "Unit": unit} for i, (desc, unit) in enumerate(productos)])

# --- Sesión ---
if "df" not in st.session_state:
    st.session_state.df = df

# --- Selección de fecha para la nueva columna ---
new_date = st.date_input("Selecciona la fecha de ingreso")
col_name = new_date.strftime("%m/%d/%y")
if col_name not in st.session_state.df.columns:
    st.session_state.df[col_name] = 0

# --- Editor para ingresar cantidades ---
# Mostrar solo 'Description' y la columna de la fecha
columns_to_show = ["Description", col_name]

# Ajuste de ancho de columnas
column_config = {
    "Description": st.column_config.Column(
        "Description", width="medium", editable=False
    ),
    col_name: st.column_config.Column(
        col_name, width="small", editable=True
    )
}

edited_df = st.data_editor(
    st.session_state.df[columns_to_show],
    num_rows="dynamic",
    use_container_width=True,
    column_config=column_config
)

# --- Guardar en Google Sheets ---
if st.button("💾 Guardar datos"):
    # Actualizar solo la columna de la fecha
    st.session_state.df[col_name] = edited_df[col_name]
    df_to_save = st.session_state.df.fillna("")
    sheet.clear()
    sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
    st.success(f"Datos guardados correctamente para la fecha {col_name}")
