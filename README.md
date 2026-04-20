# mi-tablero-python
📊 Tablero Presupuestal SIAF
Dashboard interactivo para el seguimiento de ejecución presupuestal, construido con Streamlit.
Estructura del proyecto
```
├── Respaldo_Data/          # Archivos Excel y programación guardada
│   └── .gitkeep
├── src/
│   ├── app.py              # Punto de entrada principal
│   ├── config.py           # Constantes, colores, programación precargada
│   ├── components/
│   │   ├── sidebar.py          # Filtros laterales
│   │   ├── gauges.py           # Indicadores gauge
│   │   ├── summary_table.py    # Tabla resumen por genérica
│   │   ├── drilldown_detail.py # Top 20% clasificadores por PIM
│   │   ├── monthly_chart.py    # Gráfico evolución mensual
│   │   └── programacion_form.py # Formulario de programación editable
│   └── utils/
│       ├── data_processor.py   # Pipeline de procesamiento SIAF
│       └── file_handler.py     # Gestión del repositorio de archivos
└── README.md
 ── rqueriments
```
Instalación
```bash
pip install streamlit pandas plotly openpyxl xlrd pytz
```
Ejecución
```bash
# Desde la raíz del proyecto
streamlit run src/app.py
```
Características
Carga dinámica: Sube archivos `.xls` / `.xlsx` del SIAF; se guardan en `Respaldo_Data/`
Repositorio local: Selecciona y carga archivos previamente guardados desde la barra lateral
Filtros dinámicos: Por genérica, unidad ejecutora, rubro y proyecto
Indicadores gauge: Certificado, Compromiso y Devengado con meta teórica automática
Drill-down: Top 20% de clasificadores por PIM, desplegable por genérica
Gráfico mensual: Barras apiladas por genérica + línea de programación
Programación editable: Datos precargados de la programación oficial IPEN 2026, editables y persistibles
Datos precargados
La programación mensual en `config.py` corresponde a la tabla oficial aprobada para IPEN 2026.
Para otras entidades, editar directamente en la pestaña 📅 Programación dentro de la app.
