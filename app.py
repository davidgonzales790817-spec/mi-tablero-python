import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime
import re
import numpy as np
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Tablero Presupuestal IPEN", layout="wide")

# Estilo CSS personalizado para mejorar la visualización
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        font-size: 16px;
        font-weight: 600;
    }
    .report-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Logo institucional
st.sidebar.image("https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png", width=250)

# Título principal
st.title("📊 INSTITUTO PERUANO DE ENERGÍA NUCLEAR")
st.markdown("### EJECUCIÓN PRESUPUESTAL")

# Inicializar session state para almacenar datos
if 'df_datos' not in st.session_state:
    st.session_state.df_datos = None
if 'datos_manuales' not in st.session_state:
    st.session_state.datos_manuales = None

# ==================== SECCIÓN DE CARGA DE DATOS ====================
st.sidebar.header("📁 Carga de Datos")

# Opción de carga
opcion_carga = st.sidebar.radio(
    "Seleccione método de carga:",
    ["Cargar archivo Excel", "Ingresar datos manualmente"],
    help="Puede cargar un archivo Excel del SIAF o ingresar los datos manualmente"
)

if opcion_carga == "Cargar archivo Excel":
    archivo = st.sidebar.file_uploader("Seleccionar archivo Excel", type=["xls", "xlsx"])
    
    if archivo:
        # Crear carpeta de respaldo
        carpeta_respaldo = "Respaldo_Data"
        os.makedirs(carpeta_respaldo, exist_ok=True)
        ruta_archivo = os.path.join(carpeta_respaldo, archivo.name)
        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())
        
        try:
            # Leer archivo Excel
            df = pd.read_excel(ruta_archivo)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Detectar columnas del SIAF
            col_pim = 'mto_pim' if 'mto_pim' in df.columns else None
            if col_pim is None:
                for col in df.columns:
                    if 'pim' in col:
                        col_pim = col
                        break
            
            if col_pim:
                df.rename(columns={col_pim: "PIM"}, inplace=True)
                
                # Detectar Certificado
                if 'mto_certificado' in df.columns:
                    df.rename(columns={'mto_certificado': "Certificado"}, inplace=True)
                else:
                    df["Certificado"] = 0
                
                # Detectar Compromiso
                if 'mto_compro_anual' in df.columns:
                    df.rename(columns={'mto_compro_anual': "Compromiso"}, inplace=True)
                else:
                    df["Compromiso"] = 0
                
                # Detectar columnas de devengado mensual
                meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                
                for i, mes in enumerate(meses, 1):
                    col_name = f'mto_devenga_{i:02d}'
                    if col_name in df.columns:
                        df.rename(columns={col_name: f"Devengado_{mes}"}, inplace=True)
                    else:
                        df[f"Devengado_{mes}"] = 0
                
                # Detectar tipo de gasto (Actividad/Inversión)
                if 'tipo_act_obra_ac' in df.columns:
                    df['Tipo_Gasto'] = df['tipo_act_obra_ac'].apply(
                        lambda x: 'ACTIVIDAD' if str(x).startswith('5') else ('INVERSION' if str(x).startswith('4') else 'OTROS')
                    )
                else:
                    df['Tipo_Gasto'] = 'ACTIVIDAD'
                
                # Detectar genérica
                if 'generica' in df.columns:
                    df['Genérica'] = df['generica']
                else:
                    df['Genérica'] = 'General'
                
                # Calcular Devengado Total
                devengado_cols = [f"Devengado_{mes}" for mes in meses]
                df["Devengado_Total"] = df[devengado_cols].sum(axis=1)
                df["Saldo"] = df["PIM"] - df["Devengado_Total"]
                
                st.session_state.df_datos = df
                st.sidebar.success("✅ Archivo cargado correctamente")
                
        except Exception as e:
            st.sidebar.error(f"Error al procesar el archivo: {str(e)}")

elif opcion_carga == "Ingresar datos manualmente":
    st.sidebar.markdown("### Ingreso Manual de Datos")
    
    with st.sidebar.form("form_datos_manuales"):
        tipo_gasto = st.selectbox("Tipo de Gasto", ["ACTIVIDAD", "INVERSION"])
        generica = st.selectbox("Genérica de Gasto", 
                               ["PERSONAL Y OBLIGACIONES SOCIALES", 
                                "PENSIONES Y OTRAS PRESTACIONES SOCIALES",
                                "BIENES Y SERVICIOS",
                                "OTROS GASTOS",
                                "ADQUISICION DE ACTIVOS NO FINANCIEROS"])
        
        pim = st.number_input("PIM (S/.)", min_value=0.0, step=1000.0, format="%.2f")
        certificado = st.number_input("Certificado (S/.)", min_value=0.0, step=1000.0, format="%.2f")
        compromiso = st.number_input("Compromiso (S/.)", min_value=0.0, step=1000.0, format="%.2f")
        
        st.markdown("**Devengado Mensual (S/.)**")
        cols = st.columns(4)
        devengado_mensual = []
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        for i, mes in enumerate(meses):
            with cols[i % 4]:
                valor = st.number_input(mes, key=f"dev_{mes}", min_value=0.0, step=100.0, format="%.2f", value=0.0)
                devengado_mensual.append(valor)
        
        submit = st.form_submit_button("Agregar Datos")
        
        if submit and pim > 0:
            nuevo_registro = {
                'Tipo_Gasto': tipo_gasto,
                'Genérica': generica,
                'PIM': pim,
                'Certificado': certificado,
                'Compromiso': compromiso,
                'Devengado_Total': sum(devengado_mensual),
                'Saldo': pim - sum(devengado_mensual)
            }
            
            # Agregar devengados mensuales
            for mes, valor in zip(meses, devengado_mensual):
                nuevo_registro[f'Devengado_{mes}'] = valor
            
            if st.session_state.datos_manuales is None:
                st.session_state.datos_manuales = pd.DataFrame([nuevo_registro])
            else:
                st.session_state.datos_manuales = pd.concat([st.session_state.datos_manuales, 
                                                            pd.DataFrame([nuevo_registro])], 
                                                            ignore_index=True)
            
            st.session_state.df_datos = st.session_state.datos_manuales
            st.sidebar.success("✅ Datos agregados correctamente")
    
    if st.session_state.datos_manuales is not None and len(st.session_state.datos_manuales) > 0:
        if st.sidebar.button("🗑️ Limpiar todos los datos manuales"):
            st.session_state.datos_manuales = None
            st.session_state.df_datos = None
            st.sidebar.success("Datos limpiados")
            st.rerun()

# ==================== VISUALIZACIÓN DE DATOS ====================
if st.session_state.df_datos is not None:
    df = st.session_state.df_datos.copy()
    
    # Filtros en la barra lateral
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por Tipo de Gasto
    tipos_gasto = ["TODOS"] + sorted(df['Tipo_Gasto'].unique().tolist())
    filtro_tipo = st.sidebar.selectbox("Filtrar por Tipo de Gasto", tipos_gasto)
    
    # Filtro por Genérica
    genericas = ["TODAS"] + sorted(df['Genérica'].unique().tolist())
    filtro_generica = st.sidebar.selectbox("Filtrar por Genérica", genericas)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if filtro_tipo != "TODOS":
        df_filtrado = df_filtrado[df_filtrado['Tipo_Gasto'] == filtro_tipo]
    if filtro_generica != "TODAS":
        df_filtrado = df_filtrado[df_filtrado['Genérica'] == filtro_generica]
    
    if df_filtrado.empty:
        st.warning("No hay datos para los filtros seleccionados")
        st.stop()
    
    # Calcular totales
    pim_total = df_filtrado["PIM"].sum()
    certificado_total = df_filtrado["Certificado"].sum()
    compromiso_total = df_filtrado["Compromiso"].sum()
    devengado_total = df_filtrado["Devengado_Total"].sum()
    saldo_total = pim_total - devengado_total
    
    # ==================== TABLA RESUMEN PRINCIPAL ====================
    st.markdown("### I. EJECUCIÓN PRESUPUESTAL")
    
    # Crear tabla en formato HTML
    table_html = """
    <table style="width:100%; border-collapse: collapse; margin-bottom: 20px;">
        <thead>
            <tr style="background-color: #2c3e50; color: white;">
                <th style="padding: 12px; text-align: left;">DETALLE</th>
                <th style="padding: 12px; text-align: right;">PIA</th>
                <th style="padding: 12px; text-align: right;">PIM</th>
                <th style="padding: 12px; text-align: right;">Certificado</th>
                <th style="padding: 12px; text-align: right;">Compromiso</th>
                <th style="padding: 12px; text-align: right;">Devengado</th>
                <th style="padding: 12px; text-align: right;">Saldo por Ejecutar</th>
            </tr>
        </thead>
        <tbody>
    """
    
    # Agrupar por Tipo de Gasto
    for tipo in df_filtrado['Tipo_Gasto'].unique():
        df_tipo = df_filtrado[df_filtrado['Tipo_Gasto'] == tipo]
        pim_tipo = df_tipo["PIM"].sum()
        cert_tipo = df_tipo["Certificado"].sum()
        comp_tipo = df_tipo["Compromiso"].sum()
        dev_tipo = df_tipo["Devengado_Total"].sum()
        saldo_tipo = pim_tipo - dev_tipo
        
        cert_pct = (cert_tipo / pim_tipo * 100) if pim_tipo > 0 else 0
        comp_pct = (comp_tipo / pim_tipo * 100) if pim_tipo > 0 else 0
        dev_pct = (dev_tipo / pim_tipo * 100) if pim_tipo > 0 else 0
        
        table_html += f"""
            <tr style="background-color: #ecf0f1;">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><b>{tipo}</b></td>
                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {pim_tipo:,.2f}</td>
                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {pim_tipo:,.2f}</td>
                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {cert_tipo:,.2f}<br><span style="font-size: 0.8em;">({cert_pct:.1f}%)</span></td>
                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {comp_tipo:,.2f}<br><span style="font-size: 0.8em;">({comp_pct:.1f}%)</span></td>
                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {dev_tipo:,.2f}<br><span style="font-size: 0.8em;">({dev_pct:.1f}%)</span></td>
                <td style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {saldo_tipo:,.2f}</td>
            </tr>
        """
        
        # Subdetalle por genérica dentro de cada tipo
        df_genericas = df_tipo.groupby('Genérica').agg({
            'PIM': 'sum',
            'Certificado': 'sum',
            'Compromiso': 'sum',
            'Devengado_Total': 'sum'
        }).reset_index()
        
        for _, row in df_genericas.iterrows():
            pim_gen = row['PIM']
            cert_gen = row['Certificado']
            comp_gen = row['Compromiso']
            dev_gen = row['Devengado_Total']
            saldo_gen = pim_gen - dev_gen
            
            cert_pct_gen = (cert_gen / pim_gen * 100) if pim_gen > 0 else 0
            comp_pct_gen = (comp_gen / pim_gen * 100) if pim_gen > 0 else 0
            dev_pct_gen = (dev_gen / pim_gen * 100) if pim_gen > 0 else 0
            
            table_html += f"""
                <tr>
                    <td style="padding: 8px 10px 8px 30px; border-bottom: 1px solid #ddd;">{row['Genérica']}</td>
                    <td style="padding: 8px 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {pim_gen:,.2f}</td>
                    <td style="padding: 8px 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {pim_gen:,.2f}</td>
                    <td style="padding: 8px 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {cert_gen:,.2f}<br><span style="font-size: 0.8em;">({cert_pct_gen:.1f}%)</span></td>
                    <td style="padding: 8px 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {comp_gen:,.2f}<br><span style="font-size: 0.8em;">({comp_pct_gen:.1f}%)</span></td>
                    <td style="padding: 8px 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {dev_gen:,.2f}<br><span style="font-size: 0.8em;">({dev_pct_gen:.1f}%)</span></td>
                    <td style="padding: 8px 10px; text-align: right; border-bottom: 1px solid #ddd;">S/ {saldo_gen:,.2f}</td>
                </tr>
            """
    
    # Fila de total general
    cert_total_pct = (certificado_total / pim_total * 100) if pim_total > 0 else 0
    comp_total_pct = (compromiso_total / pim_total * 100) if pim_total > 0 else 0
    dev_total_pct = (devengado_total / pim_total * 100) if pim_total > 0 else 0
    
    table_html += f"""
        <tr style="background-color: #2c3e50; color: white; font-weight: bold;">
            <td style="padding: 12px;">Total general</td>
            <td style="padding: 12px; text-align: right;">S/ {pim_total:,.2f}</td>
            <td style="padding: 12px; text-align: right;">S/ {pim_total:,.2f}</td>
            <td style="padding: 12px; text-align: right;">S/ {certificado_total:,.2f}<br><span style="font-size: 0.8em;">({cert_total_pct:.1f}%)</span></td>
            <td style="padding: 12px; text-align: right;">S/ {compromiso_total:,.2f}<br><span style="font-size: 0.8em;">({comp_total_pct:.1f}%)</span></td>
            <td style="padding: 12px; text-align: right;">S/ {devengado_total:,.2f}<br><span style="font-size: 0.8em;">({dev_total_pct:.1f}%)</span></td>
            <td style="padding: 12px; text-align: right;">S/ {saldo_total:,.2f}</td>
        </tr>
    </tbody>
    </table>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)
    
    # ==================== GRÁFICOS GAUGE ====================
    st.markdown("### Indicadores de Ejecución")
    
    col1, col2, col3 = st.columns(3)
    
    def crear_gauge(valor, total, titulo, color, subtitulo=""):
        porcentaje = round(valor / total * 100 if total > 0 else 0, 2)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=porcentaje,
            number={'suffix': "%", 'font': {'size': 36, 'color': color}},
            title={
                'text': f"<b>{titulo}</b><br><span style='font-size:12px'>{subtitulo}</span>",
                'font': {'size': 18}
            },
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkgray", 'tickfont': {'size': 10}},
                'bar': {'color': color, 'thickness': 0.3},
                'bgcolor': "white",
                'borderwidth': 1,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#f2f2f2'},
                    {'range': [50, 80], 'color': '#e8f5e9'},
                    {'range': [80, 100], 'color': '#c8e6c9'},
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.add_annotation(
            x=0.5,
            y=-0.3,
            xref="paper",
            yref="paper",
            text=f"S/ {valor:,.2f}",
            showarrow=False,
            font=dict(size=14, color=color),
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        fig.update_layout(
            height=280,
            margin=dict(l=30, r=30, t=80, b=30),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    with col1:
        fig_cert = crear_gauge(certificado_total, pim_total, "Certificado", "#1f77b4", f"de S/ {pim_total:,.0f}")
        st.plotly_chart(fig_cert, use_container_width=True, key="gauge_cert")
    
    with col2:
        fig_comp = crear_gauge(compromiso_total, pim_total, "Compromiso", "#ff7f0e", f"de S/ {pim_total:,.0f}")
        st.plotly_chart(fig_comp, use_container_width=True, key="gauge_comp")
    
    with col3:
        fig_dev = crear_gauge(devengado_total, pim_total, "Devengado", "#2ca02c", f"de S/ {pim_total:,.0f}")
        st.plotly_chart(fig_dev, use_container_width=True, key="gauge_dev")
    
    # ==================== EVOLUCIÓN MENSUAL ====================
    st.markdown("### II. EJECUCIÓN MENSUALIZADA")
    
    # Preparar datos mensuales
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    # Crear DataFrame con datos mensuales por tipo
    datos_mensuales = []
    
    for tipo in df_filtrado['Tipo_Gasto'].unique():
        df_tipo = df_filtrado[df_filtrado['Tipo_Gasto'] == tipo]
        for mes in meses:
            col_mes = f'Devengado_{mes}'
            if col_mes in df_tipo.columns:
                monto = df_tipo[col_mes].sum()
                datos_mensuales.append({
                    'Tipo': tipo,
                    'Mes': mes,
                    'Monto': monto
                })
    
    if datos_mensuales:
        df_mensual = pd.DataFrame(datos_mensuales)
        
        # Calcular totales mensuales
        totales_mensuales = df_mensual.groupby('Mes')['Monto'].sum().reset_index()
        
        # Crear gráfico de barras apiladas
        fig = go.Figure()
        
        colores_tipo = {"ACTIVIDAD": "#1f77b4", "INVERSION": "#ff7f0e", "OTROS": "#d3d3d3"}
        
        for tipo in df_mensual['Tipo'].unique():
            df_tipo_mes = df_mensual[df_mensual['Tipo'] == tipo]
            color = colores_tipo.get(tipo, "#1f77b4")
            
            fig.add_trace(go.Bar(
                name=tipo,
                x=df_tipo_mes['Mes'],
                y=df_tipo_mes['Monto'],
                text=df_tipo_mes['Monto'].apply(lambda x: f"S/ {x:,.0f}"),
                textposition='inside',
                textfont_size=10,
                marker_color=color,
                hovertemplate="<b>%{x}</b><br>" +
                            f"{tipo}<br>" +
                            "Monto: S/ %{y:,.0f}<br>" +
                            "<extra></extra>"
            ))
        
        # Agregar anotaciones de totales
        for _, row in totales_mensuales.iterrows():
            total_mes = row['Monto']
            max_y = df_mensual[df_mensual['Mes'] == row['Mes']]['Monto'].sum()
            
            fig.add_annotation(
                x=row['Mes'],
                y=max_y,
                text=f"<b>S/ {total_mes:,.0f}</b>",
                showarrow=False,
                yshift=15,
                font=dict(size=11, color="black", family="Arial Black"),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="black",
                borderwidth=1,
                borderpad=4
            )
        
        fig.update_layout(
            barmode='stack',
            title="Programado vs Ejecutado",
            xaxis_title="Mes",
            yaxis_title="Monto (S/.)",
            hovermode='x unified',
            legend_title="Tipo de Gasto",
            showlegend=True,
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor='white',
            xaxis=dict(gridcolor='lightgray', tickangle=45),
            yaxis=dict(gridcolor='lightgray')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabla mensual
        with st.expander("Ver datos detallados mensuales"):
            # Crear tabla pivot
            pivot_mensual = df_mensual.pivot_table(
                values='Monto',
                index='Tipo',
                columns='Mes',
                aggfunc='sum',
                fill_value=0
            )
            
            # Agregar fila de total
            total_fila = pivot_mensual.sum().to_frame().T
            total_fila.index = ['TOTAL']
            pivot_mensual = pd.concat([pivot_mensual, total_fila])
            
            # Formatear
            for col in pivot_mensual.columns:
                pivot_mensual[col] = pivot_mensual[col].apply(lambda x: f"S/ {x:,.2f}")
            
            st.dataframe(pivot_mensual, use_container_width=True)
    
    # ==================== TABLA POR GENÉRICA ====================
    st.markdown("### III. RESULTADOS POR GENÉRICA")
    
    # Resumen por genérica
    resumen_generica = df_filtrado.groupby('Genérica').agg({
        'PIM': 'sum',
        'Certificado': 'sum',
        'Compromiso': 'sum',
        'Devengado_Total': 'sum'
    }).reset_index()
    
    resumen_generica['Saldo'] = resumen_generica['PIM'] - resumen_generica['Devengado_Total']
    resumen_generica['%_Ejecucion'] = (resumen_generica['Devengado_Total'] / resumen_generica['PIM'] * 100).round(2)
    
    # Formatear para mostrar
    display_generica = resumen_generica.copy()
    for col in ['PIM', 'Certificado', 'Compromiso', 'Devengado_Total', 'Saldo']:
        display_generica[col] = display_generica[col].apply(lambda x: f"S/ {x:,.2f}")
    display_generica['%_Ejecucion'] = display_generica['%_Ejecucion'].apply(lambda x: f"{x}%")
    
    # Agregar fila de total
    total_row = pd.DataFrame({
        'Genérica': ['TOTAL'],
        'PIM': [f"S/ {resumen_generica['PIM'].sum():,.2f}"],
        'Certificado': [f"S/ {resumen_generica['Certificado'].sum():,.2f}"],
        'Compromiso': [f"S/ {resumen_generica['Compromiso'].sum():,.2f}"],
        'Devengado_Total': [f"S/ {resumen_generica['Devengado_Total'].sum():,.2f}"],
        'Saldo': [f"S/ {(resumen_generica['PIM'].sum() - resumen_generica['Devengado_Total'].sum()):,.2f}"],
        '%_Ejecucion': [f"{(resumen_generica['Devengado_Total'].sum() / resumen_generica['PIM'].sum() * 100):.1f}%"]
    })
    
    display_generica = pd.concat([display_generica, total_row], ignore_index=True)
    st.dataframe(display_generica, use_container_width=True, hide_index=True)
    
    # ==================== BOTONES DE DESCARGA ====================
    st.markdown("---")
    col_desc1, col_desc2 = st.columns(2)
    
    with col_desc1:
        # Exportar a Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, sheet_name='Datos Filtrados', index=False)
            resumen_generica.to_excel(writer, sheet_name='Resumen por Genérica', index=False)
            if 'df_mensual' in locals():
                df_mensual.to_excel(writer, sheet_name='Datos Mensuales', index=False)
        
        output.seek(0)
        st.download_button(
            label="📥 Exportar a Excel",
            data=output,
            file_name=f"reporte_ipen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col_desc2:
        # Exportar a CSV
        csv = df_filtrado.to_csv(index=False)
        st.download_button(
            label="📥 Exportar a CSV",
            data=csv,
            file_name=f"reporte_ipen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Información adicional
    st.markdown("---")
    st.caption(f"Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    st.caption(f"Total de registros procesados: {len(df_filtrado)}")

else:
    # Mensaje de bienvenida cuando no hay datos
    st.info("""
    ### 👋 Bienvenido al Tablero Presupuestal del IPEN
    
    Para comenzar, por favor cargue un archivo Excel o ingrese los datos manualmente usando las opciones en la barra lateral izquierda.
    
    **Formatos de archivo soportados:**
    - Reportes de gastos del SIAF (con columnas: mto_pim, mto_certificado, mto_compro_anual, mto_devenga_01 a mto_devenga_12)
    - Cualquier archivo Excel con estructura similar
    
    **Datos manuales:**
    - Puede ingresar los datos presupuestales de forma manual, completando los formularios para cada genérica de gasto.
    """)
    
    # Mostrar ejemplo de estructura esperada
    with st.expander("Ver estructura esperada del archivo Excel"):
        st.markdown("""
        El archivo Excel debe contener las siguientes columnas:
        
        | Columna | Descripción |
        |---------|-------------|
        | `mto_pim` | Presupuesto Institucional Modificado |
        | `mto_certificado` | Monto certificado |
        | `mto_compro_anual` | Monto comprometido anual |
        | `mto_devenga_01` a `mto_devenga_12` | Monto devengado por mes (01=Enero, 02=Febrero, etc.) |
        | `tipo_act_obra_ac` | Tipo de gasto (5xx = Actividad, 4xx = Inversión) |
        | `generica` | Genérica de gasto (ej. "1.PERSONAL Y OBLIGACIONES SOCIALES") |
        
        **Ejemplo de datos:**
mto_pim,mto_certificado,mto_compro_anual,mto_devenga_01,mto_devenga_02,tipo_act_obra_ac,generica
1000000,850000,800000,70000,65000,5005625,1.PERSONAL Y OBLIGACIONES SOCIALES
500000,400000,350000,30000,25000,4000068,6.ADQUISICION DE ACTIVOS NO FINANCIEROS
""")
