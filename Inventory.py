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
        ("Groutmaster", "6.5 Lbs / 2.95 Kg"),
        ("Pure O2", "8 Lbs / 3.62 Kg"),
        ("Triplephase", "1 Gal / 3.78 L"),
        ("Green Guard (Protector)", "1 Gal / 3.78 L"),
        ("Citrus Burst", "1 Gal / 3.78 L"),
        ("Procyon Liquid", "1 Gal / 3.78 L"),
        ("Releasit - Encap Cleaning Tech", "1 Gal / 3.78 L"),
        ("Wool Medic", "1 Gal / 3.78 L"),
        ("Eco Cide", "1 Gal / 3.78 L"),
        ("Solvent Clean", "1 Gal / 3.78 L"),
        ("Unchained", "1 Gal / 3.78 L"),
        ("Folex", "1 Gal / 3.78 L"),
        ("Boost All", "8 Lbs / 3.62 Kg"),
        ("Spot Stop", "Quarter / 0.94 L"),
        ("Releasit", "Quarter / 0.94 L"),
        ("Red Zone ready", "Quarter / 0.94 L"),
        ("Wool Pro", "0.47 L"),
        ("Stain Zone", "Quarter / 0.94 L"),
        ("Rust out", "Quarter / 0.94 L"),
        ("T-Rust", "0.47 L"),
        ("Filtration Soil", "473 mL"),
        ("1 Red", "Quarter / 0.94 L"),
        ("Filter Free", "Quarter / 0.94 L"),
        ("All Solvent Extreme", "0.35 L"),
    ]
    df = pd.DataFrame([{"Item": i+1, "Description": desc, "Unit": unit} for i, (desc, unit) in enumerate(productos)])

# --- Sesión ---
if "df" not in st.session_state:
    st.session_state.df = df

# --- Selección de fecha manual ---
selected_date = st.date_input("Selecciona la fecha de ingreso", value=datetime.today())
col_name = selected_date.strftime("%m/%d/%y")

# Crear columna si no existe
if col_name not in st.session_state.df.columns:
    st.session_state.df[col_name] = 0

# --- Editor para ingresar cantidades ---
columns_to_show = ["Description", col_name]

edited_df = st.data_editor(
    st.session_state.df[columns_to_show],
    num_rows="dynamic",
    use_container_width=True
)

# --- Guardar en Google Sheets ---
if st.button("💾 Guardar datos"):
    # Actualizar solo la columna de la fecha seleccionada
    st.session_state.df[col_name] = edited_df[col_name]
    df_to_save = st.session_state.df.fillna("")
    sheet.clear()
    sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
    st.success(f"Datos guardados correctamente para la fecha {col_name}")
