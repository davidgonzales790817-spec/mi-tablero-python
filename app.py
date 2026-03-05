import streamlit as st  # Importa la librería Streamlit para crear aplicaciones web interactivas.
import pandas as pd  # Importa la librería Pandas para el manejo de datos tabulares.
import plotly.graph_objects as go  # Importa la librería Plotly para crear gráficos personalizados.
import plotly.express as px  # Importa la librería Plotly Express para crear gráficos de alto nivel.
import os  # Importa el módulo os para interactuar con el sistema operativo (manejo de archivos y rutas).
import shutil  # Importa el módulo shutil para operaciones de copia de archivos (no se usa en el código proporcionado, pero se incluyó en el prompt del usuario).
from datetime import datetime  # Importa la clase datetime del módulo datetime para trabajar con fechas y horas.

# Configuración de la página en Streamlit
st.set_page_config(page_title="Tablero Presupuestal", layout="wide")  # Establece el título de la página y el diseño de la página en Streamlit.

# Mostrar logo institucional en la barra lateral
st.sidebar.image(
    "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjnfBaYRHfEIEGCd4z9kSvFFtjMekQ2ANpKE0SsZTPKB6tvu9Scpqsp5vt9znWnMCqRY5p32fWi5w9jLFgGq3MJHPR3USDTdvfG8hDQNeVscaCm66L6h4KydFg92sQ5FcRMDHsGRjgYD3I/s16000-rw/033+Despacho+Presidencial.jpg",
    width=250  # Establece el ancho del logo en la barra lateral.
)

# Cargar archivo desde la barra lateral
st.sidebar.header("Cargar archivo Excel")  # Agrega un encabezado a la barra lateral para la carga de archivos.
archivo = st.sidebar.file_uploader("Seleccionar archivo Excel", type=["xls", "xlsx"])  # Crea un widget para cargar archivos Excel en la barra lateral.

# Crear carpeta para respaldos si no existe
carpeta_respaldo = "Respaldo_Data"  # Define el nombre de la carpeta donde se guardarán los archivos de respaldo.
os.makedirs(carpeta_respaldo, exist_ok=True)  # Crea la carpeta si no existe; no genera error si ya existe.

if archivo:  # Verifica si se ha cargado un archivo.
    # Guardar archivo en carpeta de respaldo con su nombre original
    ruta_archivo = os.path.join(carpeta_respaldo, archivo.name)  # Construye la ruta completa del archivo de respaldo.
    with open(ruta_archivo, "wb") as f:  # Abre el archivo en modo escritura binaria ('wb') para guardar el contenido.
        f.write(archivo.getbuffer())  # Escribe el contenido del archivo cargado en el archivo del sistema de archivos.

    try:  # Inicia un bloque try-except para manejar posibles errores al procesar el archivo.
        # Leer archivo Excel y normalizar nombres de columnas
        df = pd.read_excel(ruta_archivo)  # Lee el archivo Excel cargado en un DataFrame de Pandas.
        df.columns = df.columns.str.strip().str.lower()  # Elimina espacios en blanco de los nombres de las columnas y los convierte a minúsculas para統一ar el formato.

        # Definir columnas obligatorias
        columnas_obligatorias = [
            "mto_pim", "mto_certificado", "mto_compro_anual"
        ] + [f"mto_devenga_{str(i).zfill(2)}" for i in range(1, 13)]  # Define la lista de columnas que se esperan en el archivo Excel (mto_pim, mto_certificado, mto_compro_anual y mto_devenga_01 a mto_devenga_12).

        # Verificar si faltan columnas obligatorias
        columnas_faltantes = [col for col in columnas_obligatorias if col not in df.columns]  # Identifica las columnas que están en la lista de columnas_obligatorias pero no en el DataFrame df.
        if columnas_faltantes:  # Si faltan columnas obligatorias, muestra un mensaje de error y detiene la ejecución.
            st.error("❌ El archivo cargado no contiene todas las columnas necesarias.")
            st.write("Faltan las siguientes columnas:")
            for col in columnas_faltantes:
                st.markdown(f"- `{col}`")  # Muestra cada columna faltante en formato markdown.
            st.stop()  # Detiene la ejecución de la aplicación Streamlit.

        # Verificar que columnas obligatorias sean numéricas
        tipos_erroneos = [col for col in columnas_obligatorias if not pd.api.types.is_numeric_dtype(df[col])]  # Identifica las columnas que deberían ser numéricas pero no lo son.
        if tipos_erroneos:  # Si hay columnas con tipos incorrectos, muestra una advertencia.
            st.warning("⚠️ Las siguientes columnas no tienen tipo numérico. Podría afectar los cálculos:")
            for col in tipos_erroneos:
                st.markdown(f"- `{col}`")  # Muestra cada columna con tipo incorrecto en formato markdown.

        # Renombrar columnas con nombres más descriptivos
        renombres = {  # Define un diccionario para mapear los nombres de las columnas originales a nombres más descriptivos.
            "mto_pim": "Presupuesto Inicial (PIM)",
            "mto_certificado": "Certificado",
            "mto_compro_anual": "Compromiso Anual",
        }
        for i in range(1, 13):  # Itera sobre los números de mes (1 al 12).
            renombres[f"mto_devenga_{str(i).zfill(2)}"] = f"Devengado {datetime(2000, i, 1).strftime('%B')}"  # Crea nombres de columna para los meses (Ej: Devengado Enero, Devengado Febrero, etc.) usando el nombre del mes.
        df.rename(columns=renombres, inplace=True)  # Renombra las columnas del DataFrame usando el diccionario renombres.

        # Calcular métricas clave
        columnas_devengado = [col for col in df.columns if "Devengado" in col]  # Obtiene la lista de columnas que contienen información de devengado.
        df["Devengado Total"] = df[columnas_devengado].sum(axis=1)  # Calcula el devengado total sumando los devengados de cada mes para cada fila.
        df["Saldo Restante"] = df["Presupuesto Inicial (PIM)"] - df["Devengado Total"]  # Calcula el saldo restante del presupuesto restando el devengado total del presupuesto inicial.
        df["% Ejecución"] = df.apply(lambda x: (x["Devengado Total"] / x["Presupuesto Inicial (PIM)"] * 100) if x["Presupuesto Inicial (PIM)"] else 0, axis=1).round(2) # Calcula el porcentaje de ejecución, manejando el caso donde el PIM es cero para evitar división por cero.

        # Obtener información general del archivo
        match = datetime.now()  # Obtiene la fecha y hora actual.
        fecha_formateada = match.strftime("%d/%m/%Y %H:%M:%S")  # Formatea la fecha y hora para mostrarla.
        pliego = df.get("pliego", pd.Series(["No especificado"])).iloc[0]  # Obtiene el pliego del DataFrame o "No especificado" si no está presente.
        ano_eje = df.get("ano_eje", pd.Series(["No disponible"])).iloc[0]  # Obtiene el año de ejecución del DataFrame o "No disponible" si no está presente.

        # Mostrar título e información general del tablero
        st.title("📊 Tablero Presupuestal Interactivo")  # Agrega un título a la aplicación Streamlit.
        st.markdown(f"""  # Agrega un texto con información sobre el tablero.
        **Entidad:** `{pliego}`  
        **Año Fiscal:** `{ano_eje}`  
        **Última actualización:** `{fecha_formateada}`  

        Este tablero permite visualizar de manera dinámica y simplificada la ejecución presupuestal de tu entidad.  
        Carga un archivo Excel con tu información presupuestal para explorar indicadores clave, hacer seguimientos por genérica o unidad ejecutora, y detectar oportunidades de mejora en la ejecución.
        """)

        # Detectar y renombrar columna de genérica
        posibles_generica = [col for col in df.columns if any(palabra in col for palabra in ["generica", "genérica", "generico", "genérico"])]  # Busca columnas que contengan alguna de las palabras clave en español para "genérica".
        col_generica = posibles_generica[0] if posibles_generica else None  # Selecciona la primera columna encontrada o None si no se encuentra ninguna.
        if col_generica:  # Si se encuentra una columna de genérica.
            df.rename(columns={col_generica: "generica"}, inplace=True)  # Renombra la columna encontrada a "generica".
        else:  # Si no se encuentra ninguna columna de genérica.
            df["generica"] = "No especificado"  # Crea una nueva columna llamada "generica" y asigna el valor "No especificado" a todas las filas.

        # Filtro de genérica en la barra lateral
        genericas = ["Todas"] + sorted(df["generica"].dropna().unique())  # Obtiene la lista de genéricas únicas del DataFrame, incluyendo "Todas".
        filtro_generica = st.sidebar.selectbox("Filtrar por Genérica", genericas)  # Crea un widget de selección en la barra lateral para filtrar por genérica.
        if filtro_generica != "Todas":  # Si se selecciona una genérica específica (diferente de "Todas").
            df = df[df["generica"] == filtro_generica]  # Filtra el DataFrame para mostrar solo las filas correspondientes a la genérica seleccionada.

        # Filtro por unidad ejecutora si existe
        if "unidad_ejecutora" in df.columns:  # Verifica si el DataFrame contiene la columna "unidad_ejecutora".
            ues = ["Todas"] + sorted(df["unidad_ejecutora"].dropna().unique())  # Obtiene la lista de unidades ejecutoras únicas del DataFrame, incluyendo "Todas".
            filtro_ue = st.sidebar.selectbox("Filtrar por Unidad Ejecutora", ues)  # Crea un widget de selección en la barra lateral para filtrar por unidad ejecutora.
            if filtro_ue != "Todas":  # Si se selecciona una unidad ejecutora específica (diferente de "Todas").
                df = df[df["unidad_ejecutora"] == filtro_ue]  # Filtra el DataFrame para mostrar solo las filas correspondientes a la unidad ejecutora seleccionada.

        # Validación de datos antes de graficar
        if df.empty or "generica" not in df.columns:  # Si el DataFrame está vacío o no contiene la columna "generica".
            st.warning("No se encontraron datos para los filtros seleccionados.")  # Muestra una advertencia.
            st.stop()  # Detiene la ejecución.

        # Calcular totales globales
        pim = df["Presupuesto Inicial (PIM)"].sum()  # Calcula la suma de la columna "Presupuesto Inicial (PIM)".
        certificado = df["Certificado"].sum()  # Calcula la suma de la columna "Certificado".
        compromiso = df["Compromiso Anual"].sum()  # Calcula la suma de la columna "Compromiso Anual".
        devengado = df["Devengado Total"].sum()  # Calcula la suma de la columna "Devengado Total".

        # Función para crear gráficos tipo gauge
        def crear_gauge(valor, total, titulo, color):  # Define una función para crear un gráfico de tipo gauge (medidor).
            porcentaje = round(valor / total * 100 if total else 0, 2)  # Calcula el porcentaje, manejando el caso donde el total es cero.
            return go.Indicator(  # Crea un objeto Indicator de Plotly para el gráfico gauge.
                mode="gauge+number",  # Establece el modo del gráfico como gauge y número.
                value=porcentaje,  # Establece el valor del indicador (el porcentaje calculado).
                number={"suffix": "%", "font": {"size": 24}},  # Formatea el número con un sufijo de porcentaje y tamaño de fuente.
                title={"text": f"<b>{titulo}</b><br><span style='font-size:0.8em'>S/ {valor:,.0f}</span>", "font": {"size": 16}},  # Establece el título del gráfico, incluyendo el valor en soles formateado.
                gauge={  # Configura el gauge (la parte visual del medidor).
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkgray"},  # Configura el eje del gauge, incluyendo el rango y el formato de las marcas.
                    "bar": {"color": color},  # Establece el color de la barra del gauge.
                    "bgcolor": "white",  # Establece el color de fondo del gauge.
                    "borderwidth": 1,  # Establece el ancho del borde del gauge.
                    "bordercolor": "gray",  # Establece el color del borde del gauge.
                    "steps": [  # Define los pasos del gauge con sus rangos y colores.
                        {"range": [0, 50], "color": "#f2f2f2"},  # Paso 1: 0-50% (color gris claro).
                        {"range": [50, 80], "color": "#d9ead3"},  # Paso 2: 50-80% (color verde claro).
                        {"range": [80, 100], "color": "#b6d7a8"},  # Paso 3: 80-100% (color verde más oscuro).
                    ]
                }
            )

        # Mostrar indicadores clave con gráficos tipo gauge
        col1, col2, col3 = st.columns(3)  # Crea tres columnas en la página para mostrar los tres gráficos gauge uno al lado del otro.
        with col1:  # En la primera columna, muestra el gráfico de porcentaje de certificado.
            fig_cert = go.Figure(crear_gauge(certificado, pim, "% Certificado", "#1f77b4"))  # Crea el gráfico gauge para el certificado.
            st.plotly_chart(fig_cert, use_container_width=True)  # Muestra el gráfico en Streamlit, ajustando el ancho al contenedor.
        with col2:  # En la segunda columna, muestra el gráfico de porcentaje de compromiso.
            fig_comp = go.Figure(crear_gauge(compromiso, pim, "% Compromiso", "#ff7f0e"))  # Crea el gráfico gauge para el compromiso.
            st.plotly_chart(fig_comp, use_container_width=True)  # Muestra el gráfico en Streamlit, ajustando el ancho al contenedor.
        with col3:  # En la tercera columna, muestra el gráfico de porcentaje de devengado.
            fig_dev = go.Figure(crear_gauge(devengado, pim, "% Devengado", "#2ca02c"))  # Crea el gráfico gauge para el devengado.
            st.plotly_chart(fig_dev, use_container_width=True)  # Muestra el gráfico en Streamlit, ajustando el ancho al contenedor.

        # Tabla resumen por genérica
        resumen = df.groupby("generica").agg({  # Agrupa el DataFrame por la columna "generica" y calcula las sumas de las columnas numéricas.
            "Presupuesto Inicial (PIM)": "sum",
            "Certificado": "sum",
            "Compromiso Anual": "sum",
            "Devengado Total": "sum",
            "Saldo Restante": "sum"
        }).reset_index()  # Convierte el resultado agrupado a un nuevo DataFrame.
        resumen["PIM - Certificado"] = resumen["Presupuesto Inicial (PIM)"] - resumen["Certificado"]  # Calcula la diferencia entre el presupuesto inicial y el certificado para cada genérica.
        resumen["% Ejecución"] = (resumen["Devengado Total"] / resumen["Presupuesto Inicial (PIM)"] * 100).round(2)  # Calcula el porcentaje de ejecución para cada genérica.

        # Reordenar columnas
        cols_orden = ["Presupuesto Inicial (PIM)", "Certificado", "PIM - Certificado", "Compromiso Anual", "Devengado Total", "Saldo Restante", "% Ejecución"]  # Define el orden deseado de las columnas.
        resumen = resumen[["generica"] + cols_orden]  # Reordena las columnas del DataFrame resumen.

        # Mostrar tabla con totales
        st.subheader("Resumen por Genérica")  # Agrega un subencabezado a la página para la tabla resumen.
        resumen_total = resumen[cols_orden].select_dtypes(include='number').sum().to_frame().T # Calcula la suma de las columnas numéricas del dataframe `resumen` y la transpone para que quede como una fila.
        resumen_total.insert(0, "generica", "TOTAL")  # Inserta una columna "generica" con el valor "TOTAL" en la primera posición.
        resumen = pd.concat([resumen, resumen_total], ignore_index=True)  # Concatena el DataFrame resumen con la fila de totales.
        resumen_formateado = resumen.applymap(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)  # Formatea los números en el DataFrame resumen_formateado para que se muestren con separador de miles y sin decimales.
        st.dataframe(resumen_formateado, use_container_width=True)  # Muestra el DataFrame formateado en Streamlit, ajustando el ancho al contenedor.

        # Gráfico de evolución mensual
        st.subheader("Evolución del Devengado Mensual")  # Agrega un subencabezado a la página para el gráfico de evolución mensual.
        if "generica" not in df.columns:  # Verifica si la columna "generica" existe en el DataFrame.
            st.warning("No se encontró la columna 'generica' para graficar la evolución mensual.")  # Muestra una advertencia si no se encuentra la columna.
        else:
            dev_mes_gen = df.melt(id_vars=["generica"], value_vars=columnas_devengado, var_name="Mes", value_name="Monto")  # Convierte el DataFrame a formato largo para el gráfico de barras apiladas, usando "generica" como identificador.
            dev_mes_gen["Mes"] = dev_mes_gen["Mes"].str.replace("Devengado ", "")  # Elimina el prefijo "Devengado " de los nombres de los meses.
            dev_mes_gen["Monto"] = dev_mes_gen["Monto"] / 1000  # Convierte el monto a miles de soles para mejorar la legibilidad del gráfico.

            fig_bar = px.bar(  # Crea un gráfico de barras apiladas con Plotly Express.
                dev_mes_gen,  # Usa el DataFrame dev_mes_gen como fuente de datos.
                x="Mes",  # Establece la columna "Mes" en el eje x.
                y="Monto",  # Establece la columna "Monto" en el eje y.
                color="generica",  # Usa la columna "generica" para asignar colores a las barras, creando la apilación.
                text="Monto",  # Etiqueta cada segmento de la barra con el valor del monto.
                labels={"Monto": "Miles de S/"},  # Renombra la etiqueta del eje y.
            )
            fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_bar.update_layout(barmode="stack", uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig_bar, use_container_width=True)  # Muestra el gráfico de barras en Streamlit, ajustando el ancho al contenedor.

    except Exception as e:  # Captura cualquier excepción que ocurra dentro del bloque try.
        st.error(f"Error al procesar el archivo: {e}")  # Muestra un mensaje de error con la excepción capturada.
else:  # Si no se ha cargado ningún archivo.
    st.info("Por favor, cargue un archivo Excel válido para comenzar.")  # Muestra un mensaje informativo solicitando cargar un archivo Excel.
