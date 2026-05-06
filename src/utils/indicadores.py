# src/utils/indicadores.py
# ─────────────────────────────────────────────────────────────────────────────
# Cálculo de los 47 indicadores derivables de la data SIAF
# Categorías: Ejecución, Eficiencia ciclo, Proyección, Riesgo, Distribución,
#             Comparativos, Calidad de dato, Estratégicos
# ─────────────────────────────────────────────────────────────────────────────

import logging
from datetime import datetime, date
from typing import Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORÍA 1: EJECUCIÓN PRESUPUESTAL (9 indicadores)
# ═══════════════════════════════════════════════════════════════════════════

def calcular_ejecucion(df: pd.DataFrame, columnas: dict) -> dict:
    """
    Calcula los 9 indicadores de ejecución presupuestal estándar SIAF-MEF.

    Args:
        df: DataFrame con datos del Excel SIAF
        columnas: Dict con nombres de columnas detectadas
                  {"pim": "mto_pim", "certificado": "mto_certificado", ...}

    Returns:
        Dict con totales y porcentajes calculados
    """
    pim         = df[columnas["pim"]].sum() if columnas.get("pim") else 0
    certificado = df[columnas["certificado"]].sum() if columnas.get("certificado") else 0
    compromiso  = df[columnas["compromiso"]].sum() if columnas.get("compromiso") else 0
    devengado   = sum(df[c].sum() for c in columnas.get("devengado", []))
    girado      = df[columnas["girado"]].sum() if columnas.get("girado") else 0
    pagado      = df[columnas["pagado"]].sum() if columnas.get("pagado") else 0

    # Función helper para evitar división por cero
    def pct(num: float, den: float) -> float:
        return (num / den * 100) if den > 0 else 0

    return {
        # Totales absolutos
        "pim_total": pim,
        "certificado_total": certificado,
        "compromiso_total": compromiso,
        "devengado_total": devengado,
        "girado_total": girado,
        "pagado_total": pagado,

        # Porcentajes oficiales (vs PIM)
        "pct_certificado": pct(certificado, pim),
        "pct_compromiso":  pct(compromiso, pim),
        "pct_avance_financiero": pct(devengado, pim),  # Indicador oficial DGPP-MEF
        "pct_girado": pct(girado, pim),
        "pct_pagado": pct(pagado, pim),

        # Saldos disponibles (cuánto queda en cada fase)
        "saldo_certificable":   max(pim - certificado, 0),
        "saldo_comprometible":  max(certificado - compromiso, 0),
        "pendiente_devengar":   max(compromiso - devengado, 0),
        "pendiente_girar":      max(devengado - girado, 0),
        "pendiente_pagar":      max(girado - pagado, 0),
    }


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORÍA 2: EFICIENCIA DEL CICLO (8 indicadores)
# ═══════════════════════════════════════════════════════════════════════════

def calcular_eficiencia(df: pd.DataFrame, columnas: dict, fecha_corte: Optional[date] = None) -> dict:
    """
    Calcula ratios de eficiencia del ciclo presupuestal.

    Mide qué tan bien fluye el presupuesto entre fases:
    Certificación → Compromiso → Devengado → Girado → Pagado
    """
    if fecha_corte is None:
        fecha_corte = date.today()

    e = calcular_ejecucion(df, columnas)
    inicio_anio = date(fecha_corte.year, 1, 1)
    dias_transcurridos = max((fecha_corte - inicio_anio).days, 1)

    def ratio(num: float, den: float) -> float:
        return (num / den * 100) if den > 0 else 0

    return {
        # Eficiencia entre fases (qué % del paso anterior se materializa)
        "ratio_compro_certif":  ratio(e["compromiso_total"], e["certificado_total"]),
        "ratio_deveng_compro":  ratio(e["devengado_total"], e["compromiso_total"]),
        "ratio_girado_deveng":  ratio(e["girado_total"], e["devengado_total"]),
        "ratio_pagado_girado":  ratio(e["pagado_total"], e["girado_total"]),

        # Velocidad temporal
        "velocidad_diaria_soles": e["devengado_total"] / dias_transcurridos,
        "dias_transcurridos": dias_transcurridos,

        # Ciclo completo (% del PIM que llegó a pagado)
        "ciclo_completo_pct":   ratio(e["pagado_total"], e["pim_total"]),

        # Días estimados Devengado → Girado (proxy: pendiente_girar / velocidad_diaria)
        "dias_dev_a_girado_estimado": (
            e["pendiente_girar"] / max(e["velocidad_diaria_soles"] if "velocidad_diaria_soles" in dir() else 1, 1)
            if e.get("pendiente_girar", 0) > 0 else 0
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORÍA 3: PROYECCIÓN Y FORECASTING (7 indicadores)
# ═══════════════════════════════════════════════════════════════════════════

def calcular_proyecciones(
    df: pd.DataFrame,
    columnas: dict,
    fecha_corte: Optional[date] = None,
    metodo: str = "lineal",
) -> dict:
    """
    Calcula proyecciones de cierre fiscal.

    Args:
        df: DataFrame con datos SIAF
        columnas: Dict con nombres de columnas
        fecha_corte: Fecha de corte para la proyección
        metodo: 'lineal' (extrapolación simple) o 'regresion' (polyfit)

    Returns:
        Dict con proyecciones, brechas y velocidades requeridas
    """
    if fecha_corte is None:
        fecha_corte = date.today()

    e = calcular_ejecucion(df, columnas)
    fin_anio = date(fecha_corte.year, 12, 31)
    inicio = date(fecha_corte.year, 1, 1)

    dias_transcurridos = max((fecha_corte - inicio).days, 1)
    dias_restantes = max((fin_anio - fecha_corte).days, 1)
    dias_total = (fin_anio - inicio).days + 1  # 365 o 366

    # Velocidad actual
    velocidad_actual = e["devengado_total"] / dias_transcurridos

    # Proyección lineal simple (asume mismo ritmo)
    if metodo == "lineal":
        proyeccion = velocidad_actual * dias_total
    else:
        # Regresión sobre devengado mensual acumulado
        meses_devengado = []
        acumulado = 0
        for col in columnas.get("devengado", []):
            acumulado += df[col].sum()
            meses_devengado.append(acumulado)

        if len(meses_devengado) >= 2:
            x = np.arange(1, len(meses_devengado) + 1)
            y = np.array(meses_devengado)
            coef = np.polyfit(x, y, 1)  # grado 1
            proyeccion = np.polyval(coef, 12)
            # R² para confianza
            y_pred = np.polyval(coef, x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - y.mean()) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        else:
            proyeccion = velocidad_actual * dias_total
            r2 = 0

    proyeccion = max(proyeccion, e["devengado_total"])  # nunca menor a lo ya devengado
    brecha_proyectada = e["pim_total"] - proyeccion
    saldo_pendiente = e["pim_total"] - e["devengado_total"]
    velocidad_requerida = saldo_pendiente / dias_restantes if dias_restantes > 0 else 0

    # Mes proyectado para 100% (lineal)
    if velocidad_actual > 0:
        dias_para_100 = e["pim_total"] / velocidad_actual
        fecha_100 = inicio + pd.Timedelta(days=dias_para_100)
    else:
        fecha_100 = None

    return {
        "proyeccion_cierre": proyeccion,
        "proyeccion_pct":    (proyeccion / e["pim_total"] * 100) if e["pim_total"] > 0 else 0,
        "brecha_proyectada": brecha_proyectada,
        "dias_restantes_fiscal": dias_restantes,
        "velocidad_requerida_diaria": velocidad_requerida,
        "multiplicador_aceleracion":  velocidad_requerida / velocidad_actual if velocidad_actual > 0 else float('inf'),
        "mes_proyectado_100pct": fecha_100.strftime("%b %Y") if fecha_100 else "Nunca a este ritmo",
        "metodo_proyeccion": metodo,
        "r2_confianza": r2 if metodo == "regresion" else None,
    }


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORÍA 4: RIESGO Y ALERTAS (6 indicadores)
# ═══════════════════════════════════════════════════════════════════════════

def detectar_alertas(df: pd.DataFrame, columnas: dict, fecha_corte: Optional[date] = None) -> list:
    """
    Detecta alertas activas en la ejecución presupuestal.

    Returns:
        Lista de alertas, cada una con severidad ('critica', 'alta', 'media'),
        título, descripción y categoría afectada.
    """
    if fecha_corte is None:
        fecha_corte = date.today()

    alertas = []
    e = calcular_ejecucion(df, columnas)
    proy = calcular_proyecciones(df, columnas, fecha_corte)

    # Alerta 1: Riesgo de subejecución crítica (proyección < 80% del PIM)
    if proy["proyeccion_pct"] < 80:
        severidad = "critica" if proy["proyeccion_pct"] < 60 else "alta"
        alertas.append({
            "severidad": severidad,
            "categoria": "Riesgo subejecución",
            "titulo": f"Proyección al cierre: {proy['proyeccion_pct']:.1f}%",
            "descripcion": f"A ritmo actual se proyecta cerrar en {proy['proyeccion_pct']:.1f}% del PIM. "
                          f"Brecha esperada: S/ {proy['brecha_proyectada']/1e6:.1f}M.",
        })

    # Alerta 2: Velocidad insuficiente
    if proy["multiplicador_aceleracion"] > 2:
        alertas.append({
            "severidad": "critica" if proy["multiplicador_aceleracion"] > 3 else "alta",
            "categoria": "Velocidad",
            "titulo": f"Velocidad {proy['multiplicador_aceleracion']:.1f}× insuficiente",
            "descripcion": f"Necesita acelerar el devengado {proy['multiplicador_aceleracion']:.1f}× "
                          f"para alcanzar 100% del PIM.",
        })

    # Alerta 3: Genéricas inactivas (pasados 4 meses sin ejecutar)
    if "generica" in columnas and fecha_corte.month >= 4:
        for gen in df[columnas["generica"]].unique():
            df_gen = df[df[columnas["generica"]] == gen]
            deveng_gen = sum(df_gen[c].sum() for c in columnas.get("devengado", []))
            pim_gen = df_gen[columnas["pim"]].sum() if columnas.get("pim") else 0
            if pim_gen > 0 and deveng_gen == 0:
                alertas.append({
                    "severidad": "alta",
                    "categoria": "Genérica inactiva",
                    "titulo": f"{gen[:40]}...",
                    "descripcion": f"PIM S/ {pim_gen/1e6:.1f}M sin ningún devengado al mes {fecha_corte.month}.",
                })

    # Alerta 4: Pendiente de girar elevado (>15% del devengado)
    if e["devengado_total"] > 0 and (e["pendiente_girar"] / e["devengado_total"]) > 0.15:
        alertas.append({
            "severidad": "media",
            "categoria": "Tesorería",
            "titulo": "Pendiente de girar elevado",
            "descripcion": f"S/ {e['pendiente_girar']/1e6:.1f}M devengado sin girar "
                          f"({e['pendiente_girar']/e['devengado_total']*100:.1f}% del total).",
        })

    # Alerta 5: Concentración crítica fin de año (típica subejecución que se acelera en Q4)
    if fecha_corte.month <= 9:  # alertar antes de octubre
        meta_teorica_pct = (fecha_corte.month / 12) * 100
        gap = meta_teorica_pct - e["pct_avance_financiero"]
        if gap > 15:
            alertas.append({
                "severidad": "alta" if gap > 25 else "media",
                "categoria": "Estacionalidad",
                "titulo": f"Rezago de {gap:.1f}pp vs meta teórica",
                "descripcion": f"Al mes {fecha_corte.month} debería estar en {meta_teorica_pct:.0f}% "
                              f"y está en {e['pct_avance_financiero']:.1f}%. Riesgo de concentración Q4.",
            })

    return alertas


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORÍA 5: DISTRIBUCIÓN Y COMPOSICIÓN (7 indicadores)
# ═══════════════════════════════════════════════════════════════════════════

def calcular_distribucion(df: pd.DataFrame, columnas: dict) -> dict:
    """
    Calcula indicadores de distribución y concentración del gasto.
    """
    devengado_cols = columnas.get("devengado", [])
    df = df.copy()
    df["_devengado_total"] = df[devengado_cols].sum(axis=1) if devengado_cols else 0

    resultado = {}

    # Por genérica
    if "generica" in columnas and columnas["generica"] in df.columns:
        por_generica = df.groupby(columnas["generica"]).agg({
            columnas["pim"]: "sum",
            "_devengado_total": "sum",
        }).reset_index()
        por_generica.columns = ["generica", "pim", "devengado"]
        por_generica["pct_avance"] = (por_generica["devengado"] / por_generica["pim"] * 100).fillna(0)
        resultado["por_generica"] = por_generica.to_dict("records")

    # Top 10 clasificadores específicos
    if "clasificador" in columnas:
        top10 = df.nlargest(10, columnas["pim"])[[columnas["clasificador"], columnas["pim"], "_devengado_total"]]
        top10.columns = ["clasificador", "pim", "devengado"]
        resultado["top10_clasificadores"] = top10.to_dict("records")

    # Concentración: ¿qué % del PIM está en el top 20% de partidas?
    if columnas.get("pim"):
        df_sorted = df.sort_values(columnas["pim"], ascending=False)
        top_20pct = int(len(df_sorted) * 0.2)
        concentracion = df_sorted.head(top_20pct)[columnas["pim"]].sum() / df[columnas["pim"]].sum() * 100
        resultado["concentracion_pareto"] = concentracion
        resultado["partidas_activas"] = len(df_sorted[df_sorted["_devengado_total"] > 0])
        resultado["partidas_totales"] = len(df_sorted)

    # Por fuente de financiamiento
    if "fuente" in columnas and columnas["fuente"] in df.columns:
        por_fuente = df.groupby(columnas["fuente"]).agg({
            columnas["pim"]: "sum",
            "_devengado_total": "sum",
        }).reset_index()
        por_fuente.columns = ["fuente", "pim", "devengado"]
        resultado["por_fuente"] = por_fuente.to_dict("records")

    # Gasto corriente vs capital (genéricas 1-4 vs 5-6 según taxonomía MEF)
    if "generica" in columnas:
        df["_es_corriente"] = df[columnas["generica"]].str.startswith(("1.", "2.", "3.", "4."))
        corriente = df[df["_es_corriente"]]["_devengado_total"].sum()
        capital   = df[~df["_es_corriente"]]["_devengado_total"].sum()
        total = corriente + capital
        resultado["gasto_corriente_pct"] = (corriente / total * 100) if total > 0 else 0
        resultado["gasto_capital_pct"]   = (capital / total * 100) if total > 0 else 0

    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORÍA 6: COMPARATIVOS (5 indicadores)
# ═══════════════════════════════════════════════════════════════════════════

def calcular_comparativos(df_actual: pd.DataFrame, df_anterior: Optional[pd.DataFrame],
                          columnas: dict, fecha_corte: Optional[date] = None) -> dict:
    """
    Compara ejecución actual vs período anterior.

    Args:
        df_actual: DataFrame del año fiscal actual
        df_anterior: DataFrame del año anterior (opcional)
        columnas: Mapeo de columnas
        fecha_corte: Para comparar al mismo punto en el tiempo
    """
    actual = calcular_ejecucion(df_actual, columnas)
    resultado = {"actual": actual}

    if df_anterior is not None and not df_anterior.empty:
        anterior = calcular_ejecucion(df_anterior, columnas)
        resultado["anterior"] = anterior

        # Variaciones
        def var_pct(act, ant):
            return ((act - ant) / ant * 100) if ant > 0 else 0

        resultado["variaciones"] = {
            "pim_var_pct":            var_pct(actual["pim_total"], anterior["pim_total"]),
            "devengado_var_pct":      var_pct(actual["devengado_total"], anterior["devengado_total"]),
            "pct_avance_diferencia":  actual["pct_avance_financiero"] - anterior["pct_avance_financiero"],
        }

    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN MAESTRA: Calcula todos los indicadores en un solo llamado
# ═══════════════════════════════════════════════════════════════════════════

def calcular_todos_indicadores(
    df: pd.DataFrame,
    columnas: dict,
    df_historico: Optional[pd.DataFrame] = None,
    fecha_corte: Optional[date] = None,
) -> dict:
    """
    Función principal: calcula los 47 indicadores en un solo objeto.

    Args:
        df: DataFrame del año fiscal actual
        columnas: Mapeo de columnas detectadas
        df_historico: DataFrame del año anterior (opcional, para comparativos)
        fecha_corte: Fecha de corte (default: hoy)

    Returns:
        Dict con todas las categorías:
        {
            "ejecucion": {...},
            "eficiencia": {...},
            "proyecciones": {...},
            "alertas": [...],
            "distribucion": {...},
            "comparativos": {...},
        }
    """
    if fecha_corte is None:
        fecha_corte = date.today()

    return {
        "ejecucion":     calcular_ejecucion(df, columnas),
        "eficiencia":    calcular_eficiencia(df, columnas, fecha_corte),
        "proyecciones":  calcular_proyecciones(df, columnas, fecha_corte),
        "alertas":       detectar_alertas(df, columnas, fecha_corte),
        "distribucion":  calcular_distribucion(df, columnas),
        "comparativos":  calcular_comparativos(df, df_historico, columnas, fecha_corte),
        "fecha_corte":   fecha_corte.isoformat(),
    }
