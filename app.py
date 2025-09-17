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
.stMultiSelect div[role="listbox"] { /* Para el menú desplegable */
    background-color: #ffffff;
    border: 1px solid #e9ecef;
    border-radius: 0.5rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.stMultiSelect div[data-baseweb="tag"] {
    background-color: #3498DB !important; /* Azul clásico para los elementos seleccionados */
    border-radius: 0.25rem;
    padding: 0.2rem 0.5rem;
    margin: 0.1rem;
    color: white !important; /* Texto blanco */
}
.stMultiSelect div[data-baseweb="tag"] svg {
    fill: white !important; /* Color blanco para el icono 'x' */
}
</style>
""", unsafe_allow_html=True)

# --- Título de la Aplicación ---
st.title('🗓️ Dashboard de Dotación Anual 2025')
st.subheader('Análisis Interactivo de la Composición de la Dotación por Periodo')

# --- Funciones Auxiliares ---

def generate_download_buttons(df_to_download, filename_prefix):
    """Genera botones para descargar un DataFrame como CSV y Excel."""
    st.markdown("##### Opciones de Descarga:")
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
    df_excel = pd.DataFrame()
    try:
        df_excel = pd.read_excel(uploaded_file_obj, sheet_name='Dotacion_25')
    except Exception as e:
        st.error(f"ERROR CRÍTICO: No se pudo leer la hoja 'Dotacion_25'. Mensaje: {e}")
        return pd.DataFrame()

    if df_excel.empty:
        return pd.DataFrame()

    if 'LEGAJO' in df_excel.columns:
        df_excel['LEGAJO'] = pd.to_numeric(df_excel['LEGAJO'], errors='coerce')

    excel_col_fecha_ingreso_raw = 'Fecha ing.'
    excel_col_fecha_nacimiento_raw = 'Fecha Nac.'
    excel_col_rango_antiguedad_raw = 'Rango (Antigüedad)'
    excel_col_rango_edad_raw = 'Rango (Edad)'

    # --- RANGO ANTIGÜEDAD ---
    if excel_col_rango_antiguedad_raw in df_excel.columns and df_excel[excel_col_rango_antiguedad_raw].notna().sum() > 0:
        df_excel['Rango Antiguedad'] = df_excel[excel_col_rango_antiguedad_raw].astype(str).str.strip().str.lower()
    else:
        if excel_col_fecha_ingreso_raw in df_excel.columns:
            temp_fecha_ingreso = pd.to_datetime(df_excel[excel_col_fecha_ingreso_raw], errors='coerce')
            if temp_fecha_ingreso.notna().sum() > 0:
                df_excel['Antiguedad (años)'] = (datetime.now() - temp_fecha_ingreso).dt.days / 365.25
                bins_antiguedad = [0, 5, 10, 15, 20, 25, 30, 35, float('inf')]
                labels_antiguedad = ['de 0 a 5 años', 'de 5 a 10 años', 'de 11 a 15 años', 'de 16 a 20 años', 'de 21 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'más de 35 años']
                df_excel['Rango Antiguedad'] = pd.cut(df_excel['Antiguedad (años)'], bins=bins_antiguedad, labels=labels_antiguedad, right=False, include_lowest=True).astype(str).str.strip().str.lower()
            else:
                df_excel['Rango Antiguedad'] = 'no disponible'
        else:
            df_excel['Rango Antiguedad'] = 'no disponible'

    # --- RANGO EDAD ---
    if excel_col_rango_edad_raw in df_excel.columns and df_excel[excel_col_rango_edad_raw].notna().sum() > 0:
        df_excel['Rango Edad'] = df_excel[excel_col_rango_edad_raw].astype(str).str.strip().str.lower()
    else:
        if excel_col_fecha_nacimiento_raw in df_excel.columns:
            temp_fecha_nacimiento = pd.to_datetime(df_excel[excel_col_fecha_nacimiento_raw], errors='coerce')
            if temp_fecha_nacimiento.notna().sum() > 0:
                df_excel['Edad (años)'] = (datetime.now() - temp_fecha_nacimiento).dt.days / 365.25
                bins_edad = [0, 19, 25, 30, 35, 40, 45, 50, 55, 60, 65, float('inf')]
                labels_edad = ['de 0 a 19 años', 'de 19 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'de 36 a 40 años', 'de 41 a 45 años', 'de 46 a 50 años', 'de 51 a 55 años', 'de 56 a 60 años', 'de 61 a 65 años', 'más de 65 años']
                df_excel['Rango Edad'] = pd.cut(df_excel['Edad (años)'], bins=bins_edad, labels=labels_edad, right=False, include_lowest=True).astype(str).str.strip().str.lower()
            else:
                df_excel['Rango Edad'] = 'no disponible'
        else:
            df_excel['Rango Edad'] = 'no disponible'

    # --- PERIODO ---
    if 'Periodo' in df_excel.columns:
        try:
            temp_periodo = pd.to_datetime(df_excel['Periodo'], errors='coerce')
            if temp_periodo.notna().any():
                spanish_months_map = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
                df_excel['Periodo'] = temp_periodo.dt.month.map(spanish_months_map).astype(str)
            else:
                df_excel['Periodo'] = df_excel['Periodo'].astype(str).str.strip().str.capitalize()
        except Exception:
            df_excel['Periodo'] = df_excel['Periodo'].astype(str).str.strip().str.capitalize()
    
    # --- LIMPIEZA FINAL ---
    text_cols_for_filters_charts = ['Gerencia', 'Relación', 'Sexo', 'Función', 'Distrito', 'Ministerio', 'Rango Antiguedad', 'Rango Edad', 'Periodo', 'Nivel']
    for col in text_cols_for_filters_charts:
        if col not in df_excel.columns:
            df_excel[col] = 'no disponible'
        df_excel[col] = df_excel[col].astype(str).replace(['None', 'nan', ''], 'no disponible').str.strip()
        if col in ['Rango Antiguedad', 'Rango Edad']:
             df_excel[col] = df_excel[col].str.lower()
        elif col == 'Periodo':
             df_excel[col] = df_excel[col].str.capitalize()


    return df_excel

def get_sorted_unique_options(dataframe, column_name):
    """Obtiene opciones únicas y ordenadas para los filtros."""
    if column_name in dataframe.columns:
        unique_values = dataframe[column_name].dropna().unique().tolist()
        
        if column_name == 'Rango Antiguedad':
            order = ['de 0 a 5 años', 'de 5 a 10 años', 'de 11 a 15 años', 'de 16 a 20 años', 'de 21 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'más de 35 años', 'no disponible']
            # Mapea los valores existentes al orden deseado
            present_values = [val for val in order if val in unique_values]
            # Agrega cualquier valor no esperado al final
            other_values = [val for val in unique_values if val not in order]
            return present_values + sorted(other_values)
        
        elif column_name == 'Rango Edad':
            order = ['de 0 a 19 años', 'de 19 a 25 años', 'de 26 a 30 años', 'de 31 a 35 años', 'de 36 a 40 años', 'de 41 a 45 años', 'de 46 a 50 años', 'de 51 a 55 años', 'de 56 a 60 años', 'de 61 a 65 años', 'más de 65 años', 'no disponible']
            present_values = [val for val in order if val in unique_values]
            other_values = [val for val in unique_values if val not in order]
            return present_values + sorted(other_values)
            
        elif column_name == 'Periodo':
            month_order = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12, 'No disponible': 99}
            return sorted(unique_values, key=lambda x: month_order.get(x, 99))
        
        return sorted(unique_values)
    return ['no disponible']


# --- Cuerpo Principal de la Aplicación ---
uploaded_file = st.file_uploader("📂 Por favor, sube tu archivo 'Dotacion_25.xlsx'", type="xlsx")

if uploaded_file is not None:
    df = load_and_clean_data(uploaded_file)

    if df.empty:
        st.warning("El archivo no pudo ser procesado. Verifica el contenido y el nombre de la hoja.")
        st.stop()

    st.success(f"Se ha cargado un total de **{len(df)}** registros de empleados.")
    st.markdown("---")

    # --- Barra Lateral de Filtros ---
    st.sidebar.header('Filtros del Dashboard')
    
    all_periodos = get_sorted_unique_options(df, 'Periodo')
    selected_periodos = st.sidebar.multiselect('Selecciona Periodo(s):', all_periodos, default=all_periodos)

    all_gerencias = get_sorted_unique_options(df, 'Gerencia')
    selected_gerencias = st.sidebar.multiselect('Selecciona Gerencia(s):', all_gerencias, default=all_gerencias)

    all_relaciones = get_sorted_unique_options(df, 'Relación')
    selected_relaciones = st.sidebar.multiselect('Selecciona Relación(es):', all_relaciones, default=all_relaciones)

    all_sexos = get_sorted_unique_options(df, 'Sexo')
    selected_sexos = st.sidebar.multiselect('Selecciona Sexo(s):', all_sexos, default=all_sexos)

    all_rangos_antiguedad = get_sorted_unique_options(df, 'Rango Antiguedad')
    selected_rangos_antiguedad = st.sidebar.multiselect('Selecciona Rango(s) de Antigüedad:', all_rangos_antiguedad, default=all_rangos_antiguedad)

    all_rangos_edad = get_sorted_unique_options(df, 'Rango Edad')
    selected_rangos_edad = st.sidebar.multiselect('Selecciona Rango(s) de Edad:', all_rangos_edad, default=all_rangos_edad)

    all_funciones = get_sorted_unique_options(df, 'Función')
    selected_funciones = st.sidebar.multiselect('Selecciona Función(es):', all_funciones, default=all_funciones)

    all_distritos = get_sorted_unique_options(df, 'Distrito')
    selected_distritos = st.sidebar.multiselect('Selecciona Distrito(s):', all_distritos, default=all_distritos)
    
    all_ministerios = get_sorted_unique_options(df, 'Ministerio')
    selected_ministerios = st.sidebar.multiselect('Selecciona Ministerio(s):', all_ministerios, default=all_ministerios)
    
    all_niveles = get_sorted_unique_options(df, 'Nivel')
    selected_niveles = st.sidebar.multiselect('Selecciona Nivel(es):', all_niveles, default=all_niveles)

    # --- Lógica de Filtrado ---
    query_parts = []
    if selected_periodos: query_parts.append("`Periodo` in @selected_periodos")
    if selected_gerencias: query_parts.append("`Gerencia` in @selected_gerencias")
    if selected_relaciones: query_parts.append("`Relación` in @selected_relaciones")
    if selected_sexos: query_parts.append("`Sexo` in @selected_sexos")
    if selected_rangos_antiguedad: query_parts.append("`Rango Antiguedad` in @selected_rangos_antiguedad")
    if selected_rangos_edad: query_parts.append("`Rango Edad` in @selected_rangos_edad")
    if selected_funciones: query_parts.append("`Función` in @selected_funciones")
    if selected_distritos: query_parts.append("`Distrito` in @selected_distritos")
    if selected_ministerios: query_parts.append("`Ministerio` in @selected_ministerios")
    if selected_niveles: query_parts.append("`Nivel` in @selected_niveles")
    
    if query_parts:
        filtered_df = df.query(" and ".join(query_parts))
    else:
        filtered_df = df.copy()


    st.write(f"Después de aplicar los filtros, se muestran **{len(filtered_df)}** registros.")
    st.markdown("---")

    # --- Pestañas de Visualización ---
    tab1, tab_edad_antiguedad, tab2, tab3 = st.tabs([
        "📊 Resumen de Dotación",
        "⏳ Edad y Antigüedad por Periodo",
        "📈 Desglose por Categoría",
        "📋 Datos Brutos"
    ])

    # --- PESTAÑA 1: RESUMEN (NO TOCAR) ---
    with tab1:
        st.header('Resumen General de la Dotación')
        if filtered_df.empty:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            st.metric(label="Total de Empleados (filtrado)", value=len(filtered_df))
            
            # --- Dotación por Periodo (Total) ---
            st.subheader('Dotación por Periodo (Total)')
            periodo_counts = filtered_df['Periodo'].value_counts().reset_index()
            periodo_counts.columns = ['Periodo', 'Cantidad']
            
            min_val = periodo_counts['Cantidad'].min()
            max_val = periodo_counts['Cantidad'].max()
            padding = (max_val - min_val) * 0.1 
            
            chart_periodo = alt.Chart(periodo_counts).mark_line(point=True).encode(
                x=alt.X('Periodo', sort=all_periodos),
                y=alt.Y('Cantidad', scale=alt.Scale(domain=[min_val - padding, max_val + padding])),
                tooltip=['Periodo', 'Cantidad']
            ).properties(title='Evolución de la Dotación Total por Periodo')
            st.altair_chart(chart_periodo, use_container_width=True)
            st.dataframe(periodo_counts)
            generate_download_buttons(periodo_counts, 'dotacion_total_por_periodo')
            st.markdown('---')

            # --- Distribución por Sexo por Periodo ---
            st.subheader('Distribución por Sexo por Periodo')
            sexo_counts = filtered_df.groupby(['Periodo', 'Sexo']).size().reset_index(name='Cantidad')
            chart_sexo = alt.Chart(sexo_counts).mark_bar().encode(
                x=alt.X('Periodo:N', sort=all_periodos),
                y='Cantidad:Q',
                color='Sexo:N',
                xOffset='Sexo:N',
                tooltip=['Periodo', 'Sexo', 'Cantidad']
            ).properties(title='Distribución por Sexo por Periodo')
            st.altair_chart(chart_sexo, use_container_width=True)
            
            sexo_pivot = sexo_counts.pivot_table(index='Periodo', columns='Sexo', values='Cantidad', fill_value=0)
            sexo_pivot['Total'] = sexo_pivot.sum(axis=1)
            st.dataframe(sexo_pivot.reset_index())
            generate_download_buttons(sexo_pivot.reset_index(), 'distribucion_sexo_por_periodo')
            st.markdown('---')

            # --- Distribución por Relación por Periodo ---
            st.subheader('Distribución por Relación por Periodo')
            relacion_counts = filtered_df.groupby(['Periodo', 'Relación']).size().reset_index(name='Cantidad')
            chart_relacion = alt.Chart(relacion_counts).mark_bar().encode(
                x=alt.X('Periodo:N', sort=all_periodos),
                y='Cantidad:Q',
                color='Relación:N',
                xOffset='Relación:N',
                tooltip=['Periodo', 'Relación', 'Cantidad']
            ).properties(title='Distribución por Relación por Periodo')
            st.altair_chart(chart_relacion, use_container_width=True)

            relacion_pivot = relacion_counts.pivot_table(index='Periodo', columns='Relación', values='Cantidad', fill_value=0)
            relacion_pivot['Total'] = relacion_pivot.sum(axis=1)
            st.dataframe(relacion_pivot.reset_index())
            generate_download_buttons(relacion_pivot.reset_index(), 'distribucion_relacion_por_periodo')
            st.markdown('---')

            # --- Variación Mensual ---
            st.subheader('Variación Mensual de Dotación (Total)')
            month_order_map = {name: i for i, name in enumerate(all_periodos) if name != 'No disponible'}
            
            periodo_var_counts = filtered_df.groupby('Periodo').size().reset_index(name='Cantidad_Actual')
            periodo_var_counts['sort_key'] = periodo_var_counts['Periodo'].map(month_order_map)
            periodo_var_counts = periodo_var_counts.sort_values('sort_key').drop(columns='sort_key').reset_index(drop=True)
            
            periodo_var_counts['Cantidad_Mes_Anterior'] = periodo_var_counts['Cantidad_Actual'].shift(1)
            periodo_var_counts['Variacion_Cantidad'] = periodo_var_counts['Cantidad_Actual'] - periodo_var_counts['Cantidad_Mes_Anterior']
            
            display_var_table = periodo_var_counts.copy().fillna('')
            st.dataframe(display_var_table)
            generate_download_buttons(display_var_table, 'variacion_mensual_total')
            
            chart_data_var = periodo_var_counts.dropna(subset=['Variacion_Cantidad'])
            
            bar_chart_var = alt.Chart(chart_data_var).mark_bar().encode(
                x=alt.X('Periodo', sort=all_periodos, title='Periodo'),
                y=alt.Y('Variacion_Cantidad', title='Variación de Empleados'),
                color=alt.condition(
                    alt.datum.Variacion_Cantidad > 0,
                    alt.value("green"),
                    alt.value("red")
                ),
                tooltip=['Periodo', 'Variacion_Cantidad']
            ).properties(
                title='Variación Mensual de Dotación'
            )
            st.altair_chart(bar_chart_var, use_container_width=True)

    # --- PESTAÑA 2: EDAD Y ANTIGÜEDAD (MODIFICADA) ---
    with tab_edad_antiguedad:
        st.header('Análisis de Edad y Antigüedad por Periodo')
        if filtered_df.empty or not selected_periodos:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            # Selector de período para esta pestaña
            periodo_a_mostrar_edad = st.selectbox(
                'Selecciona un Periodo para visualizar:',
                selected_periodos,
                index=len(selected_periodos) - 1, # Default al último período
                key='periodo_selector_edad'
            )
            
            # Filtrar el DF solo para el período seleccionado
            df_periodo_edad = filtered_df[filtered_df['Periodo'] == periodo_a_mostrar_edad]
            total_empleados_periodo_edad = len(df_periodo_edad)

            # --- Histograma Edad ---
            st.subheader(f'Distribución por Rango de Edad para {periodo_a_mostrar_edad}')
            chart_edad_hist = alt.Chart(df_periodo_edad).mark_bar().encode(
                x=alt.X('Rango Edad:N', sort=all_rangos_edad),
                y='count():Q',
                color='Relación:N',
                tooltip=['count()', 'Relación']
            ).properties(title=f'Distribución por Edad en {periodo_a_mostrar_edad}')
            st.altair_chart(chart_edad_hist, use_container_width=True)
            
            edad_table = df_periodo_edad.groupby(['Rango Edad', 'Relación']).size().unstack(fill_value=0)
            edad_table['Total'] = edad_table.sum(axis=1)
            
            if total_empleados_periodo_edad > 0:
                edad_table['% sobre Total Periodo'] = (edad_table['Total'] / total_empleados_periodo_edad * 100).map('{:.2f}%'.format)
            else:
                edad_table['% sobre Total Periodo'] = '0.00%'

            # **NUEVO: Añadir fila de totales a la tabla de Edad**
            edad_table_display = edad_table.reset_index()
            total_row_edad_values = {col: edad_table_display[col].sum() for col in edad_table_display.columns if col not in ['Rango Edad', '% sobre Total Periodo']}
            total_row_edad_values['Rango Edad'] = 'Total'
            total_row_edad_values['% sobre Total Periodo'] = '100.00%'
            total_row_edad_df = pd.DataFrame([total_row_edad_values])
            edad_table_with_total = pd.concat([edad_table_display, total_row_edad_df], ignore_index=True)

            st.dataframe(edad_table_with_total)
            generate_download_buttons(edad_table_with_total, f'distribucion_edad_{periodo_a_mostrar_edad}')
            st.markdown('---')

            # --- Histograma Antigüedad ---
            st.subheader(f'Distribución por Rango de Antigüedad para {periodo_a_mostrar_edad}')
            chart_antiguedad_hist = alt.Chart(df_periodo_edad).mark_bar().encode(
                x=alt.X('Rango Antiguedad:N', sort=all_rangos_antiguedad),
                y='count():Q',
                color='Relación:N',
                tooltip=['count()', 'Relación']
            ).properties(title=f'Distribución por Antigüedad en {periodo_a_mostrar_edad}')
            st.altair_chart(chart_antiguedad_hist, use_container_width=True)

            antiguedad_table = df_periodo_edad.groupby(['Rango Antiguedad', 'Relación']).size().unstack(fill_value=0)
            antiguedad_table['Total'] = antiguedad_table.sum(axis=1)
            
            if total_empleados_periodo_edad > 0:
                antiguedad_table['% sobre Total Periodo'] = (antiguedad_table['Total'] / total_empleados_periodo_edad * 100).map('{:.2f}%'.format)
            else:
                antiguedad_table['% sobre Total Periodo'] = '0.00%'
            
            # **NUEVO: Añadir fila de totales a la tabla de Antigüedad**
            antiguedad_table_display = antiguedad_table.reset_index()
            total_row_ant_values = {col: antiguedad_table_display[col].sum() for col in antiguedad_table_display.columns if col not in ['Rango Antiguedad', '% sobre Total Periodo']}
            total_row_ant_values['Rango Antiguedad'] = 'Total'
            total_row_ant_values['% sobre Total Periodo'] = '100.00%'
            total_row_ant_df = pd.DataFrame([total_row_ant_values])
            antiguedad_table_with_total = pd.concat([antiguedad_table_display, total_row_ant_df], ignore_index=True)

            st.dataframe(antiguedad_table_with_total)
            generate_download_buttons(antiguedad_table_with_total, f'distribucion_antiguedad_{periodo_a_mostrar_edad}')

    # --- PESTAÑA 3: DESGLOSE (NO TOCAR) ---
    with tab2:
        st.header('Desglose Detallado por Categoría por Periodo')
        if filtered_df.empty or not selected_periodos:
            st.warning("No hay datos para mostrar con los filtros seleccionados.")
        else:
            # Selector de período para esta pestaña
            periodo_a_mostrar_desglose = st.selectbox(
                'Selecciona un Periodo para visualizar:',
                selected_periodos,
                index=len(selected_periodos) - 1, # Default al último período
                key='periodo_selector_desglose'
            )

            # Filtrar el DF solo para el período seleccionado
            df_periodo_desglose = filtered_df[filtered_df['Periodo'] == periodo_a_mostrar_desglose]
            total_empleados_periodo_desglose = len(df_periodo_desglose)

            categorias = ['Gerencia', 'Ministerio', 'Función', 'Distrito', 'Nivel']
            for cat in categorias:
                st.subheader(f'Dotación por {cat} para {periodo_a_mostrar_desglose}')
                chart = alt.Chart(df_periodo_desglose).mark_bar().encode(
                    x=alt.X(f'{cat}:N'),
                    y='count():Q',
                    color=f'{cat}:N',
                    tooltip=['count()', cat]
                ).resolve_scale(x='independent')
                st.altair_chart(chart, use_container_width=True)
                
                table_data = df_periodo_desglose.groupby(cat).size().reset_index(name='Cantidad')
                
                if total_empleados_periodo_desglose > 0:
                    table_data['%'] = (table_data['Cantidad'] / total_empleados_periodo_desglose * 100).map('{:.2f}%'.format)
                else:
                    table_data['%'] = '0.00%'
                
                total_row = pd.DataFrame({
                    cat: ['Total'],
                    'Cantidad': [table_data['Cantidad'].sum()],
                    '%': ['100.00%']
                })
                table_data_with_total = pd.concat([table_data, total_row], ignore_index=True)
                
                st.dataframe(table_data_with_total)
                generate_download_buttons(table_data_with_total, f'dotacion_{cat.lower()}_{periodo_a_mostrar_desglose}')
                st.markdown('---')

    # --- PESTAÑA 4: DATOS BRUTOS ---
    with tab3:
        st.header('Tabla de Datos Filtrados')
        st.dataframe(filtered_df)
        generate_download_buttons(filtered_df, 'datos_filtrados_dotacion')

else:
    st.info("⬆️ Esperando a que se suba un archivo Excel para comenzar el análisis.")

