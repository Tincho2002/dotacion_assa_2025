import streamlit as st
import pandas as pd
import altair as alt
import io
from datetime import datetime
from itertools import product

# --- Configuración de la página y Estilos CSS ---
st.set_page_config(layout="wide")
st.markdown("""
<style>
/* Estilo general para los botones de descarga */
div.stDownloadButton button {
    background-color: #28a745; /* Verde Bootstrap */
    color: white;
    font-weight: bold;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px; /* Espacio entre el icono y el texto */
}

div.stDownloadButton button:hover {
    background-color: #218838; /* Verde más oscuro al pasar el ratón */
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
}

/* Estilo para los selectores múltiples (filtros) */
.stMultiSelect div[data-baseweb="select"] {
    border: 1px solid #2C3E50; /* Azul elegante para el borde */
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    background-color: #D6EAF8; /* Fondo azul claro elegante */
    transition: all 0.2s ease-in-out;
}
.stMultiSelect div[data-baseweb="select"]:hover {
    border-color: #3498DB; /* Azul ligeramente más brillante al pasar el ratón */
}
.stMultiSelect label {
    font-weight: bold;
    color: #2C3E50; /* Texto azul oscuro para las etiquetas */
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# --- Título de la Aplicación ---
st.title('📊 Dashboard de Dotación Anual 2025')
st.subheader('Análisis Interactivo de la Composición de la Dotación por Periodo')

# --- Funciones Auxiliares ---

def generate_download_buttons(df_to_download, filename_prefix):
    """Genera botones para descargar un DataFrame como CSV y Excel."""
    st.markdown("<h6>Opciones de Descarga:</h6>", unsafe_allow_html=True)
    col_dl1, col_dl2 = st.columns(2)
    
    # Descarga CSV
    csv_buffer = io.StringIO()
    df_to_download.to_csv(csv_buffer, index=False)
    with col_dl1:
        st.download_button(
            label="⬇️ Descargar como CSV",
            data=csv_buffer.getvalue(),
            file_name=f"{filename_prefix}.csv",
            mime="text/csv",
            key=f"csv_download_{filename_prefix}"
        )
    
    # Descarga Excel
    excel_buffer = io.BytesIO()
    df_to_download.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    with col_dl2:
        st.download_button(
            label="📊 Descargar como Excel",
            data=excel_buffer.getvalue(),
            file_name=f"{filename_prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"excel_download_{filename_prefix}"
        )

@st.cache_data
def load_and_clean_data(uploaded_file_obj):
    """Carga y limpia los datos desde el archivo Excel subido."""
    try:
        df_excel = pd.read_excel(uploaded_file_obj, sheet_name='Dotacion_25')
    except Exception as e:
        st.error(f"ERROR CRÍTICO: No se pudo leer la hoja 'Dotacion_25'. Mensaje: {e}")
        return pd.DataFrame()

    if df_excel.empty:
        return pd.DataFrame()

    # --- Procesamiento de Columnas ---
    # Convertir LEGAJO a numérico
    if 'LEGAJO' in df_excel.columns:
        df_excel['LEGAJO'] = pd.to_numeric(df_excel['LEGAJO'], errors='coerce')

    # Calcular Rango Antigüedad si no existe
    if 'Rango (Antigüedad)' not in df_excel.columns or df_excel['Rango (Antigüedad)'].isna().all():
        if 'Fecha ing.' in df_excel.columns:
            fecha_ingreso = pd.to_datetime(df_excel['Fecha ing.'], errors='coerce')
            if fecha_ingreso.notna().any():
                antiguedad_anos = (datetime.now() - fecha_ingreso).dt.days / 365.25
                bins = [0, 5, 10, 15, 20, 25, 30, 35, float('inf')]
                labels = ['de 0 a 5 años', 'de 5 a 10 años', 'de 11 a 15 años', 'de 16 a 20 años', 'de 21 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'más de 35 años']
                df_excel['Rango Antiguedad'] = pd.cut(antiguedad_anos, bins=bins, labels=labels, right=False)
            else:
                df_excel['Rango Antiguedad'] = 'no disponible'
        else:
            df_excel['Rango Antiguedad'] = 'no disponible'
    else:
        df_excel['Rango Antiguedad'] = df_excel['Rango (Antigüedad)'].astype(str).str.strip().str.lower()

    # Calcular Rango Edad si no existe
    if 'Rango (Edad)' not in df_excel.columns or df_excel['Rango (Edad)'].isna().all():
        if 'Fecha Nac.' in df_excel.columns:
            fecha_nac = pd.to_datetime(df_excel['Fecha Nac.'], errors='coerce')
            if fecha_nac.notna().any():
                edad_anos = (datetime.now() - fecha_nac).dt.days / 365.25
                bins = [0, 19, 25, 30, 35, 40, 45, 50, 55, 60, 65, float('inf')]
                labels = ['de 0 a 19 años', 'de 19 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'de 36 a 40 años', 'de 41 a 45 años', 'de 46 a 50 años', 'de 51 a 55 años', 'de 56 a 60 años', 'de 61 a 65 años', 'más de 65 años']
                df_excel['Rango Edad'] = pd.cut(edad_anos, bins=bins, labels=labels, right=False)
            else:
                df_excel['Rango Edad'] = 'no disponible'
        else:
            df_excel['Rango Edad'] = 'no disponible'
    else:
        df_excel['Rango Edad'] = df_excel['Rango (Edad)'].astype(str).str.strip().str.lower()
    
    # Procesar Período
    if 'Periodo' in df_excel.columns:
        df_excel['Periodo'] = df_excel['Periodo'].astype(str).str.strip().str.capitalize().replace(['None', 'Nan'], 'No disponible')
    
    # Asegurar que todas las columnas de texto existan y estén limpias
    text_cols = ['Gerencia', 'Relación', 'Sexo', 'Función', 'Distrito', 'Ministerio', 'Nivel', 'Rango Antiguedad', 'Rango Edad', 'Periodo']
    for col in text_cols:
        if col not in df_excel.columns:
            df_excel[col] = 'no disponible'
        df_excel[col] = df_excel[col].astype(str).str.strip().replace(['None', 'nan', ''], 'no disponible')

    return df_excel

def get_sorted_unique_options(dataframe, column_name):
    """Obtiene opciones únicas y ordenadas para los filtros."""
    if column_name in dataframe.columns:
        unique_values = dataframe[column_name].dropna().unique().tolist()
        if column_name == 'Rango Antiguedad':
            order = ['de 0 a 5 años', 'de 5 a 10 años', 'de 11 a 15 años', 'de 16 a 20 años', 'de 21 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'más de 35 años', 'no disponible']
            return sorted(unique_values, key=lambda x: order.index(x.lower()) if x.lower() in order else 99)
        elif column_name == 'Rango Edad':
            order = ['de 0 a 19 años', 'de 19 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'de 36 a 40 años', 'de 41 a 45 años', 'de 46 a 50 años', 'de 51 a 55 años', 'de 56 a 60 años', 'de 61 a 65 años', 'más de 65 años', 'no disponible']
            return sorted(unique_values, key=lambda x: order.index(x.lower()) if x.lower() in order else 99)
        elif column_name == 'Periodo':
            month_order = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12, 'No disponible': 99}
            return sorted(unique_values, key=lambda x: month_order.get(x.capitalize(), 99))
        return sorted(unique_values) if unique_values else ['no disponible']
    return ['no disponible']


# --- Cuerpo Principal de la Aplicación ---
uploaded_file = st.file_uploader("📂 Por favor, sube tu archivo Excel de dotación", type="xlsx")

if uploaded_file is not None:
    df = load_and_clean_data(uploaded_file)

    if df.empty:
        st.stop()

    st.success(f"Se ha cargado un total de **{len(df)}** registros de empleados.")
    st.markdown("---")

    # --- Barra Lateral de Filtros ---
    st.sidebar.header('Filtros del Dashboard')
    
    selected_periodos = st.sidebar.multiselect('Selecciona Periodo(s):', get_sorted_unique_options(df, 'Periodo'), default=get_sorted_unique_options(df, 'Periodo'))
    selected_gerencias = st.sidebar.multiselect('Selecciona Gerencia(s):', get_sorted_unique_options(df, 'Gerencia'), default=get_sorted_unique_options(df, 'Gerencia'))
    selected_relaciones = st.sidebar.multiselect('Selecciona Relación(es):', get_sorted_unique_options(df, 'Relación'), default=get_sorted_unique_options(df, 'Relación'))
    selected_sexos = st.sidebar.multiselect('Selecciona Sexo(s):', get_sorted_unique_options(df, 'Sexo'), default=get_sorted_unique_options(df, 'Sexo'))
    selected_rangos_antiguedad = st.sidebar.multiselect('Selecciona Rango(s) de Antigüedad:', get_sorted_unique_options(df, 'Rango Antiguedad'), default=get_sorted_unique_options(df, 'Rango Antiguedad'))
    selected_rangos_edad = st.sidebar.multiselect('Selecciona Rango(s) de Edad:', get_sorted_unique_options(df, 'Rango Edad'), default=get_sorted_unique_options(df, 'Rango Edad'))
    selected_funciones = st.sidebar.multiselect('Selecciona Función(es):', get_sorted_unique_options(df, 'Función'), default=get_sorted_unique_options(df, 'Función'))
    selected_distritos = st.sidebar.multiselect('Selecciona Distrito(s):', get_sorted_unique_options(df, 'Distrito'), default=get_sorted_unique_options(df, 'Distrito'))
    selected_ministerios = st.sidebar.multiselect('Selecciona Ministerio(s):', get_sorted_unique_options(df, 'Ministerio'), default=get_sorted_unique_options(df, 'Ministerio'))
    selected_niveles = st.sidebar.multiselect('Selecciona Nivel(es):', get_sorted_unique_options(df, 'Nivel'), default=get_sorted_unique_options(df, 'Nivel'))

    # --- Lógica de Filtrado ---
    filtered_df = df[
        (df['Periodo'].isin(selected_periodos)) &
        (df['Gerencia'].isin(selected_gerencias)) &
        (df['Relación'].isin(selected_relaciones)) &
        (df['Sexo'].isin(selected_sexos)) &
        (df['Rango Antiguedad'].isin(selected_rangos_antiguedad)) &
        (df['Rango Edad'].isin(selected_rangos_edad)) &
        (df['Función'].isin(selected_funciones)) &
        (df['Distrito'].isin(selected_distritos)) &
        (df['Ministerio'].isin(selected_ministerios)) &
        (df['Nivel'].isin(selected_niveles))
    ]

    st.write(f"Después de aplicar los filtros, se muestran **{len(filtered_df)}** registros.")
    st.markdown("---")

    # --- Pestañas de Visualización ---
    tab1, tab_edad_antiguedad, tab2, tab3 = st.tabs([
        "📊 Resumen de Dotación",
        "🎂 Edad y Antigüedad por Periodo",
        "🏢 Desglose por Categoría",
        "📋 Datos Brutos"
    ])

    with tab1:
        st.header('Resumen General de la Dotación')
        if filtered_df.empty:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            # Métricas y gráficos de resumen
            st.metric(label="Total de Empleados (filtrado)", value=len(filtered_df))
            
            st.subheader('Dotación por Periodo')
            periodo_counts = filtered_df['Periodo'].value_counts().reset_index()
            periodo_counts.columns = ['Periodo', 'Cantidad']
            chart_periodo = alt.Chart(periodo_counts).mark_bar().encode(
                x=alt.X('Periodo', sort=get_sorted_unique_options(df, 'Periodo')),
                y='Cantidad',
                tooltip=['Periodo', 'Cantidad']
            ).properties(title='Dotación Total por Periodo')
            st.altair_chart(chart_periodo, use_container_width=True)
            st.dataframe(periodo_counts)
            generate_download_buttons(periodo_counts, 'dotacion_por_periodo')
            
            # ... (se pueden añadir más gráficos de resumen de la lógica del PDF aquí)

    with tab_edad_antiguedad:
        st.header('Análisis de Edad y Antigüedad por Periodo')
        if filtered_df.empty:
            st.warning("No hay datos para mostrar.")
        else:
            # Gráfico de Edad
            st.subheader('Distribución por Rango de Edad por Periodo')
            chart_edad = alt.Chart(filtered_df).mark_bar().encode(
                x=alt.X('Rango Edad:N', sort=get_sorted_unique_options(df, 'Rango Edad')),
                y='count():Q',
                color='Relación:N',
                column='Periodo:N',
                tooltip=['count()']
            ).properties(title='Distribución por Edad')
            st.altair_chart(chart_edad, use_container_width=True)

            # Gráfico de Antigüedad
            st.subheader('Distribución por Rango de Antigüedad por Periodo')
            chart_antiguedad = alt.Chart(filtered_df).mark_bar().encode(
                x=alt.X('Rango Antiguedad:N', sort=get_sorted_unique_options(df, 'Rango Antiguedad')),
                y='count():Q',
                color='Relación:N',
                column='Periodo:N',
                tooltip=['count()']
            ).properties(title='Distribución por Antigüedad')
            st.altair_chart(chart_antiguedad, use_container_width=True)
            
    with tab2:
        st.header('Desglose Detallado por Categoría')
        if filtered_df.empty:
            st.warning("No hay datos para mostrar.")
        else:
            # Desglose por Gerencia
            st.subheader('Dotación por Gerencia por Periodo')
            chart_gerencia = alt.Chart(filtered_df).mark_bar().encode(
                x='Gerencia:N',
                y='count():Q',
                color='Gerencia:N',
                column='Periodo:N'
            ).properties(title='Dotación por Gerencia')
            st.altair_chart(chart_gerencia, use_container_width=True)
            
            # ... (se pueden añadir más gráficos de desglose de la lógica del PDF aquí)
            
    with tab3:
        st.header('Tabla de Datos Filtrados')
        st.dataframe(filtered_df)
        generate_download_buttons(filtered_df, 'datos_filtrados_dotacion')

else:
    st.info("⬆️ Esperando a que se suba un archivo Excel para comenzar el análisis.")
