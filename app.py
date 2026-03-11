import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime
import re
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Tablero Presupuestal", layout="wide")

# Logo institucional
st.sidebar.image("https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png", width=250)

# Cargar archivo
st.sidebar.header("Cargar archivo Excel")
archivo = st.sidebar.file_uploader("Seleccionar archivo Excel", type=["xls", "xlsx"])

# Crear carpeta de respaldo
carpeta_respaldo = "Respaldo_Data"
os.makedirs(carpeta_respaldo, exist_ok=True)

if archivo:
    # Guardar archivo
    ruta_archivo = os.path.join(carpeta_respaldo, archivo.name)
    with open(ruta_archivo, "wb") as f:
        f.write(archivo.getbuffer())

    try:
        # Leer archivo Excel con manejo de errores
        df = pd.read_excel(ruta_archivo)
        
        # Mostrar información de depuración (opcional, comentar si no se necesita)
        with st.expander("Información de depuración"):
            st.write("Columnas originales:", list(df.columns))
            st.write("Primeras filas:", df.head())
        
        # Normalizar nombres de columnas (minúsculas y sin espacios)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Buscar columnas de devengado mensual (patrones comunes)
        columnas_devengado = []
        patrones_mensuales = [
            r'mto_devenga_\d{2}',  # mto_devenga_01, mto_devenga_02, etc.
            r'devengado',           # cualquier columna que contenga "devengado"
            r'monto_devengado',     # monto_devengado
            r'mes_\d{2}'            # mes_01, mes_02, etc.
        ]
        
        for col in df.columns:
            for patron in patrones_mensuales:
                if re.search(patron, col, re.IGNORECASE):
                    if col not in columnas_devengado:
                        columnas_devengado.append(col)
                    break
        
        # Si no se encuentran columnas, buscar numéricas que podrían ser montos mensuales
        if len(columnas_devengado) < 12:
            # Buscar columnas numéricas que podrían ser los meses
            cols_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
            # Excluir columnas que claramente no son mensuales (PIM, certificado, etc.)
            excluir = ['mto_pim', 'pim', 'mto_certificado', 'certificado', 
                      'mto_compro_anual', 'compromiso', 'total']
            cols_candidatas = [c for c in cols_numericas if not any(e in c for e in excluir)]
            # Tomar las primeras 12 (o menos) como columnas de devengado
            columnas_devengado = cols_candidatas[:12]
        
        st.sidebar.write(f"Columnas de devengado detectadas: {len(columnas_devengado)}")
        
        if len(columnas_devengado) == 0:
            st.error("No se pudieron detectar columnas de devengado mensual. Verifique el formato del archivo.")
            st.stop()
        
        # Renombrar columnas de devengado con nombres de meses
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        for i, col in enumerate(columnas_devengado[:12]):
            df.rename(columns={col: f"Devengado_{meses[i]}"}, inplace=True)
        
        # Actualizar lista de columnas de devengado con los nuevos nombres
        columnas_devengado = [f"Devengado_{mes}" for mes in meses[:len(columnas_devengado)]]
        
        # Buscar columna PIM
        col_pim = None
        for col in df.columns:
            if 'pim' in col.lower() or 'presupuesto' in col.lower() and 'inicial' in col.lower():
                col_pim = col
                break
        
        if col_pim is None:
            # Buscar columna que podría ser PIM (valores grandes)
            cols_numericas = df.select_dtypes(include=[np.number]).columns
            for col in cols_numericas:
                if df[col].mean() > df[columnas_devengado].mean().mean() * 2:  # PIM suele ser mayor
                    col_pim = col
                    break
        
        if col_pim is None:
            st.error("No se pudo detectar la columna de Presupuesto Inicial (PIM)")
            st.stop()
        
        df.rename(columns={col_pim: "PIM"}, inplace=True)
        
        # Buscar columna de genérica
        col_generica = None
        for col in df.columns:
            if re.search(r'generica?|gen[eé]rica?', col, re.IGNORECASE):
                col_generica = col
                break
        
        if col_generica:
            df.rename(columns={col_generica: "generica"}, inplace=True)
            st.sidebar.success(f"Columna de genérica detectada: '{col_generica}'")
        else:
            df["generica"] = "General"
            st.sidebar.info("No se encontró columna de genérica. Se usará 'General'.")
        
        # Calcular métricas
        df["Devengado_Total"] = df[columnas_devengado].sum(axis=1)
        df["Saldo"] = df["PIM"] - df["Devengado_Total"]
        df["%_Ejecucion"] = (df["Devengado_Total"] / df["PIM"] * 100).round(2)
        
        # Filtrar datos no numéricos en genérica
        df = df[df["generica"].notna()]
        
        # Información general
        fecha_formateada = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        st.title("📊 Tablero Presupuestal Interactivo")
        st.markdown(f"""
        **Última actualización:** `{fecha_formateada}`  
        **Registros cargados:** `{len(df)}`  
        **Columnas de devengado:** `{', '.join(columnas_devengado)}`
        """)
        
        # Filtros en barra lateral
        st.sidebar.header("Filtros")
        
        # Filtro de genérica
        genericas = ["Todas"] + sorted(df["generica"].unique().tolist())
        filtro_generica = st.sidebar.selectbox("Filtrar por Genérica", genericas)
        
        df_filtrado = df.copy()
        if filtro_generica != "Todas":
            df_filtrado = df_filtrado[df_filtrado["generica"] == filtro_generica]
        
        if df_filtrado.empty:
            st.warning("No hay datos para los filtros seleccionados")
            st.stop()
        
        # Totales
        pim_total = df_filtrado["PIM"].sum()
        devengado_total = df_filtrado["Devengado_Total"].sum()
        
        # Mostrar métricas principales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("PIM Total", f"S/ {pim_total:,.0f}")
        with col2:
            st.metric("Devengado Total", f"S/ {devengado_total:,.0f}")
        with col3:
            ejecucion = (devengado_total / pim_total * 100) if pim_total > 0 else 0
            st.metric("% Ejecución", f"{ejecucion:.1f}%")
        
        # Tabla resumen por genérica
        st.subheader("Resumen por Genérica")
        resumen = df_filtrado.groupby("generica").agg({
            "PIM": "sum",
            "Devengado_Total": "sum",
            "Saldo": "sum"
        }).reset_index()
        
        resumen["%_Ejecucion"] = (resumen["Devengado_Total"] / resumen["PIM"] * 100).round(2)
        resumen = resumen.sort_values("PIM", ascending=False)
        
        # Formatear para mostrar
        resumen_display = resumen.copy()
        for col in ["PIM", "Devengado_Total", "Saldo"]:
            resumen_display[col] = resumen_display[col].apply(lambda x: f"S/ {x:,.0f}")
        resumen_display["%_Ejecucion"] = resumen_display["%_Ejecucion"].apply(lambda x: f"{x}%")
        
        st.dataframe(resumen_display, use_container_width=True)
        
        # --- GRÁFICO DE EVOLUCIÓN MENSUAL CORREGIDO ---
        st.subheader("📈 Evolución del Devengado Mensual por Genérica")
        
        # Preparar datos para el gráfico
        datos_grafico = []
        
        for generica in df_filtrado["generica"].unique():
            df_gen = df_filtrado[df_filtrado["generica"] == generica]
            for mes in columnas_devengado:
                monto = df_gen[mes].sum()
                if monto > 0:  # Solo incluir montos positivos
                    datos_grafico.append({
                        "generica": generica,
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
            df_grafico = df_grafico.sort_values("mes")
            
            # Calcular totales por mes para anotaciones
            totales_mes = df_grafico.groupby("mes")["monto"].sum().reset_index()
            
            # Determinar escala automática
            max_monto = df_grafico["monto"].max()
            if max_monto > 1e6:
                df_grafico["monto_mostrar"] = df_grafico["monto"] / 1e6
                unidad = "Millones S/"
                formato = lambda x: f"S/ {x/1e6:.2f}M"
            elif max_monto > 1e3:
                df_grafico["monto_mostrar"] = df_grafico["monto"] / 1e3
                unidad = "Miles S/"
                formato = lambda x: f"S/ {x/1e3:.1f}K"
            else:
                df_grafico["monto_mostrar"] = df_grafico["monto"]
                unidad = "Soles"
                formato = lambda x: f"S/ {x:,.0f}"
            
            # Crear gráfico
            fig = go.Figure()
            
            # Colores para cada genérica
            colores = px.colors.qualitative.Set2
            genericas_unicas = df_grafico["generica"].unique()
            color_map = {gen: colores[i % len(colores)] for i, gen in enumerate(genericas_unicas)}
            
            # Agregar barras para cada genérica
            for generica in genericas_unicas:
                df_gen = df_grafico[df_grafico["generica"] == generica]
                fig.add_trace(go.Bar(
                    name=generica,
                    x=df_gen["mes"],
                    y=df_gen["monto_mostrar"],
                    text=df_gen["monto"].apply(lambda x: f"S/ {x:,.0f}"),
                    textposition='inside',
                    textfont_size=10,
                    marker_color=color_map[generica],
                    hovertemplate="<b>%{x}</b><br>" +
                                f"Genérica: {generica}<br>" +
                                "Monto: S/ %{customdata:,.0f}<br>" +
                                "<extra></extra>",
                    customdata=df_gen["monto"].values
                ))
            
            # Configurar layout
            fig.update_layout(
                barmode='stack',
                title="Evolución Mensual del Gasto por Genérica",
                xaxis_title="Mes",
                yaxis_title=unidad,
                hovermode='x unified',
                legend_title="Genérica",
                showlegend=True,
                height=500
            )
            
            # Agregar anotaciones de totales
            for i, row in totales_mes.iterrows():
                mes = row["mes"]
                total = row["monto"]
                y_pos = total / (1e6 if max_monto > 1e6 else 1e3 if max_monto > 1e3 else 1)
                
                fig.add_annotation(
                    x=mes,
                    y=y_pos,
                    text=f"<b>{formato(total)}</b>",
                    showarrow=False,
                    yshift=15,
                    font=dict(size=11, color="black"),
                    bgcolor="rgba(255, 255, 255, 0.8)",
                    bordercolor="black",
                    borderwidth=1,
                    borderpad=4
                )
            
            # Mejorar ejes
            fig.update_xaxes(tickangle=45)
            fig.update_yaxes(gridcolor='lightgray')
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar datos en tabla
            with st.expander("Ver datos detallados"):
                # Pivotar tabla para mejor visualización
                pivot_df = df_grafico.pivot_table(
                    values='monto',
                    index='generica',
                    columns='mes',
                    aggfunc='sum',
                    fill_value=0
                )
                # Formatear
                for col in pivot_df.columns:
                    pivot_df[col] = pivot_df[col].apply(lambda x: f"S/ {x:,.0f}")
                st.dataframe(pivot_df, use_container_width=True)
                
                # Botón de descarga
                csv = df_grafico[["generica", "mes", "monto"]].to_csv(index=False)
                st.download_button(
                    "📥 Descargar datos CSV",
                    csv,
                    "evolucion_mensual.csv",
                    "text/csv"
                )
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.exception(e)  # Muestra el traceback completo para depuración
else:
    st.info("👈 Por favor, cargue un archivo Excel válido para comenzar.")
