import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime
import re
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Tablero Presupuestal IPEN", layout="wide")

# Logo institucional
st.sidebar.image("https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png", width=250)

# Cargar archivo
st.sidebar.header("Cargar archivo Excel")
archivo = st.sidebar.file_uploader("Seleccionar archivo ReporteGasto", type=["xls", "xlsx"])

# Crear carpeta de respaldo
carpeta_respaldo = "Respaldo_Data"
os.makedirs(carpeta_respaldo, exist_ok=True)

if archivo:
    # Guardar archivo
    ruta_archivo = os.path.join(carpeta_respaldo, archivo.name)
    with open(ruta_archivo, "wb") as f:
        f.write(archivo.getbuffer())

    try:
        # Leer archivo Excel
        df = pd.read_excel(ruta_archivo)
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # --- DETECCIÓN DE COLUMNAS OBLIGATORIAS (Mapeo SIAF) ---
        
        # 1. Detectar PIM
        col_pim = 'mto_pim' if 'mto_pim' in df.columns else None
        if col_pim is None:
            # Fallback: buscar una columna que contenga 'pim'
            for col in df.columns:
                if 'pim' in col:
                    col_pim = col
                    break
        if col_pim is None:
            st.error("No se encontró la columna PIM (mto_pim).")
            st.stop()
        df.rename(columns={col_pim: "PIM"}, inplace=True)

        # 2. Detectar Certificado
        col_cert = 'mto_certificado' if 'mto_certificado' in df.columns else None
        if col_cert is None:
            for col in df.columns:
                if 'certificado' in col:
                    col_cert = col
                    break
        if col_cert:
            df.rename(columns={col_cert: "Certificado"}, inplace=True)
        else:
            df["Certificado"] = 0

        # 3. Detectar Compromiso Anual
        col_comp = 'mto_compro_anual' if 'mto_compro_anual' in df.columns else None
        if col_comp is None:
            for col in df.columns:
                if 'compro_anual' in col or 'compromiso' in col:
                    col_comp = col
                    break
        if col_comp:
            df.rename(columns={col_comp: "Compromiso_Anual"}, inplace=True)
        else:
            df["Compromiso_Anual"] = 0

        # 4. Detectar columnas de Devengado mensual (mto_devenga_01 a mto_devenga_12)
        columnas_devengado = []
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        for i in range(1, 13):
            col_name = f'mto_devenga_{i:02d}'
            if col_name in df.columns:
                columnas_devengado.append(col_name)
                df.rename(columns={col_name: f"Devengado_{meses[i-1]}"}, inplace=True)
        
        # Si no se encuentran, intentar con nombres alternativos
        if len(columnas_devengado) < 12:
            cols_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
            excluir = ['mto_pim', 'mto_certificado', 'mto_compro_anual', 'pim', 'total', 'año', 'ano']
            cols_candidatas = [c for c in cols_numericas if not any(e in c for e in excluir)]
            # Asignar las primeras 12 candidatas
            for i, col in enumerate(cols_candidatas[:12]):
                if col not in columnas_devengado:
                    columnas_devengado.append(col)
                    df.rename(columns={col: f"Devengado_{meses[i]}"}, inplace=True)
        
        if len(columnas_devengado) == 0:
            st.error("No se pudieron detectar columnas de devengado mensual.")
            st.stop()
        
        columnas_devengado_nombres = [f"Devengado_{mes}" for mes in meses[:len(columnas_devengado)]]
        
        # 5. Detectar columna de genérica
        col_generica = None
        for col in df.columns:
            if 'generica' in col:
                col_generica = col
                break
        if col_generica:
            df.rename(columns={col_generica: "generica"}, inplace=True)
            st.sidebar.success(f"Columna de genérica detectada: '{col_generica}'")
        else:
            df["generica"] = "General"
            st.sidebar.info("No se encontró columna de genérica. Se usará 'General'.")
        
        # 6. Calcular Avance Físico (si existen las columnas necesarias)
        if 'avan_fisico_anual' in df.columns and 'cant_meta_anual' in df.columns:
            df['Avance_Fisico'] = (df['avan_fisico_anual'] / df['cant_meta_anual'] * 100).round(2)
        else:
            df['Avance_Fisico'] = 0
        
        # Calcular Devengado Total
        df["Devengado_Total"] = df[columnas_devengado_nombres].sum(axis=1)
        df["Saldo"] = df["PIM"] - df["Devengado_Total"]
        df["%_Ejecucion_Financiera"] = (df["Devengado_Total"] / df["PIM"] * 100).round(2)
        
        # Filtrar datos no válidos
        df = df[df["generica"].notna()]
        df = df[df["PIM"] > 0]  # Solo considerar registros con presupuesto
        
        # Información general
        fecha_formateada = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pliego = df.get("pliego", pd.Series(["No especificado"])).iloc[0] if "pliego" in df.columns else "No especificado"
        ano_eje = df.get("ano_eje", pd.Series(["No disponible"])).iloc[0] if "ano_eje" in df.columns else "No disponible"
        
        st.title("📊 Tablero Presupuestal - IPEN")
        st.markdown(f"""
        **Entidad:** `{pliego}`  
        **Año Fiscal:** `{ano_eje}`  
        **Última actualización:** `{fecha_formateada}`  
        **Registros cargados:** `{len(df)}`
        """)
        
        # --- FILTROS ---
        st.sidebar.header("Filtros")
        
        # Filtro de genérica (Personal y Obligaciones Sociales, Bienes y Servicios, etc.)
        genericas = ["Todas"] + sorted(df["generica"].unique().tolist())
        filtro_generica = st.sidebar.selectbox("Filtrar por Genérica", genericas)
        
        df_filtrado = df.copy()
        if filtro_generica != "Todas":
            df_filtrado = df_filtrado[df_filtrado["generica"] == filtro_generica]
        
        if df_filtrado.empty:
            st.warning("No hay datos para los filtros seleccionados")
            st.stop()
        
        # Filtro de tipo (Actividad/Inversión) si existe la columna tipo_act_obra_ac
        tipo_act_inv = "Tipo"
        if "tipo_act_obra_ac" in df.columns:
            # Mapear valores: si empieza con 5 = Actividad, si empieza con 4 = Obra (Inversión)
            df_filtrado['Tipo'] = df_filtrado['tipo_act_obra_ac'].apply(
                lambda x: 'Actividad' if str(x).startswith('5') else ('Inversión' if str(x).startswith('4') else 'Otro')
            )
            tipos = ["Todos"] + sorted(df_filtrado['Tipo'].unique())
            filtro_tipo = st.sidebar.selectbox("Filtrar por Tipo (Actividad/Inversión)", tipos)
            if filtro_tipo != "Todos":
                df_filtrado = df_filtrado[df_filtrado['Tipo'] == filtro_tipo]
        else:
            df_filtrado['Tipo'] = 'General'
            filtro_tipo = "Todos"
        
        # --- CÁLCULO DE TOTALES ---
        pim_total = df_filtrado["PIM"].sum()
        certificado_total = df_filtrado["Certificado"].sum() if "Certificado" in df_filtrado.columns else 0
        compromiso_total = df_filtrado["Compromiso_Anual"].sum() if "Compromiso_Anual" in df_filtrado.columns else 0
        devengado_total = df_filtrado["Devengado_Total"].sum()
        
        # --- GRÁFICOS GAUGE (RELOJES) - Estilo EP IPEN ---
        st.subheader("I. EJECUCIÓN PRESUPUESTAL")
        
        # Crear una tabla resumen similar al reporte
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1, 1, 1, 1, 1, 1.5])
        with col1:
            st.markdown("**Detalle**")
        with col2:
            st.markdown("**PIA**")
        with col3:
            st.markdown("**PIM**")
        with col4:
            st.markdown("**Certificado**")
        with col5:
            st.markdown("**Compromiso**")
        with col6:
            st.markdown("**Devengado**")
        with col7:
            st.markdown("**Saldo**")
        
        # Fila para Actividad
        if "Tipo" in df_filtrado.columns and "Actividad" in df_filtrado['Tipo'].values:
            df_act = df_filtrado[df_filtrado['Tipo'] == "Actividad"]
            pim_act = df_act["PIM"].sum()
            cert_act = df_act["Certificado"].sum()
            comp_act = df_act["Compromiso_Anual"].sum()
            dev_act = df_act["Devengado_Total"].sum()
            saldo_act = pim_act - dev_act
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1, 1, 1, 1, 1, 1.5])
            with col1: st.markdown("**ACTIVIDAD**")
            with col2: st.markdown(f"S/ {pim_act:,.0f}")
            with col3: st.markdown(f"S/ {pim_act:,.0f}")
            with col4: st.markdown(f"S/ {cert_act:,.0f}<br><span style='font-size:0.8em'>({(cert_act/pim_act*100 if pim_act>0 else 0):.1f}%)</span>", unsafe_allow_html=True)
            with col5: st.markdown(f"S/ {comp_act:,.0f}<br><span style='font-size:0.8em'>({(comp_act/pim_act*100 if pim_act>0 else 0):.1f}%)</span>", unsafe_allow_html=True)
            with col6: st.markdown(f"S/ {dev_act:,.0f}<br><span style='font-size:0.8em'>({(dev_act/pim_act*100 if pim_act>0 else 0):.1f}%)</span>", unsafe_allow_html=True)
            with col7: st.markdown(f"S/ {saldo_act:,.0f}")
        
        # Fila para Inversión
        if "Tipo" in df_filtrado.columns and "Inversión" in df_filtrado['Tipo'].values:
            df_inv = df_filtrado[df_filtrado['Tipo'] == "Inversión"]
            pim_inv = df_inv["PIM"].sum()
            cert_inv = df_inv["Certificado"].sum()
            comp_inv = df_inv["Compromiso_Anual"].sum()
            dev_inv = df_inv["Devengado_Total"].sum()
            saldo_inv = pim_inv - dev_inv
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1, 1, 1, 1, 1, 1.5])
            with col1: st.markdown("**INVERSION**")
            with col2: st.markdown(f"S/ {pim_inv:,.0f}")
            with col3: st.markdown(f"S/ {pim_inv:,.0f}")
            with col4: st.markdown(f"S/ {cert_inv:,.0f}<br><span style='font-size:0.8em'>({(cert_inv/pim_inv*100 if pim_inv>0 else 0):.1f}%)</span>", unsafe_allow_html=True)
            with col5: st.markdown(f"S/ {comp_inv:,.0f}<br><span style='font-size:0.8em'>({(comp_inv/pim_inv*100 if pim_inv>0 else 0):.1f}%)</span>", unsafe_allow_html=True)
            with col6: st.markdown(f"S/ {dev_inv:,.0f}<br><span style='font-size:0.8em'>({(dev_inv/pim_inv*100 if pim_inv>0 else 0):.1f}%)</span>", unsafe_allow_html=True)
            with col7: st.markdown(f"S/ {saldo_inv:,.0f}")
        
        # Fila Total General
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1, 1, 1, 1, 1, 1.5])
        with col1: st.markdown("**Total general**")
        with col2: st.markdown(f"S/ {pim_total:,.0f}")
        with col3: st.markdown(f"S/ {pim_total:,.0f}")
        with col4: st.markdown(f"S/ {certificado_total:,.0f}<br><span style='font-size:0.8em'>({(certificado_total/pim_total*100 if pim_total>0 else 0):.1f}%)</span>", unsafe_allow_html=True)
        with col5: st.markdown(f"S/ {compromiso_total:,.0f}<br><span style='font-size:0.8em'>({(compromiso_total/pim_total*100 if pim_total>0 else 0):.1f}%)</span>", unsafe_allow_html=True)
        with col6: st.markdown(f"S/ {devengado_total:,.0f}<br><span style='font-size:0.8em'>({(devengado_total/pim_total*100 if pim_total>0 else 0):.1f}%)</span>", unsafe_allow_html=True)
        with col7: st.markdown(f"S/ {pim_total - devengado_total:,.0f}")
        
        # --- GRÁFICO DE EVOLUCIÓN MENSUAL (Actividad vs Inversión) ---
        st.subheader("II. EVOLUCIÓN MENSUAL DEL GASTO (Actividad vs Inversión)")
        
        # Preparar datos para el gráfico
        datos_grafico = []
        
        if "Tipo" in df_filtrado.columns:
            tipos_grafico = ["Actividad", "Inversión"]
            # Asegurar que ambos tipos existan
            tipos_existentes = [t for t in tipos_grafico if t in df_filtrado['Tipo'].values]
            
            for tipo in tipos_existentes:
                df_tipo = df_filtrado[df_filtrado['Tipo'] == tipo]
                for mes in columnas_devengado_nombres:
                    monto = df_tipo[mes].sum()
                    if monto > 0:
                        datos_grafico.append({
                            "tipo": tipo,
                            "mes": mes.replace("Devengado_", ""),
                            "monto": monto
                        })
        
        # Si no hay datos por tipo, agrupar por genérica
        if not datos_grafico:
            for generica in df_filtrado["generica"].unique():
                df_gen = df_filtrado[df_filtrado["generica"] == generica]
                for mes in columnas_devengado_nombres:
                    monto = df_gen[mes].sum()
                    if monto > 0:
                        datos_grafico.append({
                            "tipo": generica,
                            "mes": mes.replace("Devengado_", ""),
                            "monto": monto
                        })
        
        df_grafico = pd.DataFrame(datos_grafico)
        
        if df_grafico.empty:
            st.warning("No hay datos para mostrar en el gráfico")
        else:
            # Ordenar meses cronológicamente
            df_grafico["mes"] = pd.Categorical(
                df_grafico["mes"], 
                categories=meses, 
                ordered=True
            )
            df_grafico = df_grafico.sort_values(["mes", "tipo"])
            
            # Calcular totales por mes
            totales_mes = df_grafico.groupby("mes")["monto"].sum().reset_index()
            
            # Determinar escala automática
            max_monto = df_grafico["monto"].max()
            if max_monto > 1e6:
                df_grafico["monto_mostrar"] = df_grafico["monto"] / 1e6
                unidad = "Millones S/"
                formato_total = lambda x: f"S/ {x/1e6:.2f}M"
            elif max_monto > 1e3:
                df_grafico["monto_mostrar"] = df_grafico["monto"] / 1e3
                unidad = "Miles S/"
                formato_total = lambda x: f"S/ {x/1e3:.1f}K"
            else:
                df_grafico["monto_mostrar"] = df_grafico["monto"]
                unidad = "Soles"
                formato_total = lambda x: f"S/ {x:,.0f}"
            
            # Crear gráfico de barras apiladas
            fig = go.Figure()
            
            # Colores para cada tipo
            colores_tipo = {"Actividad": "#1f77b4", "Inversión": "#ff7f0e"}
            
            # Agregar barras
            for tipo in df_grafico["tipo"].unique():
                df_tipo = df_grafico[df_grafico["tipo"] == tipo]
                if not df_tipo.empty:
                    color = colores_tipo.get(tipo, px.colors.qualitative.Set3[0])
                    fig.add_trace(go.Bar(
                        name=tipo,
                        x=df_tipo["mes"],
                        y=df_tipo["monto_mostrar"],
                        text=df_tipo["monto"].apply(lambda x: f"S/ {x:,.0f}"),
                        textposition='inside',
                        textfont_size=10,
                        marker_color=color,
                        hovertemplate="<b>%{x}</b><br>" +
                                    f"{tipo}<br>" +
                                    "Monto: S/ %{customdata:,.0f}<br>" +
                                    "<extra></extra>",
                        customdata=df_tipo["monto"].values
                    ))
            
            # Configurar layout
            fig.update_layout(
                barmode='stack',
                title="Evolución Mensual del Gasto (Programado vs Ejecutado)",
                xaxis_title="Mes",
                yaxis_title=unidad,
                hovermode='x unified',
                legend_title="Tipo",
                showlegend=True,
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Agregar anotaciones de totales
            for i, row in totales_mes.iterrows():
                mes = row["mes"]
                total = row["monto"]
                
                if max_monto > 1e6:
                    y_pos = total / 1e6
                elif max_monto > 1e3:
                    y_pos = total / 1e3
                else:
                    y_pos = total
                
                fig.add_annotation(
                    x=mes,
                    y=y_pos,
                    text=f"<b>{formato_total(total)}</b>",
                    showarrow=False,
                    yshift=15,
                    font=dict(size=11, color="black", family="Arial Black"),
                    bgcolor="rgba(255, 255, 255, 0.9)",
                    bordercolor="black",
                    borderwidth=1,
                    borderpad=4
                )
            
            # Mejorar ejes
            fig.update_xaxes(tickangle=45, gridcolor='lightgray')
            fig.update_yaxes(gridcolor='lightgray')
            
            st.plotly_chart(fig, use_container_width=True)
        
        # --- TABLA RESUMEN POR GENÉRICA ---
        st.subheader("III. RESULTADOS POR GENÉRICA")
        
        resumen = df_filtrado.groupby("generica").agg({
            "PIM": "sum",
            "Certificado": "sum",
            "Compromiso_Anual": "sum",
            "Devengado_Total": "sum",
            "Saldo": "sum",
            "Avance_Fisico": "mean"  # Promedio del avance físico
        }).reset_index()
        
        resumen["%_Ejecucion_Financiera"] = (resumen["Devengado_Total"] / resumen["PIM"] * 100).round(2)
        resumen["Saldo"] = resumen["PIM"] - resumen["Devengado_Total"]
        
        # Ordenar por nombre de genérica
        resumen = resumen.sort_values("generica").reset_index(drop=True)
        
        # Formato para mostrar
        resumen_display = resumen.copy()
        for col in ["PIM", "Certificado", "Compromiso_Anual", "Devengado_Total", "Saldo"]:
            if col in resumen_display.columns:
                resumen_display[col] = resumen_display[col].apply(lambda x: f"S/ {x:,.0f}")
        resumen_display["%_Ejecucion_Financiera"] = resumen_display["%_Ejecucion_Financiera"].apply(lambda x: f"{x}%")
        if "Avance_Fisico" in resumen_display.columns:
            resumen_display["Avance_Fisico"] = resumen_display["Avance_Fisico"].apply(lambda x: f"{x:.2f}%")
        
        # Agregar fila de total
        total_row = pd.DataFrame({
            "generica": ["TOTAL"],
            "PIM": [f"S/ {resumen['PIM'].sum():,.0f}"],
            "Certificado": [f"S/ {resumen['Certificado'].sum():,.0f}"],
            "Compromiso_Anual": [f"S/ {resumen['Compromiso_Anual'].sum():,.0f}"],
            "Devengado_Total": [f"S/ {resumen['Devengado_Total'].sum():,.0f}"],
            "Saldo": [f"S/ {(resumen['PIM'].sum() - resumen['Devengado_Total'].sum()):,.0f}"],
            "%_Ejecucion_Financiera": [f"{(resumen['Devengado_Total'].sum() / resumen['PIM'].sum() * 100):.1f}%"],
            "Avance_Fisico": [f"{(resumen['Avance_Fisico'].mean()):.2f}%"]
        })
        
        resumen_display = pd.concat([resumen_display, total_row], ignore_index=True)
        st.dataframe(resumen_display, use_container_width=True)
        
        # --- DATOS DETALLADOS (expandible) ---
        with st.expander("📋 Ver datos detallados del reporte"):
            # Mostrar columnas relevantes
            columnas_mostrar = ['generica', 'PIM', 'Certificado', 'Compromiso_Anual', 
                               'Devengado_Total', 'Saldo', '%_Ejecucion_Financiera']
            if 'Avance_Fisico' in df_filtrado.columns:
                columnas_mostrar.append('Avance_Fisico')
            if 'tipo_act_obra_ac' in df_filtrado.columns:
                columnas_mostrar.append('tipo_act_obra_ac')
            
            df_detalle = df_filtrado[columnas_mostrar].copy()
            for col in ['PIM', 'Certificado', 'Compromiso_Anual', 'Devengado_Total', 'Saldo']:
                if col in df_detalle.columns:
                    df_detalle[col] = df_detalle[col].apply(lambda x: f"S/ {x:,.0f}")
            if 'Avance_Fisico' in df_detalle.columns:
                df_detalle['Avance_Fisico'] = df_detalle['Avance_Fisico'].apply(lambda x: f"{x:.2f}%")
            if '%_Ejecucion_Financiera' in df_detalle.columns:
                df_detalle['%_Ejecucion_Financiera'] = df_detalle['%_Ejecucion_Financiera'].apply(lambda x: f"{x}%")
            
            st.dataframe(df_detalle, use_container_width=True)
            
            # Botón de descarga
            csv = df_filtrado.to_csv(index=False)
            st.download_button(
                "📥 Descargar datos completos (CSV)",
                csv,
                f"reporte_presupuestal_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.exception(e)
else:
    st.info("👈 Por favor, cargue un archivo Excel del Reporte de Gasto (formato SIAF) para comenzar.")
