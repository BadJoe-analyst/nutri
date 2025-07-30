import streamlit as st
import gspread
from datetime import date, datetime
from google.oauth2.service_account import Credentials
# ------------------ FUNCIONES ------------------ #

def guardar_en_google_sheets(tipo_dia, cumplimiento_total, cumplimiento_por_grupo):
    try:
        creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
        credentials = Credentials.from_service_account_info(creds_dict)
        gc = gspread.authorize(credentials)
        sh = gc.open("cumplimiento_tracker")
        worksheet = sh.sheet1

        fila = [
            str(date.today()),
            tipo_dia,
            cumplimiento_total
        ]

        orden = [
            "Cereales / Carbohidratos",
            "Proteínas / Carnes",
            "Verduras generales",
            "Frutas",
            "Lácteos",
            "ARL o Grasas",
            "Aceites"
        ]

        for grupo in orden:
            hechas, totales = cumplimiento_por_grupo[grupo]
            porcentaje = round((hechas / totales) * 100) if totales > 0 else 0
            fila.append(porcentaje)

        worksheet.append_row(fila)
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")
        return False

def borrar_registro_de_hoy():
    try:
        gc = gspread.service_account(filename="credentials.json")
        sh = gc.open("cumplimiento_tracker")
        worksheet = sh.sheet1
        hoy = str(date.today())

        registros = worksheet.get_all_values()
        for i, fila in enumerate(registros):
            if fila and fila[0] == hoy:
                worksheet.delete_rows(i + 1)
                return True
        return False
    except Exception as e:
        st.error(f"❌ Error al borrar: {e}")
        return False

# ------------------ INICIO APP ------------------ #

st.set_page_config(page_title="Tracker Nutricional Diario", layout="centered")


if "carreras" not in st.session_state:
    st.session_state["carreras"] = {}

st.title("🏁 Próximas Carreras")

hoy = datetime.today().date()

# 1. FORMULARIO PARA AGREGAR CARRERA
with st.expander("➕ Agregar nueva carrera"):
    with st.form("form_carrera"):
        nombre = st.text_input("Nombre de la carrera")
        fecha = st.date_input("Fecha de la carrera", value=date.today())
        submitted = st.form_submit_button("Agregar carrera")
        if submitted:
            st.session_state["carreras"][nombre] = fecha
            st.success(f"Carrera '{nombre}' agregada para el {fecha.strftime('%d de %B de %Y')}.")

# 2. MOSTRAR CARRERAS CON BOTÓN DE ELIMINAR
if st.session_state["carreras"]:
    st.markdown("### 📅 Carreras registradas")
    
    for nombre, fecha in list(st.session_state["carreras"].items()):
        dias = (fecha - hoy).days
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            st.markdown(f"<h2 style='color:#4CAF50;'>FALTAN {dias} DÍAS PARA {nombre.upper()}</h2>", unsafe_allow_html=True)
        with col2:
            eliminar = st.button("🗑️", key=f"delete_{nombre}")
            if eliminar:
                st.session_state["carreras"].pop(nombre)
                st.success(f"Carrera '{nombre}' eliminada.")
                st.experimental_rerun()
else:
    st.info("No hay carreras registradas aún.")

# ------------------ TRACKER DE PORCIONES ------------------ #

st.markdown("---")
st.header("🥗 Tracker de Porciones Diarias")

grupo_emojis = {
    "Cereales / Carbohidratos": "🍞",
    "Proteínas / Carnes": "🍗",
    "Verduras generales": "🥦",
    "Frutas": "🍎",
    "Lácteos": "🧀",
    "ARL o Grasas": "🥑",
    "Aceites": "🫒"
}

porciones_dia = {
    "1/2 entrenamientos": {
        "Cereales / Carbohidratos": 4,
        "Proteínas / Carnes": 10,
        "Verduras generales": 4,
        "Frutas": 2,
        "Lácteos": 1,
        "ARL o Grasas": 1.5,
        "Aceites": 1
    },
    "3 entrenamientos": {
        "Cereales / Carbohidratos": 5,
        "Proteínas / Carnes": 10,
        "Verduras generales": 4,
        "Frutas": 2,
        "Lácteos": 2,
        "ARL o Grasas": 1.5,
        "Aceites": 1
    }
}

tipo_dia = st.radio("Selecciona el tipo de día:", list(porciones_dia.keys()))
datos_dia = porciones_dia[tipo_dia]

st.markdown("""
    <style>
    .porcentaje {
        font-weight: bold;
        float: right;
        padding-top: 0.3rem;
    }
    </style>
""", unsafe_allow_html=True)

cumplimiento = {}
total_porciones = 0
total_marcadas = 0

for grupo, cantidad in datos_dia.items():
    emoji = grupo_emojis.get(grupo, "")
    with st.container():
        st.markdown(f"#### {emoji} {grupo} ({cantidad} porciones)")
        cols = st.columns(int(cantidad * 2) + 1)
        marcadas = 0
        for i in range(int(cantidad * 2)):
            if cols[i].checkbox("", key=f"{grupo}_{i}"):
                marcadas += 0.5
        porcentaje = round((marcadas / cantidad) * 100) if cantidad > 0 else 0

        if porcentaje == 100:
            color = "green"
        elif porcentaje >= 70:
            color = "#8BC34A"
        else:
            color = "#CCCCCC"

        cols[-1].markdown(
            f"<span class='porcentaje' style='color:{color}'>{porcentaje}%</span>",
            unsafe_allow_html=True
        )

        cumplimiento[grupo] = (marcadas, cantidad)
        total_marcadas += marcadas
        total_porciones += cantidad

cumplimiento_total = round((total_marcadas / total_porciones) * 100) if total_porciones > 0 else 0
if cumplimiento_total == 100:
    total_color = "green"
elif cumplimiento_total >= 70:
    total_color = "#8BC34A"
else:
    total_color = "#CCCCCC"

st.markdown("---")
st.markdown("## 📊 Cumplimiento Total")
st.markdown(
    f"<h2 style='color:{total_color}'>{cumplimiento_total}%</h2>",
    unsafe_allow_html=True
)
st.progress(cumplimiento_total / 100)

# ------------------ BOTONES DE GUARDAR / BORRAR ------------------ #

st.markdown("### 📂 Acciones")

col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Guardar cumplimiento de hoy"):
        exito = guardar_en_google_sheets(tipo_dia, cumplimiento_total, cumplimiento)
        if exito:
            st.success("✅ Datos guardados exitosamente en Google Sheets.")
with col2:
    if st.button("🗑️ Eliminar cumplimiento de hoy"):
        eliminado = borrar_registro_de_hoy()
        if eliminado:
            st.success("✅ Registro de hoy eliminado correctamente.")
        else:
            st.warning("⚠️ No se encontró un registro para hoy.")
