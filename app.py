import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime
from io import BytesIO

# ── Configuración de la página ───────────────────────────────────────────────
st.set_page_config(page_title="Tablero Presupuestal IPEN", layout="wide")

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-size: 16px; font-weight: 600; }
    .section-title {
        font-size: 15px; font-weight: 700; color: #1a3a5c;
        border-left: 4px solid #1a3a5c; padding-left: 8px;
        margin: 18px 0 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# CSS base que se inyecta dentro de cada iframe de components.html
TABLE_CSS = """
<style>
  body { margin: 0; padding: 0; font-family: Arial, sans-serif; font-size: 12.5px; }
  table { border-collapse: collapse; width: 100%; }
  th {
    background-color: #1a3a5c; color: white;
    padding: 7px 9px; text-align: center;
    border: 1px solid #0f2540;
  }
  td {
    padding: 6px 9px;
    border-bottom: 1px solid #d0d0d0;
    border-right: 1px solid #e8e8e8;
  }
  tr:nth-child(even) td { background-color: #f4f6f9; }
</style>
"""


def render_table(html_body: str, height: int = 300):
    """Renderiza HTML dentro de un iframe via st.components.v1.html."""
    full = f"<!DOCTYPE html><html><head>{TABLE_CSS}</head><body>{html_body}</body></html>"
    components.html(full, height=height, scrolling=False)


# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.image("https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png", width=230)
st.sidebar.header("📁 Carga de Datos")

opcion_carga = st.sidebar.radio(
    "Seleccione método de carga:",
    ["Cargar archivo Excel", "Ingresar datos manualmente"]
)

if "df_datos" not in st.session_state:
    st.session_state.df_datos = None
if "datos_manuales" not in st.session_state:
    st.session_state.datos_manuales = None

MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
         'Julio','Agosto','Setiembre','Octubre','Noviembre','Diciembre']

# ── Carga de archivo Excel ───────────────────────────────────────────────────
if opcion_carga == "Cargar archivo Excel":
    archivo = st.sidebar.file_uploader("Seleccionar archivo Excel", type=["xls","xlsx"])
    if archivo:
        carpeta = "Respaldo_Data"
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, archivo.name)
        with open(ruta, "wb") as f:
            f.write(archivo.getbuffer())
        try:
            df = pd.read_excel(ruta)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            col_pim = next((c for c in df.columns if 'pim' in c), None)
            if col_pim:
                df.rename(columns={col_pim: "PIM"}, inplace=True)

            col_pia = next((c for c in df.columns if 'pia' in c), None)
            df["PIA"] = df[col_pia] if col_pia else df["PIM"]

            for src, dst in [('mto_certificado', 'Certificado'), ('mto_compro_anual', 'Compromiso')]:
                df[dst] = df[src] if src in df.columns else 0

            for i, mes in enumerate(MESES, 1):
                col = f'mto_devenga_{i:02d}'
                df[f"Dev_{mes}"] = df[col] if col in df.columns else 0

            if 'tipo_act_obra_ac' in df.columns:
                df['Tipo_Gasto'] = df['tipo_act_obra_ac'].apply(
                    lambda x: 'ACTIVIDAD' if str(x).startswith('5')
                    else ('INVERSION' if str(x).startswith('4') else 'OTROS'))
            else:
                df['Tipo_Gasto'] = 'ACTIVIDAD'

            df['Genérica'] = df['generica'] if 'generica' in df.columns else 'General'
            df['Devengado_Total'] = df[[f"Dev_{m}" for m in MESES]].sum(axis=1)
            df['Saldo'] = df['PIM'] - df['Devengado_Total']

            st.session_state.df_datos = df
            st.sidebar.success("✅ Archivo cargado correctamente")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# ── Ingreso manual ────────────────────────────────────────────────────────────
elif opcion_carga == "Ingresar datos manualmente":
    with st.sidebar.form("form_manual"):
        tipo_gasto  = st.selectbox("Tipo de Gasto", ["ACTIVIDAD","INVERSION"])
        generica    = st.selectbox("Genérica", [
            "2.1 PERSONAL Y OBLIGACIONES SOCIALES",
            "2.2 PENSIONES Y OTRAS PRESTACIONES SOCIALES",
            "2.3 BIENES Y SERVICIOS",
            "2.5 OTROS GASTOS",
            "2.6 ADQUISICION DE ACTIVOS NO FINANCIEROS"])
        pia         = st.number_input("PIA (S/.)",         min_value=0.0, step=1000.0, format="%.2f")
        pim         = st.number_input("PIM (S/.)",         min_value=0.0, step=1000.0, format="%.2f")
        certificado = st.number_input("Certificado (S/.)", min_value=0.0, step=1000.0, format="%.2f")
        compromiso  = st.number_input("Compromiso (S/.)",  min_value=0.0, step=1000.0, format="%.2f")

        st.markdown("**Devengado Mensual (S/.)**")
        cols_ui = st.columns(3)
        devs = []
        for i, mes in enumerate(MESES):
            with cols_ui[i % 3]:
                v = st.number_input(mes, key=f"d_{mes}", min_value=0.0, step=100.0, format="%.2f")
                devs.append(v)

        if st.form_submit_button("Agregar"):
            reg = {'Tipo_Gasto': tipo_gasto, 'Genérica': generica,
                   'PIA': pia, 'PIM': pim, 'Certificado': certificado,
                   'Compromiso': compromiso,
                   'Devengado_Total': sum(devs), 'Saldo': pim - sum(devs)}
            for mes, v in zip(MESES, devs):
                reg[f"Dev_{mes}"] = v
            nuevo = pd.DataFrame([reg])
            st.session_state.datos_manuales = (
                nuevo if st.session_state.datos_manuales is None
                else pd.concat([st.session_state.datos_manuales, nuevo], ignore_index=True))
            st.session_state.df_datos = st.session_state.datos_manuales
            st.sidebar.success("✅ Datos agregados")

    if st.session_state.datos_manuales is not None:
        if st.sidebar.button("🗑️ Limpiar datos"):
            st.session_state.datos_manuales = None
            st.session_state.df_datos = None
            st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
#  VISUALIZACIÓN
# ════════════════════════════════════════════════════════════════════════════════
if st.session_state.df_datos is not None:
    df = st.session_state.df_datos.copy()

    # Filtros
    st.sidebar.header("🔍 Filtros")
    f_tipo = st.sidebar.selectbox("Tipo de Gasto", ["TODOS"] + sorted(df['Tipo_Gasto'].unique()))
    f_gen  = st.sidebar.selectbox("Genérica",      ["TODAS"] + sorted(df['Genérica'].unique()))

    dff = df.copy()
    if f_tipo != "TODOS": dff = dff[dff['Tipo_Gasto'] == f_tipo]
    if f_gen  != "TODAS": dff = dff[dff['Genérica']   == f_gen]
    if dff.empty:
        st.warning("Sin datos para los filtros seleccionados")
        st.stop()

    # Helpers
    def tot(col):  return dff[col].sum() if col in dff.columns else 0
    def pct(a, b): return round(a / b * 100, 1) if b else 0.0
    def fmt(v):    return f"{v:,.0f}"
    def fmtd(v):   return f"{v:,.2f}"

    PIA_T   = tot('PIA')
    PIM_T   = tot('PIM')
    CERT_T  = tot('Certificado')
    COMP_T  = tot('Compromiso')
    DEV_T   = tot('Devengado_Total')
    SALDO_T = PIM_T - DEV_T

    # Encabezado
    col_logo, col_titulo = st.columns([1, 7])
    with col_logo:
        st.image("https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png", width=100)
    with col_titulo:
        st.markdown("## INSTITUTO PERUANO DE ENERGÍA NUCLEAR")
        st.markdown(f"### EJECUCIÓN PRESUPUESTAL ({datetime.now().strftime('%d.%m.%Y')})")
    st.markdown("---")

    # ── TABLA PRINCIPAL ───────────────────────────────────────────────────────
    def build_main_table():
        rows = ""
        for tipo in ['ACTIVIDAD', 'INVERSION']:
            sub = dff[dff['Tipo_Gasto'] == tipo]
            if sub.empty:
                continue
            p   = sub['PIM'].sum()
            pia = sub['PIA'].sum() if 'PIA' in sub.columns else p
            c   = sub['Certificado'].sum()
            co  = sub['Compromiso'].sum()
            d   = sub['Devengado_Total'].sum()
            s   = p - d
            rows += (
                '<tr style="background:#ecf0f1; font-weight:600;">'
                + f'<td>{tipo}</td>'
                + f'<td style="text-align:right">{fmt(pia)}</td>'
                + f'<td style="text-align:right">{fmt(p)}</td>'
                + f'<td style="text-align:right">{fmtd(c)}</td>'
                + f'<td style="text-align:right">{pct(c,p):.1f}%</td>'
                + f'<td style="text-align:right">{fmtd(co)}</td>'
                + f'<td style="text-align:right">{pct(co,p):.1f}%</td>'
                + f'<td style="text-align:right">{fmtd(d)}</td>'
                + f'<td style="text-align:right">{pct(d,p):.1f}%</td>'
                + f'<td style="text-align:right">{fmtd(s)}</td>'
                + '</tr>'
            )
        rows += (
            '<tr style="background:#1a3a5c; color:white; font-weight:bold;">'
            + '<td>Total general</td>'
            + f'<td style="text-align:right">{fmt(PIA_T)}</td>'
            + f'<td style="text-align:right">{fmt(PIM_T)}</td>'
            + f'<td style="text-align:right">{fmtd(CERT_T)}</td>'
            + f'<td style="text-align:right">{pct(CERT_T,PIM_T):.1f}%</td>'
            + f'<td style="text-align:right">{fmtd(COMP_T)}</td>'
            + f'<td style="text-align:right">{pct(COMP_T,PIM_T):.1f}%</td>'
            + f'<td style="text-align:right">{fmtd(DEV_T)}</td>'
            + f'<td style="text-align:right">{pct(DEV_T,PIM_T):.1f}%</td>'
            + f'<td style="text-align:right">{fmtd(SALDO_T)}</td>'
            + '</tr>'
        )
        header = (
            '<thead><tr>'
            '<th style="text-align:left; min-width:110px">DETALLE</th>'
            '<th>PIA</th><th>PIM</th>'
            '<th>Certificado</th><th style="width:48px">%</th>'
            '<th>Compromiso</th><th style="width:48px">%.</th>'
            '<th>Devengado</th><th style="width:48px">.%</th>'
            '<th>Saldo por Ejecutar</th>'
            '</tr></thead>'
        )
        return '<table>' + header + '<tbody>' + rows + '</tbody></table>'

    render_table(build_main_table(), height=120)

    # ── GAUGES ────────────────────────────────────────────────────────────────
    def gauge(valor, total, titulo, color):
        pct_val = round(valor / total * 100 if total else 0, 1)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pct_val,
            number={'suffix': "%", 'font': {'size': 38, 'color': color}},
            title={'text': "<b>% " + titulo + "</b><br><span style='font-size:12px'>" + fmtd(valor) + "</span>",
                   'font': {'size': 16}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickfont': {'size': 9}},
                'bar': {'color': color, 'thickness': 0.28},
                'bgcolor': "white", 'borderwidth': 1, 'bordercolor': "gray",
                'steps': [
                    {'range': [0,  50], 'color': '#f2f2f2'},
                    {'range': [50, 80], 'color': '#e8f5e9'},
                    {'range': [80,100], 'color': '#c8e6c9'},
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}
            }
        ))
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=70, b=10),
                          paper_bgcolor='rgba(0,0,0,0)')
        return fig

    g1, g2, g3 = st.columns(3)
    with g1: st.plotly_chart(gauge(CERT_T, PIM_T, "Certificado", "#1f77b4"), use_container_width=True, key="g_cert")
    with g2: st.plotly_chart(gauge(COMP_T, PIM_T, "Compromiso",  "#e6a817"), use_container_width=True, key="g_comp")
    with g3: st.plotly_chart(gauge(DEV_T,  PIM_T, "Devengado",   "#2ca02c"), use_container_width=True, key="g_dev")

    # ── I. EJECUCIÓN MENSUALIZADA ─────────────────────────────────────────────
    st.markdown('<div class="section-title">I. EJECUCION MENSUALIZADA</div>', unsafe_allow_html=True)

    def mes_ejec(tipo_filter):
        sub = dff[dff['Tipo_Gasto'] == tipo_filter]
        return {m: (sub[f"Dev_{m}"].sum() if f"Dev_{m}" in sub.columns else 0) for m in MESES}

    def mes_prog(tipo_filter):
        sub = dff[dff['Tipo_Gasto'] == tipo_filter]
        pim_sub = sub['PIM'].sum()
        return {m: (sub[f"Prog_{m}"].sum() if f"Prog_{m}" in sub.columns
                    else round(pim_sub / 12, 0)) for m in MESES}

    act_ejec = mes_ejec('ACTIVIDAD');  act_prog = mes_prog('ACTIVIDAD')
    inv_ejec = mes_ejec('INVERSION');  inv_prog = mes_prog('INVERSION')

    def build_mensual_table():
        header = (
            '<thead>'
            '<tr>'
            '<th rowspan="2" style="text-align:left; min-width:90px"></th>'
            '<th colspan="3" style="background:#2c5f8a">ACTIVIDAD</th>'
            '<th colspan="3" style="background:#5a7a3a">INVERSION</th>'
            '<th colspan="3" style="background:#1a3a5c">TOTAL</th>'
            '</tr>'
            '<tr>'
            '<th style="background:#3a7ab5">PROGRAMADO</th>'
            '<th style="background:#3a7ab5">EJECUTADO</th>'
            '<th style="background:#3a7ab5; width:50px">%</th>'
            '<th style="background:#6a9a4a">PROGRAMADO</th>'
            '<th style="background:#6a9a4a">EJECUTADO</th>'
            '<th style="background:#6a9a4a; width:50px">%</th>'
            '<th style="background:#2a5a8c">PROGRAMADO</th>'
            '<th style="background:#2a5a8c">EJECUTADO</th>'
            '<th style="background:#2a5a8c; width:50px">%</th>'
            '</tr>'
            '</thead>'
        )
        rows = ""
        for mes in MESES:
            ap = act_prog[mes]; ae = act_ejec[mes]
            ip = inv_prog[mes]; ie = inv_ejec[mes]
            tp = ap + ip;       te = ae + ie
            a_p = "-" if not ap else (str(round(pct(ae,ap), 2)) + "%")
            i_p = "-" if not ip else (str(round(pct(ie,ip), 2)) + "%")
            t_p = "-" if not tp else (str(round(pct(te,tp), 2)) + "%")
            rows += (
                '<tr>'
                + '<td style="font-weight:600">' + mes + '</td>'
                + '<td style="text-align:right">' + fmt(ap) + '</td>'
                + '<td style="text-align:right">' + fmt(ae) + '</td>'
                + '<td style="text-align:right">' + a_p + '</td>'
                + '<td style="text-align:right">' + fmt(ip) + '</td>'
                + '<td style="text-align:right">' + fmt(ie) + '</td>'
                + '<td style="text-align:right">' + i_p + '</td>'
                + '<td style="text-align:right">' + fmt(tp) + '</td>'
                + '<td style="text-align:right">' + fmt(te) + '</td>'
                + '<td style="text-align:right">' + t_p + '</td>'
                + '</tr>'
            )
        return '<table>' + header + '<tbody>' + rows + '</tbody></table>'

    col_tab, col_chart = st.columns([3, 2])
    with col_tab:
        render_table(build_mensual_table(), height=430)

    with col_chart:
        meses_vis = [m for m in MESES
                     if act_ejec[m] + inv_ejec[m] > 0 or act_prog[m] + inv_prog[m] > 0] or MESES[:3]
        prog_vals = [act_prog[m] + inv_prog[m] for m in meses_vis]
        ejec_vals = [act_ejec[m] + inv_ejec[m] for m in meses_vis]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="EJECUTADO", x=meses_vis, y=ejec_vals,
            marker_color="#1f77b4",
            text=[f"{v:,.0f}" for v in ejec_vals],
            textposition="inside", textfont_size=11))
        fig_bar.add_trace(go.Scatter(
            name="PROGRAMADO", x=meses_vis, y=prog_vals,
            mode="lines+markers+text",
            line=dict(color="#e74c3c", width=2),
            marker=dict(size=8, color="#e74c3c"),
            text=[f"{v:,.0f}" for v in prog_vals],
            textposition="top center", textfont_size=10))
        fig_bar.update_layout(
            title=dict(text="Ejecución presupuestal mensual<br><sub>Programado vs. Ejecutado</sub>",
                       font=dict(size=13)),
            height=430,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#ececec"),
            yaxis=dict(gridcolor="#ececec", title="Monto (S/.)"),
            margin=dict(t=80, b=30, l=10, r=10)
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="bar_mensual")

    # ── II. EJECUCIÓN DEL MES MÁS RECIENTE ────────────────────────────────────
    mes_actual = next(
        (m for m in reversed(MESES) if f"Dev_{m}" in dff.columns and dff[f"Dev_{m}"].sum() > 0),
        MESES[0]
    )
    st.markdown(
        '<div class="section-title">II. EJECUCION ' + mes_actual.upper() + '</div>',
        unsafe_allow_html=True
    )

    col_dev = f"Dev_{mes_actual}"
    gen_grp = dff.groupby('Genérica').agg(
        PIM=('PIM', 'sum'),
        Dev=(col_dev, 'sum') if col_dev in dff.columns else ('Devengado_Total', 'sum')
    ).reset_index()
    col_prog_mes = f"Prog_{mes_actual}"
    gen_grp['Prog'] = (
        dff.groupby('Genérica')[col_prog_mes].sum().values
        if col_prog_mes in dff.columns
        else (gen_grp['PIM'] / 12).round(0)
    )

    def build_mes_table(df_gen, mes_label):
        header = (
            '<thead>'
            '<tr>'
            '<th style="text-align:left; min-width:220px">Genérica de Gasto</th>'
            '<th colspan="4" style="text-align:center">' + mes_label + '</th>'
            '</tr>'
            '<tr>'
            '<th style="background:#3a7ab5; text-align:left"></th>'
            '<th style="background:#3a7ab5">PROGRAMADO</th>'
            '<th style="background:#3a7ab5">EJECUTADO</th>'
            '<th style="background:#3a7ab5; width:55px">%</th>'
            '<th style="background:#3a7ab5">SALDO POR EJECUTAR</th>'
            '</tr>'
            '</thead>'
        )
        rows = ""
        for _, row in df_gen.iterrows():
            prog  = row['Prog'];  ejec = row['Dev']
            saldo = max(prog - ejec, 0)
            p_str = (str(round(pct(ejec, prog), 1)) + "%") if prog > 0 else "-"
            rows += (
                '<tr>'
                + '<td>' + str(row['Genérica']) + '</td>'
                + '<td style="text-align:right">' + fmt(prog) + '</td>'
                + '<td style="text-align:right">' + fmt(ejec) + '</td>'
                + '<td style="text-align:right">' + p_str + '</td>'
                + '<td style="text-align:right">' + fmt(saldo) + '</td>'
                + '</tr>'
            )
        tp = df_gen['Prog'].sum(); te = df_gen['Dev'].sum(); ts = max(tp - te, 0)
        tp_str = (str(round(pct(te, tp), 1)) + "%") if tp else "-"
        rows += (
            '<tr style="background:#1a3a5c; color:white; font-weight:bold;">'
            + '<td>TOTAL</td>'
            + '<td style="text-align:right">' + fmt(tp) + '</td>'
            + '<td style="text-align:right">' + fmt(te) + '</td>'
            + '<td style="text-align:right">' + tp_str + '</td>'
            + '<td style="text-align:right">' + fmt(ts) + '</td>'
            + '</tr>'
        )
        return '<table>' + header + '<tbody>' + rows + '</tbody></table>'

    render_table(build_mes_table(gen_grp, mes_actual), height=50 + len(gen_grp) * 38 + 60)

    # ── III. RESULTADOS POR GENÉRICA ──────────────────────────────────────────
    st.markdown('<div class="section-title">III. RESULTADOS POR GENÉRICA</div>',
                unsafe_allow_html=True)

    res_gen = dff.groupby('Genérica').agg(
        PIA=('PIA','sum') if 'PIA' in dff.columns else ('PIM','sum'),
        PIM=('PIM','sum'),
        Certificado=('Certificado','sum'),
        Compromiso=('Compromiso','sum'),
        Devengado=('Devengado_Total','sum')
    ).reset_index()
    res_gen['Saldo'] = res_gen['PIM'] - res_gen['Devengado']

    def build_generica_table(df_rg):
        header = (
            '<thead><tr>'
            '<th style="text-align:left; min-width:220px">Genérica</th>'
            '<th>PIA</th><th>PIM</th>'
            '<th>Certificado</th><th>Compromiso</th>'
            '<th>Devengado</th><th>Saldo</th><th>% Ejec</th>'
            '</tr></thead>'
        )
        rows = ""
        for _, r in df_rg.iterrows():
            rows += (
                '<tr>'
                + '<td>' + str(r['Genérica']) + '</td>'
                + '<td style="text-align:right">' + fmtd(r['PIA']) + '</td>'
                + '<td style="text-align:right">' + fmtd(r['PIM']) + '</td>'
                + '<td style="text-align:right">' + fmtd(r['Certificado']) + '</td>'
                + '<td style="text-align:right">' + fmtd(r['Compromiso']) + '</td>'
                + '<td style="text-align:right">' + fmtd(r['Devengado']) + '</td>'
                + '<td style="text-align:right">' + fmtd(r['Saldo']) + '</td>'
                + '<td style="text-align:right">' + str(round(pct(r['Devengado'], r['PIM']), 1)) + '%</td>'
                + '</tr>'
            )
        t_pia  = df_rg['PIA'].sum()
        t_pim  = df_rg['PIM'].sum()
        t_cert = df_rg['Certificado'].sum()
        t_comp = df_rg['Compromiso'].sum()
        t_dev  = df_rg['Devengado'].sum()
        t_sal  = df_rg['Saldo'].sum()
        rows += (
            '<tr style="background:#1a3a5c; color:white; font-weight:bold;">'
            + '<td>TOTAL</td>'
            + '<td style="text-align:right">' + fmtd(t_pia) + '</td>'
            + '<td style="text-align:right">' + fmtd(t_pim) + '</td>'
            + '<td style="text-align:right">' + fmtd(t_cert) + '</td>'
            + '<td style="text-align:right">' + fmtd(t_comp) + '</td>'
            + '<td style="text-align:right">' + fmtd(t_dev) + '</td>'
            + '<td style="text-align:right">' + fmtd(t_sal) + '</td>'
            + '<td style="text-align:right">' + str(round(pct(t_dev, t_pim), 1)) + '%</td>'
            + '</tr>'
        )
        return '<table>' + header + '<tbody>' + rows + '</tbody></table>'

    render_table(build_generica_table(res_gen), height=50 + len(res_gen) * 38 + 60)

    # ── Descarga ──────────────────────────────────────────────────────────────
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            dff.to_excel(writer, sheet_name='Datos', index=False)
            res_gen.to_excel(writer, sheet_name='Por Genérica', index=False)
        buf.seek(0)
        st.download_button(
            "📥 Exportar Excel", buf,
            file_name="reporte_ipen_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        st.download_button(
            "📥 Exportar CSV", dff.to_csv(index=False),
            file_name="reporte_ipen_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv",
            mime="text/csv")

    st.caption("Reporte generado: " + datetime.now().strftime('%d/%m/%Y %H:%M:%S')
               + " · Registros: " + str(len(dff)))

# ── Pantalla de bienvenida ─────────────────────────────────────────────────────
else:
    col_logo2, col_tit2 = st.columns([1, 6])
    with col_logo2:
        st.image("https://www.ipen.gob.pe/templates/ipen/images/logo-ipen.png", width=100)
    with col_tit2:
        st.markdown("## INSTITUTO PERUANO DE ENERGÍA NUCLEAR")
        st.markdown("### EJECUCIÓN PRESUPUESTAL")

    st.info("""
    ### 👋 Bienvenido al Tablero Presupuestal del IPEN

    Cargue un archivo Excel o ingrese datos manualmente desde la barra lateral izquierda.

    **Columnas esperadas en el Excel (formato SIAF):**
    `mto_pia`, `mto_pim`, `mto_certificado`, `mto_compro_anual`,
    `mto_devenga_01` … `mto_devenga_12`, `tipo_act_obra_ac`, `generica`
    """)

    with st.expander("Ver estructura esperada del archivo Excel"):
        st.markdown("""
| Columna | Descripción |
|---|---|
| `mto_pia` | Presupuesto Institucional de Apertura |
| `mto_pim` | Presupuesto Institucional Modificado |
| `mto_certificado` | Monto certificado |
| `mto_compro_anual` | Monto comprometido anual |
| `mto_devenga_01`–`mto_devenga_12` | Devengado mensual (01=Enero … 12=Diciembre) |
| `tipo_act_obra_ac` | Tipo: 5xxx = Actividad · 4xxx = Inversión |
| `generica` | Genérica de gasto |
        """)
