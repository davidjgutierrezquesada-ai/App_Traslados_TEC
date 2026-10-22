import streamlit as st
import pandas as pd
import time
import csv
import io
import urllib.parse
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Pre-Registro Inteligente - Clínica", page_icon="🏥", layout="centered")

# --- CONEXIÓN A GOOGLE SHEETS DIRECTA ---
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

def cargar_base_datos():
    try:
        sh = conectar_gsheets()
        worksheet = sh.worksheet("Pacientes")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty:
            return []
        df = df.dropna(subset=["cedula"])
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as e:
        return [
            {"cedula": "111111111", "carne": "20261001", "nombre": "Juan Carlos Pérez Morales", "fecha_nac": "15/04/2005", "contacto": "8888-1111", "es_menor": "SI", "ultima_verificacion": "15/09/2026"},
            {"cedula": "222222222", "carne": "20261002", "nombre": "María Sofía Rojas Valverde", "fecha_nac": "20/08/2000", "contacto": "N/A (Mayor de edad)", "es_menor": "NO", "ultima_verificacion": "15/09/2026"}
        ]

def guardar_base_datos(db):
    try:
        sh = conectar_gsheets()
        worksheet = sh.worksheet("Pacientes")
        df_nuevo = pd.DataFrame(db)
        worksheet.clear()
        if not df_nuevo.empty:
            worksheet.update([df_nuevo.columns.values.tolist()] + df_nuevo.values.tolist())
    except Exception as e:
        st.error(f"Error al sincronizar con la nube: {e}")

def estandarizar_fecha(fecha_str):
    fecha_limpia = fecha_str.strip().replace("-", "/")
    try:
        obj_fecha = datetime.strptime(fecha_limpia, "%d/%m/%Y")
        fecha_perfecta = obj_fecha.strftime("%d/%m/%Y")
        return obj_fecha, fecha_perfecta
    except ValueError:
        return None, None

def calcular_edad(fecha_obj):
    hoy = datetime.now()
    return hoy.year - fecha_obj.year - ((hoy.month, hoy.day) < (fecha_obj.month, fecha_obj.day))

def generar_csv(datos):
    output = io.StringIO()
    if datos:
        todas_las_columnas = []
        for registro in datos:
            for clave in registro.keys():
                if clave not in todas_las_columnas:
                    todas_las_columnas.append(clave)
        writer = csv.DictWriter(output, fieldnames=todas_las_columnas)
        writer.writeheader()
        writer.writerows(datos)
    return output.getvalue().encode('utf-8')

# Inicializar DB en estado de sesión desde la nube
if 'db' not in st.session_state:
    st.session_state.db = cargar_base_datos()

# --- INTERFAZ PRINCIPAL ---
st.title("🏥 Sistema de Pre-Registro Inteligente")
st.markdown("Sistema de validación rápida y control de emergencias (Conectado a la Nube).")

tab_enf, tab_rec, tab_ges = st.tabs(["🩺 Enfermería", "🚨 Recepción", "⚙️ Gestión"])

# --- PESTAÑA 1: ENFERMERÍA ---
with tab_enf:
    st.header("Control Rutinario - Toma de Signos Vitales")
    st.caption("💡 Ingrese la cédula sin guiones para verificar o registrar a un paciente.")
    
    cedula_enf = st.text_input("Número de Cédula:", key="enf_cedula").strip()
    
    if st.button("Verificar / Buscar", type="primary", key="btn_enf_buscar"):
        if not cedula_enf:
            st.warning("Por favor ingrese un número de cédula válido.")
        else:
            existente = next((p for p in st.session_state.db if str(p["cedula"]) == str(cedula_enf)), None)
            if existente:
                st.success(f"✔ El paciente **{existente['nombre']}** ya se encuentra registrado.")
                st.info(f"Última verificación de datos: {existente.get('ultima_verificacion', 'Desconocido')}")
            else:
                st.session_state.mostrar_formulario_nuevo = True

    if st.session_state.get("mostrar_formulario_nuevo", False):
        st.warning("Nuevo paciente detectado. Complete los datos a continuación:")
        with st.form("form_nuevo_paciente"):
            carne = st.text_input("Carné Institucional / Código Funcionario:")
            nombre = st.text_input("Nombre Completo:")
            fnac = st.text_input("Fecha de Nacimiento (DD/MM/YYYY):", placeholder="Ej: 8/6/2006 o 08/06/2006")
            contacto = st.text_input("Teléfono Emergencia (Obligatorio si es menor):")
            
            submitted = st.form_submit_button("Guardar Pre-Registro")
            if submitted:
                fecha_obj, fecha_formateada = estandarizar_fecha(fnac)
                
                if not fecha_obj:
                    st.error("🚨 Formato de fecha incorrecto. Use el formato Día/Mes/Año (Ej: 15/04/2005).")
                else:
                    edad = calcular_edad(fecha_obj)
                    es_menor = "SI" if edad < 18 else "NO"
                    
                    if es_menor == "SI" and not contacto.strip():
                        st.error("🚨 El paciente es menor de edad. Debe ingresar obligatoriamente un número de contacto.")
                    else:
                        nuevo_registro = {
                            "cedula": str(cedula_enf),
                            "carne": carne.strip(),
                            "nombre": nombre.strip(),
                            "fecha_nac": fecha_formateada,
                            "contacto": contacto.strip() if es_menor == "SI" else "N/A (Mayor de edad)",
                            "es_menor": es_menor,
                            "ultima_verificacion": datetime.now().strftime("%d/%m/%Y")
                        }
                        st.session_state.db.append(nuevo_registro)
                        guardar_base_datos(st.session_state.db)
                        
                        st.success(f"Registro guardado con éxito en la nube. Edad calculada: {edad} años.")
                        time.sleep(2.5)
                        st.session_state.mostrar_formulario_nuevo = False
                        if 'enf_cedula' in st.session_state:
                            del st.session_state['enf_cedula']
                        st.rerun()

# --- PESTAÑA 2: RECEPCIÓN ---
with tab_rec:
    st.header("Módulo de Consulta Rápida - Emergencias")
    st.caption("💡 Buscador Universal: Ingrese nombre completo, cédula o carné/código.")
    
    query_rec = st.text_input("Dato del Paciente:", key="rec_query").strip().lower()
    
    if st.button("Buscar Información", type="primary", key="btn_rec_buscar"):
        if not query_rec:
            st.warning("Ingrese un parámetro de búsqueda.")
        else:
            encontrado = next((p for p in st.session_state.db if query_rec in str(p["cedula"]).lower() or query_rec in str(p["carne"]).lower() or query_rec in str(p["nombre"]).lower()), None)
            
            if encontrado:
                fecha_obj, _ = estandarizar_fecha(encontrado["fecha_nac"])
                edad_actual = calcular_edad(fecha_obj) if fecha_obj else -1
                
                if edad_actual >= 18 and encontrado["es_menor"] == "SI":
                    encontrado["es_menor"] = "NO"
                    encontrado["contacto"] = "N/A (Alcanzó mayoría de edad)"
                    encontrado["ultima_verificacion"] = datetime.now().strftime("%d/%m/%Y")
                    guardar_base_datos(st.session_state.db)

                st.markdown("### 📌 Datos del Paciente")
                st.write(f"**Nombre:** {encontrado['nombre']}")
                st.write(f"**Cédula:** {encontrado['cedula']} | **Identificador:** {encontrado['carne']}")
                st.write(f"**Edad Actual:** {edad_actual} años" if edad_actual != -1 else "**Edad Actual:** Error en formato guardado")
                st.caption(f"🕒 *Dato verificado por última vez el: {encontrado.get('ultima_verificacion', 'Desconocido')}*")
                
                if encontrado["es_menor"] == "SI":
                    st.toast('¡ATENCIÓN! PACIENTE MENOR DE EDAD', icon='🚨')
                    st.error(f"🚨 **¡ALERTA CRÍTICA: PACIENTE MENOR DE EDAD!** 🚨\n\n📞 **Contacto de Encargado Legal:** {encontrado['contacto']}")
                else:
                    st.success("✔ Estado: Mayor de edad. No requiere contacto de emergencia.")
                
                st.markdown("---")
                cedula_limpia = str(encontrado['cedula']).strip().replace("-", "").replace(" ", "")
                categoria_edad_url = "Menor de edad" if encontrado['es_menor'] == "SI" else "Mayor de edad"
                
                url_cedula = urllib.parse.quote(cedula_limpia)
                url_categoria = urllib.parse.quote(categoria_edad_url)
                
                enlace_traslado = f"https://traslados-clinica-tec.streamlit.app/?cedula={url_cedula}&categoria={url_categoria}"
                st.link_button("🚑 INICIAR TRASLADO DE EMERGENCIA", url=enlace_traslado, type="primary")
            else:
                st.error("❌ Paciente no encontrado. Aplique el protocolo alternativo de emergencia.")

# --- PESTAÑA 3: GESTIÓN ---
with tab_ges:
    st.header("Administración de Registros y Control WIP")
    
    total_pacientes = len(st.session_state.db)
    menores_activos = sum(1 for p in st.session_state.db if str(p.get("es_menor")) == "SI")
    
    col_wip1, col_wip2 = st.columns(2)
    with col_wip1:
        with st.container(border=True):
            st.metric(label="Total Pacientes Pre-Registrados", value=total_pacientes)
    with col_wip2:
        with st.container(border=True):
            st.metric(label="Menores de Edad Activos", value=menores_activos)
            
    st.write("---")
    
    col_export_1, col_export_2 = st.columns([3, 1])
    with col_export_1:
        st.caption("Busque por cédula o carné/código para editar o eliminar un registro.")
    with col_export_2:
        if st.session_state.db:
            csv_data = generar_csv(st.session_state.db)
            st.download_button(
                label="📥 Exportar DB a CSV",
                data=csv_data,
                file_name=f"Auditoria_Clinica_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

    query_ges = st.text_input("Buscar identificador:", key="ges_query").strip().lower()
    
    if st.button("Cargar Registro", key="btn_ges_buscar"):
        encontrado_ges = next((p for p in st.session_state.db if query_ges in str(p["cedula"]).lower() or query_ges in str(p["carne"]).lower()), None)
        if encontrado_ges:
            st.session_state.registro_editar = encontrado_ges
        else:
            st.error("No se encontró ningún paciente con esos datos.")
            st.session_state.registro_editar = None

    if st.session_state.get("registro_editar"):
        reg = st.session_state.registro_editar
        st.subheader("✏️ Modificar Datos")
        st.caption(f"🕒 *Última verificación: {reg.get('ultima_verificacion', 'Desconocido')}*")
        
        with st.form("form_editar_paciente"):
            st.write(f"**Cédula:** {reg['cedula']}")
            edit_carne = st.text_input("Carné / Código:", value=str(reg["carne"]))
            edit_nombre = st.text_input("Nombre Completo:", value=str(reg["nombre"]))
            edit_fnac = st.text_input("Fecha de Nacimiento (DD/MM/YYYY):", value=str(reg["fecha_nac"]))
            edit_contacto = st.text_input("Contacto Emergencia:", value=str(reg["contacto"]))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Guardar Cambios", type="primary"):
                    fecha_obj, fecha_formateada = estandarizar_fecha(edit_fnac)
                    
                    if not fecha_obj:
                        st.error("Formato de fecha incorrecto. Use DD/MM/YYYY o DD-MM-YYYY.")
                    else:
                        edad = calcular_edad(fecha_obj)
                        es_menor = "SI" if edad < 18 else "NO"
                        
                        if es_menor == "SI" and not edit_contacto.strip():
                            st.error("Debe ingresar un número de contacto para menores de edad.")
                        else:
                            for p in st.session_state.db:
                                if str(p["cedula"]) == str(reg["cedula"]):
                                    p["carne"] = edit_carne.strip()
                                    p["nombre"] = edit_nombre.strip()
                                    p["fecha_nac"] = fecha_formateada
                                    p["es_menor"] = es_menor
                                    p["contacto"] = edit_contacto.strip() if es_menor == "SI" else "N/A (Mayor de edad)"
                                    p["ultima_verificacion"] = datetime.now().strftime("%d/%m/%Y")
                            guardar_base_datos(st.session_state.db)
                            st.success("Registro actualizado con éxito en la nube.")
                            time.sleep(2.5)
                            st.session_state.registro_editar = None
                            if 'ges_query' in st.session_state:
                                del st.session_state['ges_query']
                            st.rerun()
            
            with col2:
                if st.form_submit_button("🗑️ Eliminar Registro"):
                    st.session_state.db = [p for p in st.session_state.db if str(p["cedula"]) != str(reg["cedula"])]
                    guardar_base_datos(st.session_state.db)
                    st.success("Registro eliminado correctamente de la nube.")
                    time.sleep(2.5)
                    st.session_state.registro_editar = None
                    if 'ges_query' in st.session_state:
                        del st.session_state['ges_query']
                    st.rerun()
