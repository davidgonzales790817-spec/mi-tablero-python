# src/utils/data_processor.py
# ─────────────────────────────────────────────────────────────────────────────
# Procesamiento de datos SIAF: detección automática de columnas,
# normalización, cálculo de métricas derivadas.
# ─────────────────────────────────────────────────────────────────────────────

import re
import numpy as np
import pandas as pd
import streamlit as st
from config import MESES, PATRONES_DEVENGADO, PATRONES_EXCLUIR


class DataProcessor:
    """
    Procesa un DataFrame crudo exportado del SIAF y devuelve un DataFrame
    normalizado con columnas estandarizadas.

    Uso:
        procesador = DataProcessor(df_raw)
        procesador.procesar_completo()
        df = procesador.obtener_dataframe()
        cols_dev = procesador.obtener_columnas_devengado()
    """

    def __init__(self, df: pd.DataFrame):
        self.df               = df.copy()
        self.columnas_devengado: list[str] = []
        self.col_pim          = None
        self.col_certificado  = None
        self.col_compromiso   = None
        self.col_generica     = None

    # ── Paso 1 ────────────────────────────────────────────────────────────────

    def normalizar_columnas(self):
        """Limpia espacios, pasa a minúsculas y reemplaza espacios por '_'."""
        self.df.columns = (
            self.df.columns.str.strip()
                           .str.lower()
                           .str.replace(" ", "_")
        )
        return self

    # ── Paso 2 ────────────────────────────────────────────────────────────────

    def detectar_columnas_devengado(self):
        """
        Busca columnas de devengado mensual usando los patrones de config.
        Si no se encuentran 12, completa con columnas numéricas candidatas.
        """
        for col in self.df.columns:
            for patron in PATRONES_DEVENGADO:
                if re.search(patron, col, re.IGNORECASE):
                    if col not in self.columnas_devengado:
                        self.columnas_devengado.append(col)
                    break

        if len(self.columnas_devengado) < 12:
            cols_num = self.df.select_dtypes(include=[np.number]).columns.tolist()
            candidatas = [
                c for c in cols_num
                if not any(e in c for e in PATRONES_EXCLUIR)
                and c not in self.columnas_devengado
            ]
            self.columnas_devengado.extend(candidatas)
            self.columnas_devengado = self.columnas_devengado[:12]

        if not self.columnas_devengado:
            st.error("❌ No se detectaron columnas de devengado mensual.")
            st.stop()

        return self

    # ── Paso 3 ────────────────────────────────────────────────────────────────

    def renombrar_columnas_devengado(self):
        """Renombra las columnas detectadas como Devengado_<Mes>."""
        for i, col in enumerate(self.columnas_devengado[:12]):
            self.df.rename(columns={col: f"Devengado_{MESES[i]}"}, inplace=True)
        self.columnas_devengado = [
            f"Devengado_{m}" for m in MESES[:len(self.columnas_devengado)]
        ]
        return self

    # ── Paso 4 ────────────────────────────────────────────────────────────────

    def detectar_columna_pim(self):
        """Detecta la columna PIM por nombre o por ser la columna numérica más alta."""
        for col in self.df.columns:
            if "pim" in col.lower() or (
                "presupuesto" in col.lower() and "inicial" in col.lower()
            ):
                self.col_pim = col
                break

        if self.col_pim is None:
            cols_num = self.df.select_dtypes(include=[np.number]).columns
            media_dev = self.df[self.columnas_devengado].mean().mean() if self.columnas_devengado else 0
            for col in cols_num:
                if col not in self.columnas_devengado and self.df[col].mean() > media_dev * 1.5:
                    self.col_pim = col
                    break

        if self.col_pim is None:
            st.error("❌ No se pudo detectar la columna PIM.")
            st.stop()

        self.df.rename(columns={self.col_pim: "PIM"}, inplace=True)
        return self

    # ── Paso 5 ────────────────────────────────────────────────────────────────

    def detectar_columna_certificado(self):
        for col in self.df.columns:
            if "certificado" in col.lower():
                self.col_certificado = col
                break
        if self.col_certificado:
            self.df.rename(columns={self.col_certificado: "Certificado"}, inplace=True)
        else:
            self.df["Certificado"] = 0
        return self

    # ── Paso 6 ────────────────────────────────────────────────────────────────

    def detectar_columna_compromiso(self):
        for col in self.df.columns:
            if "compro_anual" in col.lower() or "compromiso" in col.lower():
                self.col_compromiso = col
                break
        if self.col_compromiso:
            self.df.rename(columns={self.col_compromiso: "Compromiso_Anual"}, inplace=True)
        else:
            self.df["Compromiso_Anual"] = 0
        return self

    # ── Paso 7 ────────────────────────────────────────────────────────────────

    def detectar_columna_generica(self):
        for col in self.df.columns:
            if re.search(r"generica?|gen[eé]rica?", col, re.IGNORECASE):
                self.col_generica = col
                break
        if self.col_generica:
            self.df.rename(columns={self.col_generica: "generica"}, inplace=True)
            st.sidebar.success(f"✅ Genérica detectada: `{self.col_generica}`")
        else:
            self.df["generica"] = "General"
            st.sidebar.info("ℹ️ Sin columna genérica — usando 'General'.")
        return self

    # ── Paso 8 ────────────────────────────────────────────────────────────────

    def calcular_metricas(self):
        """Agrega Devengado_Total, Saldo y %_Ejecucion; filtra filas sin PIM."""
        self.df["Devengado_Total"] = self.df[self.columnas_devengado].sum(axis=1)
        self.df["Saldo"]           = self.df["PIM"] - self.df["Devengado_Total"]
        self.df["%_Ejecucion"]     = (
            self.df["Devengado_Total"]
            / self.df["PIM"].replace(0, np.nan) * 100
        ).fillna(0).round(2)

        self.df = self.df[self.df["generica"].notna()]
        self.df = self.df[self.df["PIM"] > 0]
        return self

    # ── Pipeline completo ─────────────────────────────────────────────────────

    def procesar_completo(self):
        return (
            self.normalizar_columnas()
                .detectar_columnas_devengado()
                .renombrar_columnas_devengado()
                .detectar_columna_pim()
                .detectar_columna_certificado()
                .detectar_columna_compromiso()
                .detectar_columna_generica()
                .calcular_metricas()
        )

    # ── Getters ───────────────────────────────────────────────────────────────

    def obtener_dataframe(self) -> pd.DataFrame:
        return self.df

    def obtener_columnas_devengado(self) -> list[str]:
        return self.columnas_devengado
