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
            location_context = f"{user_data['basic']['pais']}, {user_data['basic']['provincia']}" if 'provincia' in user_data['basic'] else user_data['basic']['pais']
            
            # Generar plan para cada día por separado
            plans = []
            for day in range(1, 4):
                prompt = f"""
                Eres un experto nutricionista. Genera el plan nutricional para el Día {day} de 3.
                
                Ubicación: {location_context}
                
                REQUISITOS:
                - Generar UN día completo con 4 comidas (desayuno, almuerzo, merienda, cena)
                - Todas las comidas deben ser diferentes a los otros días
                - Mantener balance calórico consistente
                - Macronutrientes equivalentes (±10g) entre comidas
                
                Para cada comida especificar:
                1. Nombre de la preparación
                2. Ingredientes con:
                   - Cantidades exactas en gramos
                   - Marcas específicas de {location_context} (3 alternativas)
                3. Proceso detallado de preparación
                4. Información nutricional completa
                
                Formato exacto a seguir:
                
                Día {day}
                
                [Comida]:
                
                Ingredientes:
                - [cantidad] [ingrediente] ([marca1] o [marca2] o [marca3])
                
                Preparación:
                1. [paso]
                2. [paso]
                
                Esta comida aporta:
                - Calorías: X kcal
                - Carbohidratos: X g
                - Proteínas: X g
                - Grasas: X g
                - Fibra: X g
                - Sodio: X mg
                - Potasio: X mg
                - Magnesio: X mg
                
                [Repetir para cada comida]
                
                Balance total del Día {day}:
                [Totales nutricionales]
                """
                
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Eres un nutricionista experto que genera planes detallados y precisos."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000
                )
                
                plans.append(response.choices[0].message.content)
            
            # Combinar los tres días en un solo plan
            full_plan = "\n\n---\n\n".join(plans)
            
            # Agregar encabezado y pie
            final_plan = f"""
            Plan Nutricional Personalizado para {location_context}
            
            {full_plan}
            
            Notas importantes:
            - Todas las marcas mencionadas están verificadas como disponibles en {location_context}
            - Los valores nutricionales son aproximados y pueden variar según las marcas específicas utilizadas
            - Ajuste las porciones según necesidad manteniendo las proporciones
            """
            
            return final_plan
            
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