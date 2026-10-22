import streamlit as st
import pandas as pd
import datetime
import time 
import gspread
from google.oauth2.service_account import Credentials

def calcular_minutos(hora_inicio, hora_fin):
    if isinstance(hora_inicio, datetime.time): hora_inicio = hora_inicio.strftime("%H:%M")
    if isinstance(hora_fin, datetime.time): hora_fin = hora_fin.strftime("%H:%M")
    
    hora_inicio = str(hora_inicio).strip()[:5]
    hora_fin = str(hora_fin).strip()[:5]
    
    formato = "%H:%M"
    try:
        t1 = datetime.datetime.strptime(hora_inicio, formato)
        t2 = datetime.datetime.strptime(hora_fin, formato)
        if t2 < t1:
            t2 += datetime.timedelta(days=1)
        diferencia = t2 - t1
        return round(diferencia.total_seconds() / 60.0, 1)
    except:
        return None 

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
    try:
        sh = conectar_gsheets()
        worksheet = sh.worksheet("Traslados")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            columnas = [
                "ID Evento", "Fecha", "Categoría (Edad)", "Código Prioridad", 
                "Hora Alerta", "Hora Arribo", "Hora Salida", "Tiempo Espera (min)", 
                "Tiempo Extracción", "Tiempo Total", "Cédula", "Motivo Traslado", "Lugar Origen"
            ]
            return pd.DataFrame(columns=columnas)
        return df
    except Exception:
        columnas = [
            "ID Evento", "Fecha", "Categoría (Edad)", "Código Prioridad", 
            "Hora Alerta", "Hora Arribo", "Hora Salida", "Tiempo Espera (min)", 
            "Tiempo Extracción", "Tiempo Total", "Cédula", "Motivo Traslado", "Lugar Origen"
        ]
        return pd.DataFrame(columns=columnas)

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

if 'hora_alerta_guardada' not in st.session_state:
    st.session_state.hora_alerta_guardada = None
if 'hora_arribo_guardada' not in st.session_state:
    st.session_state.hora_arribo_guardada = None
if 'hora_salida_guardada' not in st.session_state:
    st.session_state.hora_salida_guardada = None

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
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
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
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Capturar Hora Actual", key="btn_alerta"):
                st.session_state.hora_alerta_guardada = datetime.datetime.now().strftime("%H:%M")
        with col2:
            if st.session_state.hora_alerta_guardada is not None:
                st.success(f"Hora capturada: {st.session_state.hora_alerta_guardada}")
            else:
                st.info("Esperando captura...")

    with st.container(border=True):
        st.subheader("Toma 2: Hora de Arribo (B)")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Capturar Hora Actual", key="btn_arribo"):
                st.session_state.hora_arribo_guardada = datetime.datetime.now().strftime("%H:%M")
        with col2:
            if st.session_state.hora_arribo_guardada is not None:
                st.success(f"Hora capturada: {st.session_state.hora_arribo_guardada}")
            else:
                st.info("Esperando captura...")

    with st.container(border=True):
        st.subheader("Toma 3: Hora de Salida (C)")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Capturar Hora Actual", key="btn_salida"):
                st.session_state.hora_salida_guardada = datetime.datetime.now().strftime("%H:%M")
        with col2:
            if st.session_state.hora_salida_guardada is not None:
                st.success(f"Hora capturada: {st.session_state.hora_salida_guardada}")
            else:
                st.info("Esperando captura...")

    st.write("") 
    
    
    motivo_traslado = "N/D"
    lugar_origen = "N/D"
    
    if st.session_state.hora_alerta_guardada and st.session_state.hora_arribo_guardada and st.session_state.hora_salida_guardada:
        with st.container(border=True):
            st.info("🚑 **Ambulancia en camino:** Puede completar la información complementaria con calma.")
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                motivo_traslado = st.text_input("Motivo Clínico del Traslado (Manual):", placeholder="Ej. Lesión deportiva...")
            with col_m2:
                lugar_origen = st.text_input("Lugar de Origen en el Campus (Manual):", placeholder="Ej. Gimnasio, Talleres...")

    st.write("") 
    
    if st.button("Guardar y Finalizar Registro", type="primary", use_container_width=True):
        if st.session_state.hora_alerta_guardada and st.session_state.hora_arribo_guardada and st.session_state.hora_salida_guardada and cedula:
            try:
                df = cargar_datos_traslados()
                
                
                if not df.empty and "ID Evento" in df.columns:
                    ultimo_id = df.iloc[-1]["ID Evento"]
                    if ultimo_id and "TR-" in str(ultimo_id):
                        num = int(str(ultimo_id).split("-")[1])
                        nuevo_id = f"TR-{num + 1}"
                    else:
                        nuevo_id = "TR-1001"
                else:
                    nuevo_id = "TR-1001"
                
                
                t_espera = calcular_minutos(st.session_state.hora_alerta_guardada, st.session_state.hora_arribo_guardada)
                t_extraccion = calcular_minutos(st.session_state.hora_arribo_guardada, st.session_state.hora_salida_guardada)
                t_total = calcular_minutos(st.session_state.hora_alerta_guardada, st.session_state.hora_salida_guardada)
                
                
                nuevo_registro = {
                    "ID Evento": nuevo_id,
                    "Fecha": hoy,
                    "Categoría (Edad)": cat_edad,
                    "Código Prioridad": cod_prioridad,
                    "Hora Alerta": st.session_state.hora_alerta_guardada,
                    "Hora Arribo": st.session_state.hora_arribo_guardada,
                    "Hora Salida": st.session_state.hora_salida_guardada,
                    "Tiempo Espera (min)": t_espera,
                    "Tiempo Extracción": t_extraccion,
                    "Tiempo Total": t_total,
                    "Cédula": str(cedula),
                    "Motivo Traslado": motivo_traslado if motivo_traslado else "N/D",
                    "Lugar Origen": lugar_origen if lugar_origen else "N/D"
                }
                
               
                df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
                guardar_datos_traslados(df)
                
                st.session_state.hora_alerta_guardada = None
                st.session_state.hora_arribo_guardada = None
                st.session_state.hora_salida_guardada = None
                
                st.query_params.clear()
                
                st.balloons()
                st.success(f"¡Paciente {cedula} guardado exitosamente en la nube bajo la prioridad {cod_prioridad}!")
                time.sleep(3) 
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al guardar en la nube: {e}")
        else:
            st.warning("⚠️ Por favor captura el número de cédula y las tres horas antes de guardar el registro.")


elif st.session_state.pantalla_actual == 'Dashboard':
    st.title("Dashboard de Indicadores (KPIs - Nube)")
    st.link_button("📊 Abrir Base de Datos Central (Google Sheets)", url=https://docs.google.com/spreadsheets/d/1UAWXhHxnvRpGMfnfvSDizyfsdi0Dd7r10LyEzuSmMz4/edit?usp=sharing)

    
    try:
        df = cargar_datos_traslados()
        
        if df.empty:
            st.warning("⚠️ No hay datos de traslados registrados en la nube todavía.")
        else:
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            df['Tiempo Espera (min)'] = pd.to_numeric(df['Tiempo Espera (min)'], errors='coerce')
            
            if 'Cédula' not in df.columns:
                df['Cédula'] = "N/D"
            else:
                df['Cédula'] = df['Cédula'].fillna("N/D")
            
            total_traslados = len(df)
            promedio_historico = df['Tiempo Espera (min)'].mean()
            
            mes_actual = datetime.datetime.now().month
            df_mes = df[df['Fecha'].dt.month == mes_actual]
            promedio_mes = df_mes['Tiempo Espera (min)'].mean() if not df_mes.empty else 0.0
            
            
            st.subheader("💡 Diagnóstico Rápido")
            if promedio_historico < 20:
                st.success(f"**🟢 ESTADO ÓPTIMO:** El tiempo promedio de espera general es de {promedio_historico:.1f} minutos.")
            elif 20 <= promedio_historico <= 30:
                st.info(f"**🟡 ESTADO ACEPTABLE:** El tiempo promedio de espera es de {promedio_historico:.1f} minutos.")
            else:
                st.error(f"**🔴 ALERTA DE DEMORA:** Los tiempos de espera están muy altos ({promedio_historico:.1f} minutos en promedio).")
                
            st.write("---")
            
            
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                with st.container(border=True): 
                    st.metric(label="Promedio histórico", value=f"{promedio_historico:.1f} min")
            with kpi2:
                with st.container(border=True): 
                    st.metric(label="Promedio del mes", value=f"{promedio_mes:.1f} min")
            with kpi3:
                with st.container(border=True): 
                    st.metric(label="Total de traslados", value=f"{total_traslados}")
                    
            st.write("---") 
            
            
            st.subheader("⚠️ Auditoría de Cuellos de Botella (Tiempos Críticos)")
            df_criticos = df[df['Tiempo Espera (min)'] > 30] 
            if not df_criticos.empty:
                st.warning(f"Se han detectado {len(df_criticos)} traslados que excedieron el tiempo de espera aceptable (>30 min).")
                columnas_mostrar = ['ID Evento', 'Cédula', 'Fecha', 'Código Prioridad', 'Tiempo Espera (min)', 'Tiempo Total', 'Motivo Traslado']
                st.dataframe(df_criticos[columnas_mostrar].sort_values(by='Tiempo Espera (min)', ascending=False), use_container_width=True)
            else:
                st.success("¡Excelente! No hay traslados críticos recientes que superen los 30 minutos de espera.")
                
            st.write("---")
            
            
            graf_izq, graf_der = st.columns([6, 4])
            
            with graf_izq:
                with st.container(border=True): 
                    st.subheader("Tendencia: Tiempos de Espera (min)")
                    df_tendencia = df.groupby(df['Fecha'].dt.date)['Tiempo Espera (min)'].mean()
                    st.line_chart(df_tendencia)
                    
            with graf_der:
                with st.container(border=True): 
                    st.subheader("Distribución por Prioridad")
                    df_prioridad = df['Código Prioridad'].value_counts()
                    st.bar_chart(df_prioridad)

            
            st.write("---")
            st.subheader("🕒 Útimos 5 Traslados Registrados en la Nube")
            df_recientes = df.tail(5)[['ID Evento', 'Cédula', 'Código Prioridad', 'Motivo Traslado', 'Tiempo Total']].iloc[::-1]
            st.dataframe(df_recientes, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error al leer los datos del Dashboard desde la nube: {e}")
