import streamlit as st
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

# Obtener API key desde variables de entorno
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configuración de la página
st.set_page_config(
    page_title="ML Data Analyzer",
    page_icon="🤖",
    layout="wide"
)

# Título y descripción
st.title("🤖 Análisis de Datos con ML")
st.markdown("### Analiza tus datos con Machine Learning")

# Función para análisis exploratorio
def analisis_exploratorio(df):
    st.markdown("### 📊 Análisis Exploratorio de Datos")
    
    # Información básica
    st.write("Dimensiones del dataset:", df.shape)
    
    # Tipos de datos
    st.write("Tipos de datos:")
    st.write(df.dtypes)
    
    # Estadísticas descriptivas
    st.write("Estadísticas descriptivas:")
    st.write(df.describe())
    
    # Valores nulos
    st.write("Valores nulos por columna:")
    st.write(df.isnull().sum())
    
    # Visualización básica para columnas numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        st.write("Visualización de columnas numéricas:")
        for col in numeric_cols:
            st.line_chart(df[col])

# Subida de archivo
uploaded_file = st.file_uploader("Sube tu archivo CSV", type=['csv'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("¡Archivo cargado exitosamente!")
        
        st.markdown("### 📋 Vista Previa de Datos")
        st.write("Primeras filas del dataset:")
        st.write(df.head())
        
        analisis_exploratorio(df)
        
        # Selección de variables
        st.markdown("### 🎯 Selección de Variables")
        target_column = st.selectbox(
            "Selecciona la columna objetivo",
            df.columns
        )
        
        feature_columns = st.multiselect(
            "Selecciona las columnas para el análisis",
            [col for col in df.columns if col != target_column],
            default=[col for col in df.columns if col != target_column][:3]
        )
        
        if st.button("Generar Visualizaciones"):
            st.markdown("### 📊 Visualizaciones")
            
            # Visualizaciones básicas
            if df[target_column].dtype in ['int64', 'float64']:
                st.write(f"Distribución de {target_column}")
                st.bar_chart(df[target_column])
            
            # Visualizaciones para features seleccionadas
            for feature in feature_columns:
                if df[feature].dtype in ['int64', 'float64']:
                    st.write(f"Análisis de {feature}")
                    st.line_chart(df[feature])
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")

# Verificación de API key (opcional)
if OPENAI_API_KEY:
    st.sidebar.success("API Key cargada correctamente")
else:
    st.sidebar.warning("API Key no encontrada en .env")