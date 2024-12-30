import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import os
import PyPDF2
import io
from vector_db import VectorDBManager
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import re
import time
import random

# Constantes y configuraciones
MEAL_TYPES = {
    "Desayuno": {"start_time": "07:00", "end_time": "09:00"},
    "Almuerzo": {"start_time": "12:00", "end_time": "14:00"},
    "Merienda": {"start_time": "16:00", "end_time": "17:30"},
    "Cena": {"start_time": "20:00", "end_time": "21:30"}
}

ACTIVITY_LEVELS = {
    "Baja": 1.2,
    "Media": 1.375,
    "Alta": 1.55,
    "Muy alta": 1.725
}

# Constantes globales
MAX_ATTEMPTS = 3  # Número máximo de intentos para generar el plan
TEMPERATURE_REDUCTION = 0.1  # Reducción de temperatura por intento

# Diccionario de valores nutricionales estandarizados
STANDARD_NUTRIENTS = {
    'huevo': {'calories': 110, 'protein': 9, 'carbs': 0, 'fat': 7.5},  # por unidad
    'pan_integral': {'calories': 250, 'protein': 10, 'carbs': 43, 'fat': 4},  # por 100g
    'palta': {'calories': 144, 'protein': 2, 'carbs': 8, 'fat': 13},  # por 90g
    'pollo': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.5},  # por 100g
    'pescado': {'calories': 206, 'protein': 22, 'carbs': 0, 'fat': 12.7},  # por 100g
    'arroz': {'calories': 130, 'protein': 2.5, 'carbs': 28, 'fat': 0.3},  # por 100g
    'pasta': {'calories': 130, 'protein': 4, 'carbs': 28, 'fat': 0.7},  # por 100g
    'leche': {'calories': 100, 'protein': 3.4, 'carbs': 4.7, 'fat': 3.2},  # por 250ml
    'yogur': {'calories': 100, 'protein': 3.8, 'carbs': 4, 'fat': 0.1},  # por 100g
    'queso': {'calories': 380, 'protein': 29, 'carbs': 0, 'fat': 28},  # por 100g
    'aceite': {'calories': 884, 'protein': 0, 'carbs': 0, 'fat': 100},  # por 100g
    'azucar': {'calories': 387, 'protein': 0, 'carbs': 100, 'fat': 0},  # por 100g
    'sal': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0},  # por 100g
}

# Cachear la inicialización de servicios
@st.cache_resource
def init_services():
    try:
        load_dotenv()  # Cargar variables de entorno
        openai = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        db_manager = VectorDBManager()
        return openai, db_manager
    except Exception as e:
        st.sidebar.error(f"Error en la inicialización: {str(e)}")
        st.error("Por favor configura las API Keys en Streamlit Cloud Settings -> Secrets")
        raise e

# Configuración de la página
st.set_page_config(
    page_title="Nutrition AI",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# Inicializar servicios una sola vez
try:
    openai, db_manager = init_services()
    st.sidebar.success("API Key y Base de Conocimientos cargadas correctamente")
except Exception as e:
    st.stop()

def load_book_context():
    try:
        pdf_path = os.path.join('data', 'libro_nutricion.pdf')
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
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
        
        data['pais'] = st.selectbox(
            "País",
            ["Argentina", "España", "México", "Colombia", "Chile", "Perú", "Uruguay"]
        )
        if data['pais'] == "Argentina":
            data['provincia'] = st.selectbox(
                "Provincia",
                ["Buenos Aires", "Córdoba", "Santa Fe", "Mendoza", "Tucumán", "Entre Ríos", "Salta", "Otras"]
            )
        
        data['objetivo_principal'] = st.selectbox(
            "Objetivo Principal",
            ["Pérdida de grasa", "Ganancia muscular", "Mantenimiento", 
             "Rendimiento deportivo", "Salud general"]
        )
        
        data['objetivos_secundarios'] = st.multiselect(
            "Objetivos Secundarios",
            ["Mejorar energía", "Mejorar recuperación", "Definición muscular",
             "Aumentar fuerza", "Mejorar digestión", "Reducir inflamación",
             "Optimizar hormonas", "Mejorar calidad del sueño"]
        )
        
        data['tiempo_objetivo'] = st.number_input(
            "Tiempo para alcanzar objetivo (semanas)", 
            1, 52, 12
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
        
        data['no_consume'] = st.multiselect(
            "No consume/Alergias",
            ["Lácteos", "Gluten", "Maní", "Huevos", "Pescado", "Mariscos", 
             "Soja", "Frutos secos", "Cerdo", "Res", "Ninguna restricción"]
        )
        
        data['preferencias'] = st.multiselect(
            "Alimentos preferidos",
            ["Pollo", "Pescado", "Carne roja", "Huevos", "Lácteos", 
             "Legumbres", "Arroz", "Pasta", "Verduras", "Frutas"]
        )
        
        st.markdown("### 🍽️ Estructura de Comidas")
        data['comidas_principales'] = st.multiselect(
            "Comidas principales",
            ["Desayuno", "Almuerzo", "Merienda", "Cena"],
            default=["Desayuno", "Almuerzo", "Merienda", "Cena"]
        )
        
        data['incluir_colaciones'] = st.checkbox("Incluir colaciones")
        if data['incluir_colaciones']:
            data['tipo_colaciones_regulares'] = st.selectbox(
                "Tipo de colaciones entre comidas",
                ["Dulces", "Saladas", "Ambas"]
            )
            data['n_colaciones_regulares'] = st.number_input(
                "Número de colaciones entre comidas", 0, 4, 2
            )
            
            data['colaciones_deportivas'] = st.multiselect(
                "Colaciones relacionadas al entrenamiento",
                ["Pre-entreno", "Intra-entreno", "Post-entreno"]
            )
            
        # Objetivos específicos de macros
        data['objetivo_proteina'] = st.selectbox(
            "Objetivo de proteína",
            ["Bajas (0.8g/kg)", "Normales (1.6g/kg)", "Altas (2.2g/kg)", 
             "Muy altas (2.8g/kg)", "Adecuadas anabólicos (3.0g/kg)"]
        )
        
        data['porcentaje_carbos'] = st.select_slider(
            "Porcentaje de carbohidratos",
            options=['30%', '40%', '50%', '60%']
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
    
    return data

def collect_anabolic_data():
    """Recolecta datos específicos sobre uso de anabólicos"""
    data = {}
    if st.checkbox("¿Usa anabólicos?"):
        data['usa_anabolicos'] = True
        data['tipo_anabolicos'] = st.multiselect(
            "Tipo de anabólicos",
            ["Testosterona", "Trembolona", "Deca", "Otros"]
        )
        data['tiempo_uso'] = st.number_input(
            "Tiempo de uso (semanas)", 
            1, 52
        )
    else:
        data['usa_anabolicos'] = False
    return data

def calculate_energy_needs(user_data: Dict[str, Any]) -> Dict[str, float]:
    """Calcula las necesidades energéticas con mayor precisión"""
    try:
        peso = user_data['basic']['peso']
        altura = user_data['basic']['altura']
        edad = user_data['basic']['edad']
        actividad = user_data['activity']['intensidad']
        
        # Fórmula Harris-Benedict revisada
        bmr = 447.593 + (9.247 * peso) + (3.098 * altura) - (4.330 * edad)
        
        # Ajuste por nivel de actividad
        tdee = bmr * ACTIVITY_LEVELS.get(actividad, 1.2)
        
        # Ajuste por objetivo
        objetivo = user_data['basic']['objetivo_principal']
        if objetivo == "Pérdida de grasa":
            tdee *= 0.85
        elif objetivo == "Ganancia muscular":
            tdee *= 1.15
            
        return {
            'bmr': bmr,
            'tdee': tdee,
            'protein_need': peso * float(user_data['basic']['objetivo_proteina'].split('(')[1].split('g')[0]),
            'carb_need': (tdee * float(user_data['basic']['porcentaje_carbos'].strip('%')) / 100) / 4,
            'fat_need': (tdee * 0.25) / 9
        }
    except Exception as e:
        st.error(f"Error al calcular necesidades energéticas: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_cached_nutrition_data(query: str) -> str:
    """Caché para consultas frecuentes a la base vectorial"""
    db_manager = VectorDBManager()
    return db_manager.query_book_context(query=query, n_results=3)

def get_nutrition_context(user_data: Dict[str, Any], db_manager: VectorDBManager) -> str:
    """Obtiene contexto nutricional relevante de la base de datos vectorial"""
    try:
        st.write("🔍 Consultando base de datos de conocimiento nutricional...")
        
        # Construir queries específicas basadas en los datos del usuario
        queries = {
            "objetivo": f"método tres días y carga para {user_data['basic']['objetivo_principal']}",
            "nutricion": f"nutrición para {user_data['basic']['objetivo_principal']}",
            "suplementacion": "suplementación" if "Creatina" in user_data['basic'].get('suplementacion', []) 
                            else "nutrición sin suplementos"
        }

        contexts = {}
        for topic, query in queries.items():
            st.write(f"🔎 Buscando información sobre: {topic}")
            
            # Usar el método search_knowledge para obtener resultados
            results = db_manager.search_knowledge(
                query=query,
                top_k=3,
                threshold=0.5
            )
            
            if results:
                st.write(f"✅ Encontrados {len(results)} resultados para {topic}")
                # Extraer y formatear los resultados
                context = "\n".join([f"• {r['text']}" for r in results])
                contexts[topic] = context
            else:
                st.write(f"⚠️ No se encontró información para {topic}")

        # También podemos usar query_book_context para consultas más específicas
        specific_query = f"""
        plan nutricional {user_data['basic']['objetivo_principal']} 
        con {user_data['activity']['intensidad']} intensidad
        """
        book_context = db_manager.query_book_context(specific_query, n_results=3)
        
        if book_context:
            contexts['específico'] = book_context
            st.write("✅ Encontrado contexto específico del libro")

        # Combinar todos los contextos
        combined_context = "\n\n".join([
            f"### {topic.title()}\n{context}" 
            for topic, context in contexts.items()
        ])

        if not combined_context.strip():
            st.warning("⚠️ No se encontró información específica en la base de datos")
            return "No se encontró información específica en la base de datos."

        st.success("✅ Contexto nutricional generado exitosamente")
        return combined_context

    except Exception as e:
        st.error(f"❌ Error al consultar la base de datos: {str(e)}")
        return "Error al obtener contexto nutricional."

def generate_pdf(plan_text: str, user_data: Dict[str, Any], energy_needs: Dict[str, float]) -> bytes:
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para tablas
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])

        # Título
        elements.append(Paragraph("Plan Nutricional Personalizado", styles['Title']))
        elements.append(Spacer(1, 20))
        
        # Información del paciente
        patient_data = [
            ['Datos Personales', 'Valores'],
            ['Edad', f"{user_data['basic']['edad']} años"],
            ['Peso Actual', f"{user_data['basic']['peso']} kg"],
            ['Altura', f"{user_data['basic']['altura']} cm"],
            ['Objetivo', user_data['basic']['objetivo_principal']]
        ]
        
        patient_table = Table(patient_data)
        patient_table.setStyle(table_style)
        elements.append(patient_table)
        elements.append(Spacer(1, 20))
        
        # Tabla de macros
        macro_data = [
            ['Macronutrientes', 'Objetivo Diario'],
            ['Calorías', f"{int(energy_needs['tdee'])} kcal"],
            ['Proteínas', f"{int(energy_needs['protein_need'])}g"],
            ['Carbohidratos', f"{int(energy_needs['carb_need'])}g"],
            ['Grasas', f"{int(energy_needs['fat_need'])}g"]
        ]
        
        macro_table = Table(macro_data)
        macro_table.setStyle(table_style)
        elements.append(macro_table)
        elements.append(Spacer(1, 20))
        
        # Plan detallado
        elements.append(Paragraph("Plan Detallado", styles['Heading1']))
        elements.append(Spacer(1, 10))
        
        # Convertir el plan de texto a formato de tabla
        plan_lines = plan_text.split('\n')
        current_day = None
        plan_data = [['Comida', 'Día 1', 'Día 2', 'Día 3']]
        
        for comida in user_data['basic']['comidas_principales']:
            plan_data.append([comida, '', '', ''])
            
        if user_data['basic'].get('incluir_colaciones'):
            plan_data.append(['Colaciones', '', '', ''])
            if 'colaciones_deportivas' in user_data['basic']:
                for colacion in user_data['basic']['colaciones_deportivas']:
                    plan_data.append([colacion, '', '', ''])
        
        plan_table = Table(plan_data, colWidths=[100, 160, 160, 160])
        plan_table.setStyle(table_style)
        elements.append(plan_table)
        
        # 5. Notas y recomendaciones
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Notas y Recomendaciones:", styles['Heading2']))
        elements.append(Paragraph("• Mantener una buena hidratación (2-3L de agua al día)", styles['Normal']))
        elements.append(Paragraph("• Respetar los horarios de las comidas", styles['Normal']))
        elements.append(Paragraph("• Ajustar las porciones según tolerancia individual", styles['Normal']))
        
        doc.build(elements)
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error al generar el PDF: {str(e)}")
        raise e

def error_handler(func):
    """Decorador para manejar errores de manera consistente"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"Error en {func.__name__}: {str(e)}")
            st.error("Por favor, verifica los datos ingresados e intenta nuevamente.")
            return None
    return wrapper

def validate_supplements_in_plan(plan_text: str, user_supplements: List[str]) -> bool:
    """Valida que solo se incluyan los suplementos seleccionados"""
    # Lista de suplementos comunes y sus variantes
    supplement_variants = {
        "Proteína": ["proteína en polvo", "batido de proteínas", "whey protein", "proteína whey"],
        "Creatina": ["creatina", "creatina monohidrato", "monohidrato de creatina"],
        "BCAA": ["bcaa", "aminoácidos ramificados", "aminoacidos ramificados"]
    }
    
    # Convertir el plan a minúsculas para la búsqueda
    plan_lower = plan_text.lower()
    
    # Verificar que no haya suplementos no seleccionados
    for supp, variants in supplement_variants.items():
        if supp not in user_supplements:
            for variant in variants:
                if variant in plan_lower:
                    st.warning(f"El plan incluye {supp} que no fue seleccionado")
                    return False
    
    return True

def get_supplement_protocol(supplements: List[str]) -> str:
    """Genera el protocolo de suplementación basado en los suplementos seleccionados"""
    if not supplements or "Ninguna" in supplements:
        return "### Suplementación\nNo se han seleccionado suplementos para este plan."
    
    protocols = {
        "Creatina": """
        ### Suplementación con Creatina
        **Fase de carga (7 días):**
        - 8.7gr, 4 veces al día
        - Tomar con 150ml de jugo de frutas (la fructosa y vitamina C mejoran absorción)
        - Momento: pre desayuno
        
        **Fase de mantenimiento:**
        - 8.7gr diarios
        - Tomar pre desayuno
        - Mantener ingesta de líquidos alta
        """,
        "Proteína": """
        ### Suplementación con Proteína
        - Dosis: 30g por toma
        - Timing: post-entrenamiento o entre comidas
        - Mantener hidratación adecuada
        """,
        "BCAA": """
        ### Suplementación con BCAA
        - Dosis: 5-10g por toma
        - Timing: durante el entrenamiento
        - Especialmente útil en entrenamientos en ayunas
        """
    }
    
    supplement_text = ""
    for supplement in supplements:
        if supplement in protocols:
            supplement_text += protocols[supplement] + "\n\n"
    
    return supplement_text.strip()

def get_supplement_protocols(user_weight: float) -> Dict[str, str]:
    """Genera protocolos de suplementación personalizados según el peso corporal"""
    return {
        "Proteína": f"""
        - Proteína en polvo: 
          * {round(user_weight * 0.3)}g post-entrenamiento
          * {round(user_weight * 0.3)}g entre comidas cuando sea necesario
          * Preferentemente whey protein o mezcla de proteínas
        """,
        "Creatina": f"""
        - Creatina Monohidrato:
          * {round(user_weight * 0.07)}g diarios
          * Tomar con comidas que contengan carbohidratos
          * Fase de carga (opcional): {round(user_weight * 0.2)}g/día por 5-7 días
          * Mantener hidratación alta (3L agua/día)
        """,
        "BCAA": f"""
        - BCAA (Aminoácidos Ramificados):
          * {round(user_weight * 0.1)}g durante el entrenamiento
          * {round(user_weight * 0.05)}g en ayunas (opcional)
          * Ratio 2:1:1 (Leucina:Isoleucina:Valina)
          * Especialmente útil en días de entrenamiento intenso
        """
    }

def validate_meal_nutrients(meal_text: str) -> bool:
    """Valida que los nutrientes de cada comida sean consistentes"""
    try:
        # Extraer alimentos individuales y sus valores
        foods = re.findall(r'-\s+.*?\[(\d+)\s*kcal\s*\|\s*P:\s*(\d+)g\s*\|\s*C:\s*(\d+)g\s*\|\s*G:\s*(\d+)g\]', meal_text)
        
        # Extraer totales reportados
        total_match = re.search(r'Total comida:\s*(\d+)\s*kcal\s*\|\s*Proteína:\s*(\d+)g\s*\|\s*Carbos:\s*(\d+)g\s*\|\s*Grasas:\s*(\d+)g', meal_text)
        
        if not foods or not total_match:
            return False
            
        # Calcular sumas
        sums = {
            'calories': sum(int(f[0]) for f in foods),
            'protein': sum(int(f[1]) for f in foods),
            'carbs': sum(int(f[2]) for f in foods),
            'fat': sum(int(f[3]) for f in foods)
        }
        
        # Comparar con totales reportados
        reported = {
            'calories': int(total_match.group(1)),
            'protein': int(total_match.group(2)),
            'carbs': int(total_match.group(3)),
            'fat': int(total_match.group(4))
        }
        
        # Permitir un margen de error de ±2 unidades
        tolerance = 2
        for key in sums:
            if abs(sums[key] - reported[key]) > tolerance:
                st.warning(f"Discrepancia en {key}: suma={sums[key]}, reportado={reported[key]}")
                return False
                
        return True
        
    except Exception as e:
        st.error(f"Error al validar nutrientes de comida: {str(e)}")
        return False

def validate_daily_macros(day_text: str) -> bool:
    """Valida que los macronutrientes del día estén en rangos aceptables"""
    try:
        # Extraer totales del día
        totals = re.search(r'Total calorías:\s*(\d+)\s*kcal.*?Total proteína:\s*(\d+)g.*?Total carbohidratos:\s*(\d+)g.*?Total grasas:\s*(\d+)g', day_text, re.DOTALL)
        
        if not totals:
            return False
            
        calories = int(totals.group(1))
        protein = int(totals.group(2))
        carbs = int(totals.group(3))
        fat = int(totals.group(4))
        
        # Validar rangos
        if not (2200 <= calories <= 2500):
            st.warning(f"Calorías fuera de rango: {calories}")
            return False
            
        if not (180 <= protein <= 210):
            st.warning(f"Proteína fuera de rango: {protein}g")
            return False
            
        if not (200 <= carbs <= 250):
            st.warning(f"Carbohidratos fuera de rango: {carbs}g")
            return False
            
        if not (70 <= fat <= 95):
            st.warning(f"Grasas fuera de rango: {fat}g")
            return False
            
        return True
        
    except Exception as e:
        st.error(f"Error al validar macros del día: {str(e)}")
        return False

@error_handler
def generate_nutrition_plan(user_data: Dict[str, Any]) -> Optional[tuple[str, bytes]]:
    try:
        # Inicializar servicios
        openai, db_manager = init_services()
        
        # Calcular necesidades energéticas
        energy_needs = calculate_energy_needs(user_data)
        if not energy_needs:
            return None
        
        # Obtener contexto nutricional enriquecido
        nutrition_context = get_nutrition_context(user_data, db_manager)
        
        # Obtener suplementos seleccionados 
        supplements = user_data['basic'].get('suplementacion', [])

        # Preparar información del paciente
        info_paciente = f"""
        DATOS DEL PACIENTE:
        ==================
        Información Personal:
        - Edad: {user_data['basic']['edad']} años
        - Peso actual: {user_data['basic']['peso']} kg
        - Altura: {user_data['basic']['altura']} cm
        - % Grasa corporal: {user_data['basic']['grasa']}%
        - % Músculo: {user_data['basic']['musculo']}%
        
        Objetivos:
        - Principal: {user_data['basic']['objetivo_principal']}
        - Tiempo objetivo: {user_data['basic']['tiempo_objetivo']} semanas
        
        Actividad Física:
        - Tipo: {', '.join(user_data['activity']['tipo_actividad'])}
        - Frecuencia: {user_data['activity']['frecuencia']} días/semana
        - Intensidad: {user_data['activity']['intensidad']}
        
        Necesidades Energéticas:
        - BMR: {int(energy_needs['bmr'])} kcal
        - TDEE: {int(energy_needs['tdee'])} kcal
        - Proteína objetivo: {int(energy_needs['protein_need'])}g
        - Carbohidratos objetivo: {int(energy_needs['carb_need'])}g
        - Grasas objetivo: {int(energy_needs['fat_need'])}g
        """
        
        # Preparar información de suplementación solo si existe y no es "Ninguna"
        supp_info = ""
        has_supplements = (
            'suplementacion' in user_data['basic'] and 
            user_data['basic']['suplementacion'] and 
            'Ninguna' not in user_data['basic']['suplementacion']
        )
        
        if has_supplements:
            supp_info = """
            PROTOCOLO DE SUPLEMENTACIÓN:
            ==========================
            """
            # Obtener protocolos personalizados según el peso
            supp_protocols = get_supplement_protocols(float(user_data['basic']['peso']))
            
            for supp in user_data['basic']['suplementacion']:
                if supp in supp_protocols:
                    supp_info += supp_protocols[supp]
        
        # Construir lista de suplementos permitidos
        supplements = user_data['basic'].get('suplementacion', [])
        supplements_str = ", ".join(supplements) if supplements else "ningún suplemento"
        
        # Mensaje específico sobre suplementos
        supplements_instruction = f"""
        INSTRUCCIONES CRÍTICAS SOBRE SUPLEMENTACIÓN:
        =========================================
        - SOLO usar los siguientes suplementos: {supplements_str}
        - NO incluir batidos de proteína ni proteína en polvo
        - NO agregar ningún otro suplemento no especificado
        - Las proteínas deben venir de fuentes alimenticias naturales
        
        Si el usuario no seleccionó proteína en polvo, NO INCLUIR:
        - Batidos de proteína
        - Proteína en polvo
        - Whey protein
        - Suplementos proteicos
        """
        
        # Agregar tablas de equivalencias y notas importantes
        equivalence_tables = """
        ## TABLAS DE EQUIVALENCIAS
        
        ### Equivalencias Proteicas
        | Alimento | Cantidad | Kcal aprox. |
        |----------|----------|-------------|
        | Carne | 100gr | 155 |
        | Legumbre | 70gr | 158 |
        | Queso | 60gr | 166 |
        | Huevo | 2 unidades (80gr) | 156 |
        | Claras | 10 unidades (200gr) | 170 |
        | Jamón crudo/cocido | 100gr | 160 |
        
        ### Equivalencias de Grasas Saludables
        | Alimento | Cantidad | Gramos de Grasas Buenas |
        |----------|----------|------------------------|
        | Palta | 90gr (media) | 5.4 |
        | Aceite de oliva/coco | 1 cda de té | 5.5 |
        | Aceitunas | 13 unidades sin carozo | 5.4 |
        
        ### Equivalencias de Carbohidratos
        | Alimento | Cantidad | Gramos de Carbos |
        |----------|----------|------------------|
        | Banana | 100gr | 22.2 |
        | Frutilla | 280gr | 22.4 |
        | Manzana sin cáscara | 190gr | 22.8 |
        | Avena | 40gr | 22 |
        | Pan integral | 50gr | 19 |
        """
        
        notas_importantes = """
        ## NOTAS IMPORTANTES
        
        ### Flexibilidad del Plan
        - Las comidas son intercambiables dentro del mismo día, manteniendo las porciones indicadas
        - Puedes reemplazar alimentos usando la tabla de equivalencias
        - Respeta las cantidades/porciones especificadas
        
        ### Hidratación
        - Mantén una ingesta de agua adecuada (mínimo 2-3 litros diarios)
        - Aumenta la ingesta durante el ejercicio
        
        ### Suplementación con Creatina
        {}
        
        ### Reemplazos Proteicos
        - 160gr de carne = 115gr de legumbres (menor aporte proteico)
        - 160gr de carne = 2 huevos + 50gr de queso (mantiene aporte proteico)
        
        ### Ciclos de Carga
        - Después del ciclo de 3 días, realizar carga de carbohidratos
        - Fuentes: papa, batata, cereales integrales, frutas, miel
        - Retomar el plan normal al día siguiente
        """.format(
            get_creatine_protocol(user_data['basic'].get('suplementacion', []))
        )
        
        # Ajustar el prompt para mantener un orden consistente
        prompt = f"""
        CONTEXTO ESPECIALIZADO:
        ======================
        {nutrition_context}
        
        {info_paciente}
        
        {supplements_instruction}
        
        PLAN NUTRICIONAL REQUERIDO:
        =========================
        1. Utiliza la información del contexto especializado para personalizar el plan
        2. Generar plan para 3 días
        3. Incluir {len(user_data['basic']['comidas_principales'])} comidas principales: {', '.join(user_data['basic']['comidas_principales'])}
        4. {f"Agregar {user_data['basic'].get('n_colaciones_regulares', 0)} colaciones de tipo {user_data['basic'].get('tipo_colaciones_regulares', '')}" if user_data['basic'].get('incluir_colaciones') else "Sin colaciones"}
        5. Las proteínas deben venir de fuentes naturales como carnes, huevos, pescado, legumbres

        FORMATO EXACTO para cada día:
        ### DÍA [número]

        [Comidas con formato exacto como en el ejemplo]

        **TOTALES DEL DÍA**
        Total calorías: X kcal
        Total proteína: Xg
        Total carbohidratos: Xg
        Total grasas: Xg

        **SUPLEMENTACIÓN DEL DÍA**
        {supp_info if has_supplements else "No se requiere suplementación para este plan."}

        ---

        FORMATO EXACTO para cada comida:
        **[Nombre Comida]: "[Nombre Creativo]"** _([Horario])_
        - [alimento] ([cantidad]g) _[X kcal | P: Xg | C: Xg | G: Xg]_
        - [siguiente alimento] ([cantidad]g) _[X kcal | P: Xg | C: Xg | G: Xg]_
        **Total comida: X kcal | Proteína: Xg | Carbos: Xg | Grasas: Xg**

        Orden específico de comidas:
        1. Desayuno (7:00 - 8:00)
        2. Colación Dulce 1 (10:00 - 10:30)
        3. Almuerzo (12:00 - 13:00)
        4. Merienda (16:00 - 17:00)
        5. Colación Dulce 2 (18:00 - 18:30)
        6. Cena (20:00 - 21:00)

        Al final de cada día incluir:
        **TOTALES DEL DÍA**
        Total calorías: X kcal
        Total proteína: Xg
        Total carbohidratos: Xg
        Total grasas: Xg

        Objetivos diarios a cumplir:
        - Calorías: {int(energy_needs['tdee'])} kcal
        - Proteína: {int(energy_needs['protein_need'])}g
        - Carbohidratos: {int(energy_needs['carb_need'])}g
        - Grasas: {int(energy_needs['fat_need'])}g
        
        RESTRICCIONES:
        ============
        - Solo usar: {', '.join(user_data['basic']['preferencias'])}
        - Evitar: {', '.join(user_data['basic']['no_consume'])}
        - NO incluir suplementos de proteína en ninguna forma
        - Mantener consistencia en nombres (usar "palta" en lugar de "aguacate")
        - TODOS los alimentos deben incluir sus macros entre corchetes
        - Especificar preparación sugerida para cada alimento
        - Para verduras, dar ejemplos específicos con cantidades
        """
        
        # Agregar al prompt
        prompt += f"\n\nINCLUIR AL FINAL DEL PLAN:\n{equivalence_tables}\n{notas_importantes}"
        
        # Validar el plan generado
        attempt = 0
        plan_valid = False
        
        while not plan_valid and attempt < MAX_ATTEMPTS:
            current_temperature = 0.3 - (attempt * TEMPERATURE_REDUCTION)
            
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": """Eres un nutricionista experto que sigue las instrucciones AL PIE DE LA LETRA. 
                        NUNCA incluyas suplementos que no hayan sido específicamente autorizados.
                        Si no se menciona proteína en polvo, NO la incluyas en el plan bajo ninguna circunstancia."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=current_temperature,
                max_tokens=4000
            )
            
            plan_text = response.choices[0].message.content
            
            # Validar macros y suplementos
            macros_valid = validate_nutrition_plan(plan_text, energy_needs)
            supplements_valid = validate_supplements_in_plan(
                plan_text, 
                user_data['basic'].get('suplementacion', [])
            )
            
            if macros_valid and supplements_valid:
                plan_valid = True
            else:
                attempt += 1
                if attempt < MAX_ATTEMPTS:
                    st.warning(f"Reintentando generación del plan (intento {attempt + 1})")
        
        if not plan_valid:
            st.warning("No se pudo generar un plan que cumpla exactamente con los requisitos")
            
        # Generar PDF
        pdf_bytes = generate_pdf(plan_text, user_data, energy_needs)
        
        return plan_text, pdf_bytes
        
    except Exception as e:
        st.error(f"Error al generar el plan: {str(e)}")
        return None

def extract_meals_from_plan(plan_text: str, day: int) -> List[Dict]:
    """Extrae la información de comidas para un día específico"""
    try:
        # Encontrar la sección del día
        day_pattern = f"### Día {day}(.*?)(?=### Día {day+1}|### Consideraciones Finales|$)"
        day_match = re.search(day_pattern, plan_text, re.DOTALL)
        if not day_match:
            return []
        
        day_content = day_match.group(1)
        
        # Extraer cada comida
        meals = []
        meal_pattern = r"\*\*(.*?)\**\n((?:- .*?\n)*)"
        for meal_match in re.finditer(meal_pattern, day_content):
            meal_name = meal_match.group(1)
            items = meal_match.group(2)
            
            # Extraer macros de cada ítem
            total_macros = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
            item_pattern = r"- (.*?)\((\d+) kcal,\s*(\d+)g proteína,\s*(\d+)g carbohidratos,\s*(\d+)g grasa\)"
            
            for item in re.finditer(item_pattern, items):
                total_macros['calories'] += int(item.group(2))
                total_macros['protein'] += int(item.group(3))
                total_macros['carbs'] += int(item.group(4))
                total_macros['fat'] += int(item.group(5))
            
            meals.append({
                'name': meal_name,
                'macros': total_macros
            })
        
        return meals
    except Exception as e:
        st.warning(f"Error al extraer comidas del día {day}: {str(e)}")
        return []

def calculate_daily_totals(meals_data: List[Dict]) -> Dict[str, float]:
    """Calcula los totales diarios de macros y calorías"""
    totals = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0
    }
    
    for meal in meals_data:
        for macro, value in meal['macros'].items():
            totals[macro] += value
    
    return totals

def calculate_averages(daily_totals: List[Dict[str, float]]) -> Dict[str, float]:
    """Calcula los promedios de macros y calorías"""
    if not daily_totals:
        return {}
    
    averages = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0
    }
    
    for macro in averages.keys():
        averages[macro] = sum(day[macro] for day in daily_totals) / len(daily_totals)
    
    return averages

def get_supplement_protocol(supplements: List[str]) -> str:
    """Genera el protocolo de suplementación basado en los suplementos seleccionados"""
    if not supplements or "Ninguna" in supplements:
        return "### Suplementación\nNo se han seleccionado suplementos para este plan."
    
    protocols = {
        "Creatina": """
        ### Suplementación con Creatina
        **Fase de carga (7 días):**
        - 8.7gr, 4 veces al día
        - Tomar con 150ml de jugo de frutas (la fructosa y vitamina C mejoran absorción)
        - Momento: pre desayuno
        
        **Fase de mantenimiento:**
        - 8.7gr diarios
        - Tomar pre desayuno
        - Mantener ingesta de líquidos alta
        """,
        "Proteína": """
        ### Suplementación con Proteína
        - Dosis: 30g por toma
        - Timing: post-entrenamiento o entre comidas
        - Mantener hidratación adecuada
        """,
        "BCAA": """
        ### Suplementación con BCAA
        - Dosis: 5-10g por toma
        - Timing: durante el entrenamiento
        - Especialmente útil en entrenamientos en ayunas
        """
    }
    
    supplement_text = ""
    for supplement in supplements:
        if supplement in protocols:
            supplement_text += protocols[supplement] + "\n\n"
    
    return supplement_text.strip()

def validate_macros(averages: Dict[str, float], targets: Dict[str, float], tolerance: float = 0.10) -> bool:
    """Valida que los macros estén dentro del rango aceptable"""
    try:
        for macro, target in targets.items():
            if macro in averages:
                actual = averages[macro]
                lower_bound = target * (1 - tolerance)
                upper_bound = target * (1 + tolerance)
                
                if not (lower_bound <= actual <= upper_bound):
                    st.warning(f"Macro {macro} fuera de rango: {actual:.1f}g (objetivo: {target:.1f}g ±{tolerance*100}%)")
                    return False
        return True
    except Exception as e:
        st.warning(f"Error al validar macros: {str(e)}")
        return False

def validate_nutrition_plan(plan_text: str, energy_needs: Dict[str, float]) -> bool:
    """Valida que el plan cumpla con los objetivos de macros"""
    try:
        daily_totals = []
        for day in range(1, 4):  # 3 días
            meals = extract_meals_from_plan(plan_text, day)
            if not meals:  # Si falta algún día
                return False
            totals = calculate_daily_totals(meals)
            daily_totals.append(totals)
        
        # Verificar que los promedios estén dentro del ±10% del objetivo
        averages = calculate_averages(daily_totals)
        return validate_macros(averages, energy_needs)
        
    except Exception as e:
        st.warning(f"Error en la validación del plan: {str(e)}")
        return False

def get_creatine_protocol(supplements: List[str]) -> str:
    if "Creatina" in supplements:
        return """
        Fase de carga (7 días):
        - 8.7gr, 4 veces al día
        - Tomar con 150ml de jugo de frutas (la fructosa y vitamina C mejoran absorción)
        - Momento: pre desayuno
        
        Fase de mantenimiento:
        - 8.7gr diarios
        - Tomar pre desayuno
        - Mantener ingesta de líquidos alta
        """
    return ""

def format_meal_plan(meals: Dict[str, List[Dict]], day: int) -> str:
    """Formatea el plan diario con macros y calorías"""
    return f"""
### Día {day}

**Desayuno: "Desayuno Energético"** _(7:00 - 8:00)_
- 3 huevos revueltos con especias (120g) _[240 kcal | P: 18g | C: 0g | G: 16g]_
- 1 rebanada de pan integral tostado (50g) _[120 kcal | P: 4g | C: 23g | G: 1g]_
- 1 cucharada de aceite de oliva (15ml) _[120 kcal | P: 0g | C: 0g | G: 14g]_
- 1 manzana fresca (190g) _[95 kcal | P: 0.5g | C: 25g | G: 0g]_
**Total comida: 575 kcal | Proteína: 22.5g | Carbos: 48g | Grasas: 31g**

**Colación 1 (Dulce): "Snack Saludable"** _(10:00 - 10:30)_
- Mix de almendras naturales (30g) _[180 kcal | P: 6g | C: 6g | G: 15g]_
**Total comida: 180 kcal | Proteína: 6g | Carbos: 6g | Grasas: 15g**

**Almuerzo: "Pollo Mediterráneo"** _(12:00 - 13:00)_
- Pechuga de pollo a la plancha con hierbas (200g)
- Arroz integral aromático (100g en crudo)
- Mix de verduras al vapor (brócoli, zanahoria) a elección
- Aderezo de aceite de oliva extra virgen (15ml)

**Merienda: "Proteína Completa"** _(16:00 - 17:00)_
- Huevos duros (80g)
- Queso fresco (60g)

**Colación 2 (Dulce): "Energía Natural"** _(18:00 - 18:30)_
- Banana fresca (100g)

**Cena: "Parrilla Saludable"** _(20:00 - 21:00)_
- Bife de carne magra a la parrilla (200g)
- Puré rústico de batata (100g)
- Ensalada fresca de lechuga y tomate
- Aderezo de aceite de oliva (15ml)

**TOTALES DEL DÍA**
Total calorías: 2,400 kcal
Total proteína: 180g
Total carbohidratos: 220g
Total grasas: 93g
"""

def get_vegetarian_equivalences() -> str:
    """Retorna tabla de equivalencias vegetarianas"""
    return """
### Equivalencias Vegetarianas
| Alimento Animal | Equivalente Vegetariano | Proteína (g) |
|-----------------|------------------------|--------------|
| 100g pollo | 120g tempeh | 20g |
| 100g carne | 150g seitán | 25g |
| 2 huevos | 200g tofu firme | 16g |
| 100g pescado | 100g tempeh + 30g levadura nutricional | 22g |
| 100g atún | 150g garbanzos cocidos + semillas | 18g |
"""

def get_meal_timing() -> str:
    """Retorna guía de timing de comidas"""
    return """
    ### Timing de Comidas
    - **Desayuno:** 7:00 - 8:00
    - **Colación 1:** 10:00 - 10:30
    - **Almuerzo:** 12:30 - 13:30
    - **Merienda:** 16:00 - 16:30
    - **Colación 2:** 18:00 - 18:30
    - **Cena:** 20:00 - 21:00

    _Ajustar los horarios según tu rutina personal y de entrenamiento._
    """

def validate_plan_completeness(plan_text: str) -> bool:
    """Valida que el plan esté completo con todos sus componentes"""
    try:
        # Verificar que estén los 3 días
        for day in range(1, 4):
            if f"### DÍA {day}" not in plan_text:
                st.warning(f"Falta el día {day} en el plan")
                return False
            
            # Verificar que cada día tenga todas las comidas
            required_sections = [
                "Desayuno", "Colación Dulce 1", "Almuerzo",
                "Merienda", "Colación Dulce 2", "Cena",
                "TOTALES DEL DÍA", "SUPLEMENTACIÓN DEL DÍA"
            ]
            
            for section in required_sections:
                if section not in plan_text:
                    st.warning(f"Falta la sección {section} en el día {day}")
                    return False
                    
        return True
        
    except Exception as e:
        st.error(f"Error al validar completitud del plan: {str(e)}")
        return False

def show_generation_progress():
    """Muestra el progreso de generación del plan de forma visual"""
    
    # Contenedor principal para el progreso
    progress_container = st.empty()
    
    with progress_container.container():
        st.markdown("### 🔄 Generando Plan Nutricional")
        progress_bar = st.progress(0)
        
        # Fase 1: Preparación (30%)
        st.markdown("🔍 Analizando requerimientos nutricionales...")
        time.sleep(0.5)
        progress_bar.progress(0.1)
        
        st.markdown("📊 Calculando distribución de macronutrientes...")
        time.sleep(0.5)
        progress_bar.progress(0.2)
        
        st.markdown("🍳 Seleccionando alimentos apropiados...")
        time.sleep(0.5)
        progress_bar.progress(0.3)
        
        # Fase 2: Generación (60%)
        st.markdown("📝 Estructurando plan alimenticio...")
        time.sleep(0.5)
        progress_bar.progress(0.4)
        
        st.markdown("🔄 Optimizando distribución de comidas...")
        time.sleep(0.5)
        progress_bar.progress(0.5)
        
        st.markdown("⚖️ Ajustando porciones y cantidades...")
        time.sleep(0.5)
        progress_bar.progress(0.6)
        
        # Fase 3: Validación (90%)
        st.markdown("✅ Verificando balance nutricional...")
        time.sleep(0.5)
        progress_bar.progress(0.8)
        
        st.markdown("📋 Realizando validaciones finales...")
        time.sleep(0.5)
        progress_bar.progress(0.9)
        
        # Fase 4: Finalización (100%)
        st.markdown("✨ Finalizando generación del plan...")
        time.sleep(0.5)
        progress_bar.progress(1.0)
        
        # Limpiar el contenedor cuando termine
        time.sleep(1)
        progress_container.empty()

def validate_daily_totals(meals: List[Dict]) -> bool:
    """Valida que los totales diarios sean correctos"""
    calculated_totals = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0
    }
    
    for meal in meals:
        calculated_totals['calories'] += meal['calories']
        calculated_totals['protein'] += meal['protein']
        calculated_totals['carbs'] += meal['carbs']
        calculated_totals['fat'] += meal['fat']
    
    # Comparar con los totales reportados
    reported_totals = get_reported_totals(meals)
    
    tolerance = 0.01  # 1% de tolerancia
    for macro, value in calculated_totals.items():
        if abs(value - reported_totals[macro]) > (value * tolerance):
            st.warning(f"Error en total de {macro}: calculado={value}, reportado={reported_totals[macro]}")
            return False
            
    return True

def get_reported_totals(meals: List[Dict]) -> Dict[str, float]:
    """Obtiene los totales reportados del último bloque de cada día"""
    try:
        reported_totals = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0
        }
        
        # Buscar la línea de totales
        for meal in meals:
            if "TOTALES DEL DÍA" in meal.get('name', ''):
                # Extraer valores de las líneas de totales
                totals_text = meal.get('description', '')
                
                # Patrones para buscar los valores
                patterns = {
                    'calories': r'Total calorías:\s*(\d+(?:\.\d+)?)',
                    'protein': r'Total proteína:\s*(\d+(?:\.\d+)?)',
                    'carbs': r'Total carbohidratos:\s*(\d+(?:\.\d+)?)',
                    'fat': r'Total grasas:\s*(\d+(?:\.\d+)?)'
                }
                
                # Extraer cada valor usando regex
                for macro, pattern in patterns.items():
                    match = re.search(pattern, totals_text)
                    if match:
                        reported_totals[macro] = float(match.group(1))
                    else:
                        st.warning(f"No se encontró el total para {macro}")
                        
                break  # Solo necesitamos los totales una vez
        
        return reported_totals
        
    except Exception as e:
        st.error(f"Error al obtener totales reportados: {str(e)}")
        return reported_totals

def extract_meal_nutrients(meal_text: str) -> Dict[str, float]:
    """Extrae los valores nutricionales de una comida"""
    try:
        # Buscar el total de la comida
        pattern = r'Total comida:\s*(\d+(?:\.\d+)?)\s*kcal\s*\|\s*Proteína:\s*(\d+(?:\.\d+)?)g\s*\|\s*C:\s*(\d+(?:\.\d+)?)g\s*\|\s*G:\s*(\d+(?:\.\d+)?)g'
        match = re.search(pattern, meal_text)
        
        if match:
            return {
                'calories': float(match.group(1)),
                'protein': float(match.group(2)),
                'carbs': float(match.group(3)),
                'fat': float(match.group(4))
            }
        else:
            st.warning("No se encontraron valores nutricionales en la comida")
            return {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0
            }
            
    except Exception as e:
        st.error(f"Error al extraer nutrientes: {str(e)}")
        return {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0
        }

def validate_meal_structure(meal_text: str) -> bool:
    """Valida la estructura de cada comida"""
    try:
        # Verificar formato del título
        title_pattern = r'\*\*[^*]+:\s+"[^"]+"\*\*\s+_\(\d{1,2}:\d{2}(?:\s*-\s*\d{1,2}:\d{2})?\)_'
        if not re.search(title_pattern, meal_text):
            return False
            
        # Verificar formato de los alimentos
        food_pattern = r'-\s+.+\s+\(\d+g?\)\s+_\[\d+\s*kcal\s*\|\s*P:\s*\d+g\s*\|\s*C:\s*\d+g\s*\|\s*G:\s*\d+g\]_'
        if not re.findall(food_pattern, meal_text):
            return False
            
        # Verificar totales
        total_pattern = r'\*\*Total comida:\s*\d+\s*kcal\s*\|\s*Proteína:\s*\d+g\s*\|\s*Carbos:\s*\d+g\s*\|\s*Grasas:\s*\d+g\*\*'
        if not re.search(total_pattern, meal_text):
            return False
            
        return True
        
    except Exception as e:
        st.error(f"Error al validar estructura de comida: {str(e)}")
        return False

def validate_daily_totals_match(day_text: str) -> bool:
    """Valida que los totales del día coincidan con la suma de las comidas"""
    try:
        meals = re.findall(r'\*\*Total comida:.*?\*\*', day_text, re.DOTALL)
        daily_total = re.search(r'\*\*TOTALES DEL DÍA\*\*.*?Total calorías:\s*(\d+)', day_text, re.DOTALL)
        
        if not meals or not daily_total:
            return False
            
        calculated_calories = sum([
            int(re.search(r'Total comida:\s*(\d+)\s*kcal', meal).group(1))
            for meal in meals
        ])
        
        reported_calories = int(daily_total.group(1))
        
        # Permitir un margen de error de ±5 calorías
        return abs(calculated_calories - reported_calories) <= 5
        
    except Exception as e:
        st.error(f"Error al validar totales del día: {str(e)}")
        return False

def validate_nutrition_consistency(plan_text: str) -> bool:
    """Valida la consistencia nutricional entre días"""
    try:
        days = re.findall(r'### DÍA \d+.*?(?=### DÍA|\Z)', plan_text, re.DOTALL)
        
        for day in days:
            if not validate_meal_structure(day) or not validate_daily_totals_match(day):
                return False
                
        return True
        
    except Exception as e:
        st.error(f"Error al validar consistencia nutricional: {str(e)}")
        return False

def main():
    st.title("🥗 Generador de Plan Nutricional")
    
    tab1, tab2, tab3 = st.tabs(["Datos Personales", "Actividad Física", "Plan Nutricional"])
    
    with tab1:
        basic_data = collect_basic_data()
    
    with tab2:
        activity_data = collect_activity_data()
    
    with tab3:
        if st.button("Generar Plan Nutricional"):
            show_generation_progress()
            user_data = {
                'basic': basic_data,
                'activity': activity_data
            }
            
            with st.spinner('Generando plan personalizado...'):
                try:
                    result = generate_nutrition_plan(user_data)
                    if result:
                        plan_text, plan_pdf = result
                        st.markdown("### 🤖 Plan Nutricional Personalizado")
                        st.markdown(plan_text)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="Descargar Plan (TXT)",
                                data=plan_text,
                                file_name="plan_nutricional.txt",
                                mime="text/plain"
                            )
                        with col2:
                            st.download_button(
                                label="Descargar Plan (PDF)",
                                data=plan_pdf,
                                file_name="plan_nutricional.pdf",
                                mime="application/pdf"
                            )
                    else:
                        st.error("No se pudo generar el plan nutricional. Por favor, intenta de nuevo.")
                except Exception as e:
                    st.error(f"Error al generar el plan: {str(e)}")

if __name__ == "__main__":
    main()