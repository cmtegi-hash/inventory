import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
import json

st.set_page_config(page_title="Inventory – Carpet Cleaner", layout="centered")
st.title("📦 Inventory – Carpet Cleaner")

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

# --- Leer datos ---
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
if "new_load" not in st.session_state:
    st.session_state.new_load = False
if "fecha_pasada" not in st.session_state:
    st.session_state.fecha_pasada = None
if "fecha_actual" not in st.session_state:
    st.session_state.fecha_actual = None

# --- Nueva carga ---
if st.button("📅 Nueva carga"):
    st.session_state.new_load = True

if st.session_state.new_load:
    new_date = st.date_input("Selecciona la fecha para la nueva columna", key="new_date")
    if st.button("✅ Confirmar nueva columna"):
        col_name = new_date.strftime("%m/%d/%y")
        if col_name not in st.session_state.df.columns:
            st.session_state.df[col_name] = 0
        st.session_state.new_load = False

# --- Selección de fechas para diferencias ---
cols_dates = [col for col in st.session_state.df.columns if "/" in col]
if len(cols_dates) >= 2:
    st.session_state.fecha_pasada = cols_dates[-2]
    st.session_state.fecha_actual = cols_dates[-1]

# --- Editor interactivo ---
# Solo permitir editar las columnas que no son pasadas
editable_cols = st.session_state.df.columns.tolist()
disabled_cols = [st.session_state.fecha_pasada] if st.session_state.fecha_pasada else []
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True,
    disabled=disabled_cols
)

# --- Calcular diferencia ---
def calcular_diferencia(row):
    fecha_pasada = st.session_state.fecha_pasada
    fecha_actual = st.session_state.fecha_actual
    if fecha_pasada and fecha_actual:
        diff = int(row[fecha_actual]) - int(row[fecha_pasada])
        if diff < 0:
            return f"{diff} 🔴"
        elif diff > 0:
            return f"+{diff} 🟢"
        else:
            return f"{diff} 🟡"
    return ""

edited_df["Difference"] = edited_df.apply(calcular_diferencia, axis=1)

# --- Mostrar tabla final ---
st.markdown("### 🧾 Inventory with difference")
st.dataframe(edited_df, use_container_width=True)

# --- Clase PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 11)
        self.cell(200, 10, "Inventory - Carpet Cleaner", ln=True, align="C")
        fecha_pasada = st.session_state.fecha_pasada or ""
        fecha_actual = st.session_state.fecha_actual or ""
        self.cell(200, 10, f"Comparison: {fecha_pasada} vs {fecha_actual}", ln=True, align="C")
        self.ln(5)

        col_widths = [10, 60, 40]
        if fecha_pasada and fecha_actual:
            col_widths += [25, 25]
        col_widths.append(30)
        headers = ["#", "Description", "Unit"]
        if fecha_pasada and fecha_actual:
            headers += [fecha_pasada, fecha_actual]
        headers.append("Difference")
        self.set_fill_color(220, 220, 220)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, align="C", fill=True)
        self.ln()

# --- Exportar PDF ---
def export_pdf(df):
    pdf = PDF()
    pdf.add_page()
    col_widths = [10, 60, 40]
    fecha_pasada = st.session_state.fecha_pasada
    fecha_actual = st.session_state.fecha_actual
    if fecha_pasada and fecha_actual:
        col_widths += [25, 25]
    col_widths.append(30)
    row_height = 8
    block_size = 5

    for idx in range(0, len(df), block_size):
        block = df.iloc[idx:idx+block_size]
        if pdf.get_y() + row_height*(len(block)+2) > pdf.page_break_trigger:
            pdf.add_page()
        for i, row in block.iterrows():
            fill_color = (245, 245, 245) if i % 2 == 0 else (255, 255, 255)
            pdf.set_fill_color(*fill_color)
            pdf.set_font("Arial", size=10)

            pdf.cell(col_widths[0], row_height, str(row["Item"]), border=1, align="C", fill=True)
            pdf.cell(col_widths[1], row_height, str(row["Description"]).replace("–", "-"), border=1, fill=True)
            pdf.cell(col_widths[2], row_height, str(row["Unit"]), border=1, align="C", fill=True)

            if fecha_pasada and fecha_actual:
                pdf.cell(col_widths[3], row_height, str(int(row[fecha_pasada])), border=1, align="C", fill=True)
                pdf.cell(col_widths[4], row_height, str(int(row[fecha_actual])), border=1, align="C", fill=True)
                diff = int(row[fecha_actual]) - int(row[fecha_pasada])
            else:
                diff = 0

            pdf.set_font("Arial", size=12)
            if diff < 0:
                pdf.set_text_color(255, 0, 0)
                pdf.cell(col_widths[-1], row_height, str(diff), border=1, align="C", fill=True)
            elif diff > 0:
                pdf.set_text_color(0, 150, 0)
                pdf.cell(col_widths[-1], row_height, f"+{diff}", border=1, align="C", fill=True)
            else:
                pdf.set_text_color(200, 200, 0)
                pdf.cell(col_widths[-1], row_height, "0", border=1, align="C", fill=True)

            pdf.set_text_color(0, 0, 0)
            pdf.ln()
        pdf.ln(5)

    return bytes(pdf.output(dest="S"))

# --- Guardar en Google Sheets ---
if st.button("💾 Guardar"):
    st.session_state.df.update(edited_df)
    df_to_save = st.session_state.df.fillna("")
    sheet.clear()
    sheet.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())
    st.success("Datos guardados correctamente en Google Sheets")

# --- Exportar PDF ---
if st.button("📤 Export to PDF"):
    pdf_bytes = export_pdf(edited_df)
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name="inventory_report.pdf",
        mime="application/pdf"
    )
