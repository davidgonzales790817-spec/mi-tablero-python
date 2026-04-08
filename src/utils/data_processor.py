# utils/data_processor.py
import pandas as pd
import re
import numpy as np
import streamlit as st
from config import MESES, PATRONES_DEVENGADO, PATRONES_EXCLUIR

class DataProcessor:
    def __init__(self, df):
        self.df = df.copy()
        self.columnas_devengado = []
        self.col_pim = None
        self.col_certificado = None
        self.col_compromiso = None
        self.col_generica = None

    def normalizar_columnas(self):
        self.df.columns = self.df.columns.str.strip().str.lower().str.replace(' ', '_')
        return self

    def detectar_columnas_devengado(self):
        for col in self.df.columns:
            for patron in PATRONES_DEVENGADO:
                if re.search(patron, col, re.IGNORECASE):
                    if col not in self.columnas_devengado:
                        self.columnas_devengado.append(col)
                    break

        if len(self.columnas_devengado) < 12:
            cols_numericas = self.df.select_dtypes(include=[np.number]).columns.tolist()
            cols_candidatas = [c for c in cols_numericas if not any(e in c for e in PATRONES_EXCLUIR)]
            self.columnas_devengado = cols_candidatas[:12]

        if len(self.columnas_devengado) == 0:
            st.error("No se pudieron detectar columnas de devengado mensual")
            st.stop()
        return self

    def renombrar_columnas_devengado(self):
        for i, col in enumerate(self.columnas_devengado[:12]):
            self.df.rename(columns={col: f"Devengado_{MESES[i]}"}, inplace=True)
        self.columnas_devengado = [f"Devengado_{mes}" for mes in MESES[:len(self.columnas_devengado)]]
        return self

    def detectar_columna_pim(self):
        for col in self.df.columns:
            if 'pim' in col.lower() or ('presupuesto' in col.lower() and 'inicial' in col.lower()):
                self.col_pim = col
                break

        if self.col_pim is None:
            cols_numericas = self.df.select_dtypes(include=[np.number]).columns
            for col in cols_numericas:
                if col not in self.columnas_devengado:
                    if self.df[col].mean() > self.df[self.columnas_devengado].mean().mean() * 1.5:
                        self.col_pim = col
                        break

        if self.col_pim is None:
            st.error("No se pudo detectar la columna PIM")
            st.stop()

        self.df.rename(columns={self.col_pim: "PIM"}, inplace=True)
        return self

    def detectar_columna_certificado(self):
        for col in self.df.columns:
            if 'certificado' in col.lower():
                self.col_certificado = col
                break

        if self.col_certificado:
            self.df.rename(columns={self.col_certificado: "Certificado"}, inplace=True)
        else:
            self.df["Certificado"] = 0
        return self

    def detectar_columna_compromiso(self):
        for col in self.df.columns:
            if 'compro_anual' in col.lower() or 'compromiso' in col.lower():
                self.col_compromiso = col
                break

        if self.col_compromiso:
            self.df.rename(columns={self.col_compromiso: "Compromiso_Anual"}, inplace=True)
        else:
            self.df["Compromiso_Anual"] = 0
        return self

    def detectar_columna_generica(self):
        for col in self.df.columns:
            if re.search(r'generica?|gen[eé]rica?', col, re.IGNORECASE):
                self.col_generica = col
                break

        if self.col_generica:
            self.df.rename(columns={self.col_generica: "generica"}, inplace=True)
            st.sidebar.success(f"Columna de genérica detectada: '{self.col_generica}'")
        else:
            self.df["generica"] = "General"
            st.sidebar.info("No se encontró columna de genérica. Se usará 'General'.")
        return self

    def calcular_metricas(self):
        self.df["Devengado_Total"] = self.df[self.columnas_devengado].sum(axis=1)
        self.df["Saldo"] = self.df["PIM"] - self.df["Devengado_Total"]
        self.df["%_Ejecucion"] = (self.df["Devengado_Total"] / self.df["PIM"] * 100).round(2)

        self.df = self.df[self.df["generica"].notna()]
        self.df = self.df[self.df["PIM"] > 0]
        return self

    def procesar_completo(self):
        return (self.normalizar_columnas()
                .detectar_columnas_devengado()
                .renombrar_columnas_devengado()
                .detectar_columna_pim()
                .detectar_columna_certificado()
                .detectar_columna_compromiso()
                .detectar_columna_generica()
                .calcular_metricas())

    def obtener_dataframe(self):
        return self.df

    def obtener_columnas_devengado(self):
        return self.columnas_devengado
