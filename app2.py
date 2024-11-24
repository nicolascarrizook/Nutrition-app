import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import os
import PyPDF2

# Configuración de la página
st.set_page_config(
    page_title="Nutrition AI",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# Obtener API key desde Streamlit Secrets
try:
    openai = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    st.sidebar.success("API Key cargada correctamente")
except Exception as e:
    st.sidebar.error("API Key no encontrada")
    st.error("Por favor configura la API Key en Streamlit Cloud Settings -> Secrets")
    st.stop()

def load_book_context():
    try:
        pdf_path = os.path.join('data', 'libro_nutricion.pdf')
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            # Mostrar progreso de carga del libro
            with st.spinner('Cargando base de conocimientos...'):
                progress_bar = st.progress(0)
                total_pages = len(pdf_reader.pages)
                
                for i, page in enumerate(pdf_reader.pages):
                    text += page.extract_text()
                    progress_bar.progress((i + 1) / total_pages)
                
                progress_bar.empty()
            return text
    except Exception as e:
        st.error(f"Error cargando el PDF: {str(e)}")
        return ""
    
# Título y descripción
st.title("🏋️‍♂️ Nutrition AI")
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
        # Agregar ubicación
        data['pais'] = st.selectbox(
            "País",
            ["Argentina", "España", "México", "Colombia", "Chile", "Perú", "Uruguay"]
        )
        if data['pais'] == "Argentina":
            data['provincia'] = st.selectbox(
                "Provincia",
                ["Buenos Aires", "Córdoba", "Santa Fe", "Mendoza", "Tucumán", "Entre Ríos", "Salta", "Otras"]
            )
    
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
        
        # Preferencias alimentarias
        st.markdown("### 🍽️ Preferencias Alimentarias")
        
        # Alimentos que no consume
        data['no_consume'] = st.multiselect(
            "No consume/Alergias",
            ["Lácteos", "Gluten", "Maní", "Huevos", "Pescado", "Mariscos", 
             "Soja", "Frutos secos", "Cerdo", "Res", "Ninguna restricción"]
        )
        
        # Alimentos preferidos
        data['preferencias'] = st.multiselect(
            "Alimentos preferidos",
            ["Pollo", "Pescado", "Carne roja", "Huevos", "Lácteos", 
             "Legumbres", "Arroz", "Pasta", "Verduras", "Frutas"]
        )
        
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
        with st.spinner('Generando plan nutricional personalizado...'):
            prompt = f"""
            Eres un experto nutricionista que ha estudiado y memorizado completamente el libro que se te proporcionó como base de conocimientos.
            
            Genera un plan nutricional de 3 días para una persona de {user_data['basic']['pais']}
            {f"(provincia de {user_data['basic']['provincia']})" if 'provincia' in user_data['basic'] else ""} 
            con las siguientes características:
            
            DATOS BÁSICOS:
            - Edad: {user_data['basic']['edad']} años
            - Peso: {user_data['basic']['peso']} kg
            - Altura: {user_data['basic']['altura']} cm
            - % Grasa: {user_data['basic']['grasa']}%
            - % Músculo: {user_data['basic']['musculo']}%
            
            ACTIVIDAD FÍSICA:
            - Tipo: {', '.join(user_data['activity']['tipo_actividad'])}
            - Frecuencia: {user_data['activity']['frecuencia']} días/semana
            - Intensidad: {user_data['activity']['intensidad']}
            
            RESTRICCIONES Y PREFERENCIAS:
            - No consume: {', '.join(user_data['basic']['no_consume'])}
            - Alimentos preferidos: {', '.join(user_data['basic']['preferencias'])}
            - Patologías: {', '.join(user_data['basic']['patologia'])}
            - Número de comidas: {user_data['basic']['n_comidas']}
            
            El plan debe:
            1. Seguir los principios y metodologías del libro
            2. Mantener el mismo balance calórico los 3 días
            3. Tener comidas equivalentes en macronutrientes (±10g)
            4. EVITAR COMPLETAMENTE los alimentos listados en "No consume"
            5. PRIORIZAR los alimentos listados en "Alimentos preferidos"
            6. Usar nombres de alimentos y preparaciones comunes en {user_data['basic']['pais']}
            7. Incluir opciones de compra locales cuando sea posible
            
            Formato de respuesta:
            1. Plan detallado día por día
            2. Macronutrientes por comida
            3. Suplementación recomendada según el libro
            4. Lista de compras con nombres locales de los alimentos
            5. Notas y recomendaciones específicas
            """
            
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Has estudiado y memorizado completamente el libro de nutrición proporcionado. Usa ese conocimiento como base para tus recomendaciones."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000
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

if __name__ == "__main__":
    main()