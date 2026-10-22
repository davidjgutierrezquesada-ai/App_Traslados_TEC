import streamlit as st
import pandas as pd
import datetime
import time 
from openpyxl import load_workbook 

# --- FUNCIÓN MATEMÁTICA ROBUSTA ---
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

# 1. Configuración principal de la página
st.set_page_config(
    page_title="App Traslados TEC",
    page_icon="🚑",
    layout="wide"
)

# --- RECEPTOR DE DATOS DE LA APP DE PRE-REGISTRO ---
params = st.query_params
url_cedula = params.get("cedula", "")
url_categoria = params.get("categoria", "") # Recibe "Mayor de edad" o "Menor de edad"

# 2. --- MEMORIA DE NAVEGACIÓN Y VARIABLES ---
if 'pantalla_actual' not in st.session_state:
    # ENRUTAMIENTO INTELIGENTE: Si detecta cédula, salta directo al Registro
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

# 3. --- MENÚ LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("Clínica TEC")
    st.divider()
    
    if st.button("Inicio", use_container_width=True):
        st.session_state.pantalla_actual = 'Inicio'
        
    if st.button("Registrar Traslado", use_container_width=True):
        st.session_state.pantalla_actual = 'Registro'
        
    if st.button("Dashboard de KPIs", use_container_width=True):
        st.session_state.pantalla_actual = 'Dashboard'

# 4. --- ÁREA PRINCIPAL ---

# Pantalla 1: INICIO
if st.session_state.pantalla_actual == 'Inicio':
    st.title("Sistema de Control de Traslados")
    st.subheader("Clínica TEC - Módulo de Auditoría de Tiempos")
    st.info("👈 Selecciona una opción en el menú lateral para comenzar.")

# Pantalla 2: REGISTRO
elif st.session_state.pantalla_actual == 'Registro':
    st.title("Nuevo Registro de Traslado")
    hoy = datetime.datetime.now().strftime("%Y-%m-%d")
    st.caption(f"Fecha: {hoy} | ID Evento: Generación Automática")
    
    if url_cedula:
        st.success("⚡ Cédula y categoría de edad sincronizadas automáticamente desde Pre-Registro.")
    
    st.write("") 

    # DATOS DEL PACIENTE CON CÉDULA
    with st.container(border=True):
        st.subheader("📋 Datos del Paciente")
        col_ced, col_cat, col_prio = st.columns(3)
        with col_ced:
            # AUTOCOMPLETADO DE CÉDULA
            cedula = st.text_input("Número de Cédula", value=url_cedula, placeholder="Ej. 101230456")
        with col_cat:
            # AUTOCOMPLETADO INTELIGENTE DE CATEGORÍA DE EDAD
            opciones_edad = ["Mayor de edad", "Menor de edad"]
            
            # Si la URL trae la categoría exacta, la seleccionamos; si no, por defecto la primera (Mayor)
            indice_edad = 0
            if url_categoria in opciones_edad:
                indice_edad = opciones_edad.index(url_categoria)
                
            cat_edad = st.selectbox("Categoría (Edad)", opciones_edad, index=indice_edad)
            
        with col_prio:
            cod_prioridad = st.selectbox("Código Prioridad", ["Verde", "Amarillo", "Rojo"])
    
    # TARJETAS DE TIEMPO
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
    
    if st.button("Guardar y Finalizar Registro", type="primary", use_container_width=True):
        if st.session_state.hora_alerta_guardada and st.session_state.hora_arribo_guardada and st.session_state.hora_salida_guardada and cedula:
            try:
                nombre_archivo = 'Dashboard_Control_Tiempos.xlsx'
                wb = load_workbook(nombre_archivo)
                ws = wb.active
                
                # Auditor Automático (Backfill)
                for fila in range(3, ws.max_row + 1):
                    alerta = ws.cell(row=fila, column=5).value
                    arribo = ws.cell(row=fila, column=6).value
                    salida = ws.cell(row=fila, column=7).value
                    espera_actual = ws.cell(row=fila, column=8).value
                    
                    if alerta and arribo and salida and (espera_actual is None or str(espera_actual).strip() == ""):
                        calc_espera = calcular_minutos(alerta, arribo)
                        calc_extraccion = calcular_minutos(arribo, salida)
                        calc_total = calcular_minutos(alerta, salida)
                        if calc_espera is not None:
                            ws.cell(row=fila, column=8).value = calc_espera
                            ws.cell(row=fila, column=9).value = calc_extraccion
                            ws.cell(row=fila, column=10).value = calc_total

                # Ingreso de nuevo paciente
                fila_vacia = ws.max_row + 1
                for fila in range(3, ws.max_row + 2):
                    if ws.cell(row=fila, column=1).value is None:
                        fila_vacia = fila
                        break
                        
                ultimo_id = ws.cell(row=fila_vacia - 1, column=1).value
                if ultimo_id and "TR-" in str(ultimo_id):
                    num = int(str(ultimo_id).split("-")[1])
                    nuevo_id = f"TR-{num + 1}"
                else:
                    nuevo_id = "TR-1001"
                
                # Escritura en Excel
                ws.cell(row=2, column=11).value = "Cédula"
                ws.cell(row=fila_vacia, column=11).value = cedula 
                ws.cell(row=fila_vacia, column=1).value = nuevo_id 
                ws.cell(row=fila_vacia, column=2).value = hoy      
                ws.cell(row=fila_vacia, column=3).value = cat_edad       
                ws.cell(row=fila_vacia, column=4).value = cod_prioridad  
                ws.cell(row=fila_vacia, column=5).value = st.session_state.hora_alerta_guardada 
                ws.cell(row=fila_vacia, column=6).value = st.session_state.hora_arribo_guardada 
                ws.cell(row=fila_vacia, column=7).value = st.session_state.hora_salida_guardada 
                
                ws.cell(row=fila_vacia, column=8).value = calcular_minutos(st.session_state.hora_alerta_guardada, st.session_state.hora_arribo_guardada)
                ws.cell(row=fila_vacia, column=9).value = calcular_minutos(st.session_state.hora_arribo_guardada, st.session_state.hora_salida_guardada)
                ws.cell(row=fila_vacia, column=10).value = calcular_minutos(st.session_state.hora_alerta_guardada, st.session_state.hora_salida_guardada)
                
                wb.save(nombre_archivo)
                
                st.session_state.hora_alerta_guardada = None
                st.session_state.hora_arribo_guardada = None
                st.session_state.hora_salida_guardada = None
                
                # Limpiar los parámetros de la URL para evitar recargas repetidas
                st.query_params.clear()
                
                st.balloons()
                st.success(f"¡Paciente {cedula} guardado exitosamente bajo la prioridad {cod_prioridad}!")
                time.sleep(3) 
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al guardar: {e}")
        else:
            st.warning("⚠️ Por favor captura el número de cédula y las tres horas antes de guardar el registro.")

# Pantalla 3: DASHBOARD MEJORADO Y CORREGIDO
elif st.session_state.pantalla_actual == 'Dashboard':
    st.title("Dashboard de Indicadores (KPIs)")
    
    try:
        with open('Dashboard_Control_Tiempos.xlsx', 'rb') as f:
            st.download_button(
                label="📥 Descargar Base de Datos (Excel)",
                data=f,
                file_name=f"Control_Tiempos_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
    except FileNotFoundError:
        pass
    
    st.write("") 
    
    try:
        df = pd.read_excel('Dashboard_Control_Tiempos.xlsx', header=1)
        df = df.dropna(subset=['ID Evento'])
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        
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
            st.error(f"**🔴 ALERTA DE DEMORA:** Los tiempos de espera están muy altos ({promedio_historico:.1f} minutos).")
            
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
            st.warning(f"Se han detectado {len(df_criticos)} traslados que excedieron el tiempo aceptable (>30 min).")
            columnas_mostrar = ['ID Evento', 'Cédula', 'Fecha', 'Código Prioridad', 'Tiempo Espera (min)', 'Tiempo Total']
            st.dataframe(df_criticos[columnas_mostrar].sort_values(by='Tiempo Espera (min)', ascending=False), use_container_width=True)
        else:
            st.success("¡Excelente! No hay traslados críticos recientes que superen los 30 minutos.")
            
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
        st.subheader("🕒 Útimos 5 Traslados Registrados")
        df_recientes = df.tail(5)[['ID Evento', 'Cédula', 'Código Prioridad', 'Tiempo Total']].iloc[::-1]
        st.dataframe(df_recientes, use_container_width=True)

    except FileNotFoundError:
        st.warning("⚠️ No se encontró la base de datos Excel. Registra un traslado primero para crearla.")
    except Exception as e:
        st.error(f"⚠️ Error al leer los datos del Dashboard: {e}")
