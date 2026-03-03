import streamlit as st
import pandas as pd

st.title("🚀 Mi Tablero de Control")
st.write("Bienvenido a mi aplicación web programada en Python.")

# Un pequeño gráfico de ejemplo
data = pd.DataFrame({
    'Categoría': ['A', 'B', 'C', 'D'],
    'Valores': [10, 45, 30, 70]
})

st.bar_chart(data.set_index('Categoría'))

if st.button('¡Salúdame!'):
    st.balloons()
    st.success("¡Todo funciona correctamente!")
