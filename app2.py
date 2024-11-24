import streamlit as st
import pandas as pd
import numpy as np
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Obtener API key desde variables de entorno
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai = OpenAI(api_key=OPENAI_API_KEY)

# Configuración de la página
st.set_page_config(
    page_title="NutriSport AI",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# Título y descripción
st.title("🏋️‍♂️ Nutricion AI")
st.markdown("### Sistema de Análisis y Recomendación Nutricional")

def collect_basic_data():
    st.markdown("### 📋 Datos Personales")
    
    col1, col2 = st.columns(2)
    data = {}
    
    with col1:
        data['edad'] = st.number_input("Edad", 18, 100)
        data['altura'] = st.number_input("Altura (cm)", 140, 220)
        data['peso'] = st.number_input("Peso (kg)", 40, 200)
        data['grasa'] = st.number_input("Porcentaje de grasa corporal", 0, 50)
        data['musculo'] = st.number_input("Porcentaje de músculo", 0, 100)
    
    with col2:
        data['patologia'] = st.multiselect(
            "Patologías",
            ["Diabetes", "Hipertensión", "Colesterol alto", "Ninguna"]
        )
        data['suplementacion'] = st.multiselect(
            "Suplementación actual",
            ["Proteína", "Creatina", "BCAA", "Ninguna"]
        )
        data['n_comidas'] = st.slider("Número de comidas diarias", 2, 8, 4)
        data['analisis_img'] = st.file_uploader(
            "Subir análisis clínico (opcional)", 
            type=['png', 'jpg', 'jpeg']
        )
    
    return data

def collect_activity_data():
    st.markdown("### 🏋️ Actividad Física")
    data = {}
    
    col1, col2 = st.columns(2)
    with col1:
        data['tipo_actividad'] = st.multiselect(
            "Tipo de actividad",
            ["Musculación", "Cardio", "CrossFit", "Calistenia"]
        )
        data['frecuencia'] = st.number_input("Días por semana", 1, 7)
        data['duracion'] = st.number_input("Duración por sesión (minutos)", 15, 180)
    
    with col2:
        data['intensidad'] = st.select_slider(
            "Intensidad",
            options=["Baja", "Media", "Alta", "Muy alta"]
        )
        data['reloj_data'] = st.file_uploader(
            "Subir datos del reloj inteligente (opcional)", 
            type=['csv', 'json']
        )
    
    return data

def collect_anabolic_data():
    st.markdown("### 💊 Información de Ciclos")
    show_ciclo = st.checkbox("¿Está realizando un ciclo de anabólicos?")
    
    data = {'tiene_ciclo': show_ciclo}
    if show_ciclo:
        data['compuesto'] = st.text_input("Compuesto")
        data['dosificacion'] = st.number_input("Dosificación (mg)", 0, 1000)
        data['duracion'] = st.number_input("Duración del ciclo (semanas)", 1, 52)
    
    return data

def generate_nutrition_plan(user_data):
    try:
        prompt = f"""
        Genera un plan nutricional de 3 días para una persona con las siguientes características:
        - Edad: {user_data['basic']['edad']} años
        - Peso: {user_data['basic']['peso']} kg
        - Altura: {user_data['basic']['altura']} cm
        - % Grasa: {user_data['basic']['grasa']}%
        - % Músculo: {user_data['basic']['musculo']}%
        - Actividad física: {', '.join(user_data['activity']['tipo_actividad'])}
        - Frecuencia: {user_data['activity']['frecuencia']} días/semana
        - Intensidad: {user_data['activity']['intensidad']}
        - Patologías: {', '.join(user_data['basic']['patologia'])}
        - Número de comidas: {user_data['basic']['n_comidas']}
        
        El plan debe:
        1. Mantener el mismo balance calórico los 3 días
        2. Tener comidas equivalentes en macronutrientes (±10g)
        3. Incluir opciones de alimentos reales y procesados permitidos
        4. Especificar marcas recomendadas de suplementos
        5. Indicar ingredientes a evitar en productos procesados
        """
        
        
        response = openai.chat.completions.create( 
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generando el plan: {str(e)}"

def main():
    # Recolección de datos
    tab1, tab2, tab3 = st.tabs(["Datos Personales", "Actividad Física", "Plan Nutricional"])
    
    with tab1:
        basic_data = collect_basic_data()
        anabolic_data = collect_anabolic_data()
    
    with tab2:
        activity_data = collect_activity_data()
    
    with tab3:
        if st.button("Generar Plan Nutricional"):
            user_data = {
                'basic': basic_data,
                'activity': activity_data,
                'anabolic': anabolic_data
            }
            
            with st.spinner('Generando plan personalizado...'):
                plan = generate_nutrition_plan(user_data)
                st.markdown("### 🤖 Plan Nutricional Personalizado")
                st.markdown(plan)
                
                # Botón para descargar el plan
                st.download_button(
                    label="Descargar Plan",
                    data=plan,
                    file_name="plan_nutricional.txt",
                    mime="text/plain"
                )

# Verificación de API key
if OPENAI_API_KEY:
    st.sidebar.success("API Key cargada correctamente")
else:
    st.sidebar.warning("API Key no encontrada en .env")

if __name__ == "__main__":
    main()