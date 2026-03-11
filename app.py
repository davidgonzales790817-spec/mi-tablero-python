import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime
import re

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
        # Leer y normalizar nombres de columnas
        df = pd.read_excel(ruta_archivo)
        df.columns = df.columns.str.strip().str.lower()

        # Columnas obligatorias
        columnas_obligatorias = [
            "mto_pim", "mto_certificado", "mto_compro_anual"
        ] + [f"mto_devenga_{str(i).zfill(2)}" for i in range(1, 13)]

        # Verificar columnas faltantes
        columnas_faltantes = [col for col in columnas_obligatorias if col not in df.columns]
        if columnas_faltantes:
            st.error("❌ El archivo cargado no contiene todas las columnas necesarias.")
            st.write("Faltan las siguientes columnas:")
            for col in columnas_faltantes:
                st.markdown(f"- `{col}`")
            st.stop()

        # Verificar tipos numéricos
        tipos_erroneos = [col for col in columnas_obligatorias if not pd.api.types.is_numeric_dtype(df[col])]
        if tipos_erroneos:
            st.warning("⚠️ Las siguientes columnas no tienen tipo numérico. Podría afectar los cálculos:")
            for col in tipos_erroneos:
                st.markdown(f"- `{col}`")

        # Renombrar columnas
        renombres = {
            "mto_pim": "Presupuesto Inicial (PIM)",
            "mto_certificado": "Certificado",
            "mto_compro_anual": "Compromiso Anual",
        }
        for i in range(1, 13):
            renombres[f"mto_devenga_{str(i).zfill(2)}"] = f"Devengado {datetime(2000, i, 1).strftime('%B')}"
        df.rename(columns=renombres, inplace=True)

        # Calcular métricas
        columnas_devengado = [col for col in df.columns if "Devengado" in col]
        df["Devengado Total"] = df[columnas_devengado].sum(axis=1)
        df["Saldo Restante"] = df["Presupuesto Inicial (PIM)"] - df["Devengado Total"]
        df["% Ejecución"] = df.apply(lambda x: (x["Devengado Total"] / x["Presupuesto Inicial (PIM)"] * 100) if x["Presupuesto Inicial (PIM)"] else 0, axis=1).round(2)

        # Información general
        fecha_formateada = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pliego = df.get("pliego", pd.Series(["No especificado"])).iloc[0]
        ano_eje = df.get("ano_eje", pd.Series(["No disponible"])).iloc[0]

        st.title("📊 Tablero Presupuestal Interactivo")
        st.markdown(f"""
        **Entidad:** `{pliego}`  
        **Año Fiscal:** `{ano_eje}`  
        **Última actualización:** `{fecha_formateada}`  

        Este tablero permite visualizar de manera dinámica la ejecución presupuestal.
        Carga un archivo Excel con tu información para explorar indicadores clave y seguimiento por genérica.
        """)

        # Detección de columna de genérica
        patron_generica = re.compile(r'generica?|gen[eé]rica?', re.IGNORECASE)
        posibles_generica = [col for col in df.columns if patron_generica.search(col)]

        col_generica = None
        if len(posibles_generica) == 1:
            col_generica = posibles_generica[0]
            df.rename(columns={col_generica: "generica"}, inplace=True)
            st.sidebar.success(f"Columna de genérica detectada automáticamente: '{col_generica}'")
        elif len(posibles_generica) > 1:
            opcion = st.sidebar.selectbox("Múltiples columnas de genérica encontradas. Seleccione la correcta:", posibles_generica)
            col_generica = opcion
            df.rename(columns={col_generica: "generica"}, inplace=True)
        else:
            df["generica"] = "No especificado"
            st.sidebar.info("No se encontró columna de genérica. Se usará 'No especificado'.")

        # Filtro de genérica
        genericas = ["Todas"] + sorted(df["generica"].dropna().unique())
        filtro_generica = st.sidebar.selectbox("Filtrar por Genérica", genericas)
        if filtro_generica != "Todas":
            df = df[df["generica"] == filtro_generica]

        # Filtro por unidad ejecutora
        if "unidad_ejecutora" in df.columns:
            ues = ["Todas"] + sorted(df["unidad_ejecutora"].dropna().unique())
            filtro_ue = st.sidebar.selectbox("Filtrar por Unidad Ejecutora", ues)
            if filtro_ue != "Todas":
                df = df[df["unidad_ejecutora"] == filtro_ue]

        # Validar datos
        if df.empty:
            st.warning("No se encontraron datos para los filtros seleccionados.")
            st.stop()

        # Totales globales
        pim = df["Presupuesto Inicial (PIM)"].sum()
        certificado = df["Certificado"].sum()
        compromiso = df["Compromiso Anual"].sum()
        devengado = df["Devengado Total"].sum()

        # Función para gráficos gauge
        def crear_gauge(valor, total, titulo, color):
            porcentaje = round(valor / total * 100 if total else 0, 2)
            return go.Indicator(
                mode="gauge+number",
                value=porcentaje,
                number={"suffix": "%", "font": {"size": 24}},
                title={"text": f"<b>{titulo}</b><br><span style='font-size:0.8em'>S/ {valor:,.0f}</span>", "font": {"size": 16}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkgray"},
                    "bar": {"color": color},
                    "bgcolor": "white",
                    "borderwidth": 1,
                    "bordercolor": "gray",
                    "steps": [
                        {"range": [0, 50], "color": "#f2f2f2"},
                        {"range": [50, 80], "color": "#d9ead3"},
                        {"range": [80, 100], "color": "#b6d7a8"},
                    ]
                }
            )

        # Mostrar indicadores
        col1, col2, col3 = st.columns(3)
        with col1:
            fig_cert = go.Figure(crear_gauge(certificado, pim, "% Certificado", "#1f77b4"))
            st.plotly_chart(fig_cert, use_container_width=True)
        with col2:
            fig_comp = go.Figure(crear_gauge(compromiso, pim, "% Compromiso", "#ff7f0e"))
            st.plotly_chart(fig_comp, use_container_width=True)
        with col3:
            fig_dev = go.Figure(crear_gauge(devengado, pim, "% Devengado", "#2ca02c"))
            st.plotly_chart(fig_dev, use_container_width=True)

        # Tabla resumen por genérica
        resumen = df.groupby("generica").agg({
            "Presupuesto Inicial (PIM)": "sum",
            "Certificado": "sum",
            "Compromiso Anual": "sum",
            "Devengado Total": "sum",
            "Saldo Restante": "sum"
        }).reset_index()
        resumen["PIM - Certificado"] = resumen["Presupuesto Inicial (PIM)"] - resumen["Certificado"]
        resumen["% Ejecución"] = (resumen["Devengado Total"] / resumen["Presupuesto Inicial (PIM)"] * 100).round(2)

        cols_orden = ["Presupuesto Inicial (PIM)", "Certificado", "PIM - Certificado", "Compromiso Anual", "Devengado Total", "Saldo Restante", "% Ejecución"]
        resumen = resumen[["generica"] + cols_orden]

        st.subheader("Resumen por Genérica")
        resumen_total = resumen[cols_orden].select_dtypes(include='number').sum().to_frame().T
        resumen_total.insert(0, "generica", "TOTAL")
        resumen = pd.concat([resumen, resumen_total], ignore_index=True)
        resumen_formateado = resumen.applymap(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)
        st.dataframe(resumen_formateado, use_container_width=True)

        # --- GRÁFICO DE EVOLUCIÓN MENSUAL MEJORADO ---
        st.subheader("Evolución del Devengado Mensual")

        # Preparar datos
        dev_mes_gen = df.melt(id_vars=["generica"], value_vars=columnas_devengado,
                              var_name="Mes", value_name="Monto")
        dev_mes_gen["Mes"] = dev_mes_gen["Mes"].str.replace("Devengado ", "")

        # Orden cronológico
        meses_orden = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                       "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        dev_mes_gen["Mes"] = pd.Categorical(dev_mes_gen["Mes"], categories=meses_orden, ordered=True)
        dev_mes_gen = dev_mes_gen.sort_values("Mes")

        # Calcular total por mes (para anotaciones)
        total_por_mes = dev_mes_gen.groupby("Mes")["Monto"].sum().reset_index()
        total_por_mes.columns = ["Mes", "Total"]

        # Determinar unidad automática
        max_monto = dev_mes_gen["Monto"].max()
        if max_monto > 1e6:
            factor = 1e6
            unidad = "Millones S/"
            formato = lambda x: f"{x/factor:.2f}"
        elif max_monto > 1e3:
            factor = 1e3
            unidad = "Miles S/"
            formato = lambda x: f"{x/factor:.1f}"
        else:
            factor = 1
            unidad = "S/"
            formato = lambda x: f"{x:,.0f}"

        # Crear columna para mostrar
        dev_mes_gen["Monto_mostrar"] = dev_mes_gen["Monto"] / factor

        # Selector de tipo de gráfico
        tipo_grafico = st.radio("Tipo de gráfico", ["Apilado", "Agrupado", "100% Apilado"], horizontal=True, key="tipo_grafico")

        # Crear figura base
        if tipo_grafico == "100% Apilado":
            # Calcular porcentajes
            total_mes = dev_mes_gen.groupby("Mes")["Monto"].transform("sum")
            dev_mes_gen["Porcentaje"] = dev_mes_gen["Monto"] / total_mes * 100
            y_val = "Porcentaje"
            labels = {"Porcentaje": "Porcentaje (%)"}
            text_template = '%{text:.1f}%'
            hover_template = '%{y:.1f}%'
        else:
            y_val = "Monto_mostrar"
            labels = {"Monto_mostrar": unidad}
            text_template = '%{text:.1f}' if factor > 1 else '%{text:,.0f}'
            hover_template = '%{y:.1f}' if factor > 1 else '%{y:,.0f}'

        # Crear gráfico de barras
        fig_bar = px.bar(
            dev_mes_gen,
            x="Mes",
            y=y_val,
            color="generica",
            text="Monto_mostrar" if y_val == "Monto_mostrar" else "Porcentaje",
            labels=labels,
            color_discrete_sequence=px.colors.qualitative.Set2,
            hover_data={"Monto": ":,.0f"}  # Mostrar monto original en hover
        )

        # Configurar texto de las barras
        fig_bar.update_traces(
            texttemplate=text_template,
            textposition='inside',  # Etiquetas dentro de los segmentos
            insidetextanchor='middle',
            textfont_size=10
        )

        # Configurar layout según tipo
        if tipo_grafico == "Apilado":
            barmode = "stack"
            # Añadir anotaciones con el total encima de cada barra
            for i, mes in enumerate(total_por_mes["Mes"]):
                total_val = total_por_mes[total_por_mes["Mes"] == mes]["Total"].values[0]
                total_mostrar = total_val / factor
                fig_bar.add_annotation(
                    x=mes,
                    y=total_mostrar,
                    text=f"<b>{formato(total_val)}</b>",  # Formato original
                    showarrow=False,
                    yshift=10,  # Desplazamiento vertical
                    font=dict(size=12, color="black"),
                    align="center"
                )
        elif tipo_grafico == "Agrupado":
            barmode = "group"
        else:  # 100% Apilado
            barmode = "relative"
            fig_bar.update_yaxes(range=[0, 100])

        fig_bar.update_layout(
            barmode=barmode,
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            yaxis_title=labels.get(y_val, unidad),
            xaxis_title="Mes",
            hovermode='x unified'
        )

        # Ajustar hover template para mostrar monto original
        fig_bar.update_traces(
            hovertemplate="<b>%{x}</b><br>" +
                          "Genérica: %{fullData.name}<br>" +
                          "Monto: S/ %{customdata[0]:,.0f}<br>" +
                          "<extra></extra>",
            customdata=dev_mes_gen[["Monto"]].values
        )

        st.plotly_chart(fig_bar, use_container_width=True)

        # Opción de descargar datos
        with st.expander("Descargar datos del gráfico"):
            csv = dev_mes_gen[["generica", "Mes", "Monto"]].to_csv(index=False)
            st.download_button("Descargar CSV", csv, "evolucion_mensual.csv", "text/csv")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Por favor, cargue un archivo Excel válido para comenzar.")
