import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import time 
import re
import gspread
from google.oauth2.service_account import Credentials

def obtener_hora_cr():
    return datetime.now(timezone.utc) - timedelta(hours=6)

def calcular_minutos(hora_inicio, hora_fin):
    if not hora_inicio or not hora_fin: return None
    hora_inicio = str(hora_inicio).strip()[:5]
    hora_fin = str(hora_fin).strip()[:5]
    
    formato = "%H:%M"
    try:
        t1 = datetime.strptime(hora_inicio, formato)
        t2 = datetime.strptime(hora_fin, formato)
        if t2 < t1:
            t2 += timedelta(days=1)
        diferencia = t2 - t1
        return round(diferencia.total_seconds() / 60.0, 1)
    except:
        return None 

def validar_hora(hora_str):
    return bool(re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", str(hora_str).strip()))

st.set_page_config(
    page_title="App Traslados TEC",
    page_icon="🚑",
    layout="wide"
)

def conectar_gsheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["connections"]["gsheets"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sh = client.open("DB_Central_Clinica_TEC")
    return sh

def cargar_datos_traslados():
    columnas_default = [
        "ID Evento", "Fecha", "Categoría (Edad)", "Código Prioridad", 
        "Hora Alerta", "Hora Arribo", "Hora Salida", "Tiempo Espera (min)", 
        "Tiempo Extracción", "Tiempo Total", "Cédula", "Motivo Traslado", "Lugar Origen", "Destino"
    ]
    try:
        sh = conectar_gsheets()
        worksheet = sh.worksheet("Traslados")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=columnas_default)
        return df
    except Exception:
        return pd.DataFrame(columns=columnas_default)

def guardar_datos_traslados(df):
    try:
        sh = conectar_gsheets()
        worksheet = sh.worksheet("Traslados")
        worksheet.clear()
        if not df.empty:
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"Error al sincronizar traslados con la nube: {e}")

params = st.query_params
url_cedula = params.get("cedula", "")
url_categoria = params.get("categoria", "")

if 'pantalla_actual' not in st.session_state:
    if url_cedula:
        st.session_state.pantalla_actual = 'Registro'
    else:
        st.session_state.pantalla_actual = 'Inicio'

if 'limpiar_campos' in st.session_state and st.session_state.limpiar_campos:
    st.session_state.in_alerta = ""
    st.session_state.in_arribo = ""
    st.session_state.in_salida = ""
    st.session_state.limpiar_campos = False

if 'in_alerta' not in st.session_state:
    st.session_state.in_alerta = ""
if 'in_arribo' not in st.session_state:
    st.session_state.in_arribo = ""
if 'in_salida' not in st.session_state:
    st.session_state.in_salida = ""

def capturar_alerta():
    st.session_state.in_alerta = obtener_hora_cr().strftime("%H:%M")

def capturar_arribo():
    st.session_state.in_arribo = obtener_hora_cr().strftime("%H:%M")

def capturar_salida():
    st.session_state.in_salida = obtener_hora_cr().strftime("%H:%M")

with st.sidebar:
    st.header("Clínica TEC")
    st.divider()
    
    if st.button("Inicio", use_container_width=True):
        st.session_state.pantalla_actual = 'Inicio'
        
    if st.button("Registrar Traslado", use_container_width=True):
        st.session_state.pantalla_actual = 'Registro'
        
    if st.button("Dashboard de KPIs", use_container_width=True):
        st.session_state.pantalla_actual = 'Dashboard'

if st.session_state.pantalla_actual == 'Inicio':
    st.title("Sistema de Control de Traslados")
    st.subheader("Clínica TEC - Módulo de Auditoría de Tiempos (Nube)")
    st.info("👈 Selecciona una opción en el menú lateral para comenzar.")

elif st.session_state.pantalla_actual == 'Registro':
    st.title("Nuevo Registro de Traslado")
    hoy = obtener_hora_cr().strftime("%Y-%m-%d")
    st.caption(f"Fecha: {hoy} | ID Evento: Generación Automática")
    
    if url_cedula:
        st.success("⚡ Cédula y categoría de edad sincronizadas automáticamente desde Pre-Registro.")
    
    st.write("") 

    with st.container(border=True):
        st.subheader("📋 Datos del Paciente")
        col_ced, col_cat, col_prio = st.columns(3)
        with col_ced:
            cedula = st.text_input("Número de Cédula", value=url_cedula, placeholder="Ej. 101230456")
        with col_cat:
            opciones_edad = ["Mayor de edad", "Menor de edad"]
            indice_edad = 0
            if url_categoria in opciones_edad:
                indice_edad = opciones_edad.index(url_categoria)
            cat_edad = st.selectbox("Categoría (Edad)", opciones_edad, index=indice_edad)
        with col_prio:
            cod_prioridad = st.selectbox("Código Prioridad", ["Verde", "Amarillo", "Rojo"])
    
    with st.container(border=True):
        st.subheader("Toma 1: Hora de Alerta (A)")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.button("Capturar Hora Actual", key="btn_alerta", on_click=capturar_alerta)
        with col2:
            hora_alerta = st.text_input("O ingrese hora manualmente (formato HH:MM):", key="in_alerta")

    with st.container(border=True):
        st.subheader("Toma 2: Hora de Arribo (B)")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.button("Capturar Hora Actual", key="btn_arribo", on_click=capturar_arribo)
        with col2:
            hora_arribo = st.text_input("O ingrese hora manualmente (formato HH:MM):", key="in_arribo")

    with st.container(border=True):
        st.subheader("Toma 3: Hora de Salida (C)")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.button("Capturar Hora Actual", key="btn_salida", on_click=capturar_salida)
        with col2:
            hora_salida = st.text_input("O ingrese hora manualmente (formato HH:MM):", key="in_salida")

    st.write("") 
    
    with st.container(border=True):
        st.info("🚑 **Información del Traslado:** Llene estos datos para completar el registro.")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            motivo_traslado = st.text_input("Motivo Clínico:", placeholder="Ej. Lesión deportiva...")
        with col_m2:
            lugar_origen = st.text_input("Lugar de Origen:", placeholder="Ej. Gimnasio...")
        with col_m3:
            destino_traslado = st.text_input("Destino del Traslado:", placeholder="Ej. Hospital Max Peralta")
        
        st.caption("💡 **Nota importante:** Si el destino u otro dato cambia durante el trayecto, puede actualizarlo en cualquier momento editando la celda directamente en la base de datos de Google Sheets.")

    st.write("") 
    
    if st.
