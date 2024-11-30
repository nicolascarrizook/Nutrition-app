import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import os
import PyPDF2
import io

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
        # Datos básicos
        data['edad'] = st.number_input("Edad", 18, 100)
        data['altura'] = st.number_input("Altura (cm)", 140, 220)
        data['peso'] = st.number_input("Peso (kg)", 40, 200)
        data['grasa'] = st.number_input("Porcentaje de grasa corporal", 0, 50)
        data['musculo'] = st.number_input("Porcentaje de músculo", 0, 100)
        
        # Ubicación
        data['pais'] = st.selectbox(
            "País",
            ["Argentina", "España", "México", "Colombia", "Chile", "Perú", "Uruguay"]
        )
        if data['pais'] == "Argentina":
            data['provincia'] = st.selectbox(
                "Provincia",
                ["Buenos Aires", "Córdoba", "Santa Fe", "Mendoza", "Tucumán", "Entre Ríos", "Salta", "Otras"]
            )
        
        # Objetivos
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

        # Objetivos nutricionales
        data['objetivo_peso'] = st.selectbox(
            "Objetivo de Peso",
            ["Mantención", 
             "Pérdida 0.5kg/semana",
             "Pérdida 1kg/semana",
             "Ganancia 0.5kg/semana",
             "Ganancia 1kg/semana"]
        )
        
        data['porcentaje_carbos'] = st.select_slider(
            "Porcentaje de Carbohidratos",
            options=[f"{i}%" for i in range(5, 60, 5)],
            value="40%"
        )
        
        data['objetivo_proteina'] = st.selectbox(
            "Objetivo de Proteínas",
            ["Bajas (0.8g/kg)",
             "Normales (1.6g/kg)",
             "Altas (2.2g/kg)",
             "Muy altas (2.8g/kg)",
             "Adecuadas anabólicos (3.0g/kg)",
             "Adecuadas patología (según condición)",
             "Recuperación entrenamiento (2.4g/kg)",
             "Enfoque saciedad (2.6g/kg)"]
        )

    with col2:
        # Datos médicos y restricciones
        data['patologia'] = st.multiselect(
            "Patologías",
            ["Diabetes", "Hipertensión", "Colesterol alto", "Ninguna"]
        )
        
        data['suplementacion'] = st.multiselect(
            "Suplementación actual",
            ["Proteína", "Creatina", "BCAA", "Ninguna"]
        )
        
        # Preferencias alimentarias
        st.markdown("### 🍽️ Preferencias Alimentarias")
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
        
        # Estructura de comidas
        st.markdown("### 🍽️ Estructura de Comidas")
        data['comidas_principales'] = st.multiselect(
            "Comidas principales",
            ["Desayuno", "Almuerzo", "Merienda", "Cena"],
            default=["Desayuno", "Almuerzo", "Merienda", "Cena"]
        )
        
        # Sistema de colaciones
        data['incluir_colaciones'] = st.checkbox("Incluir colaciones")
        if data['incluir_colaciones']:
            st.markdown("#### Colaciones Entre Comidas")
            data['tipo_colaciones_regulares'] = st.selectbox(
                "Tipo de colaciones entre comidas",
                ["Dulces", "Saladas", "Ambas"]
            )
            data['n_colaciones_regulares'] = st.number_input(
                "Número de colaciones entre comidas", 0, 4, 2
            )
            
            st.markdown("#### Colaciones Deportivas")
            data['colaciones_deportivas'] = st.multiselect(
                "Colaciones relacionadas al entrenamiento",
                ["Pre-entreno", "Intra-entreno", "Post-entreno"]
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
        # Calcular calorías y macros básicos
        peso = user_data['basic']['peso']
        altura = user_data['basic']['altura']
        edad = user_data['basic']['edad']
        
        # Verificar suplementación
        tiene_suplementos = 'Ninguna' not in user_data['basic']['suplementacion'] and len(user_data['basic']['suplementacion']) > 0
        
        # Calcular TMB y factores
        tmb = 10 * peso + 6.25 * altura - 5 * edad
        actividad_factores = {
            "Baja": 1.2,
            "Media": 1.375,
            "Alta": 1.55,
            "Muy alta": 1.725
        }
        factor = actividad_factores[user_data['activity']['intensidad']]
        calorias_mantenimiento = tmb * factor
        
        # Ajustar calorías según objetivo
        objetivos_calorias = {
            "Mantención": calorias_mantenimiento,
            "Pérdida 0.5kg/semana": calorias_mantenimiento - 500,
            "Pérdida 1kg/semana": calorias_mantenimiento - 1000,
            "Ganancia 0.5kg/semana": calorias_mantenimiento + 500,
            "Ganancia 1kg/semana": calorias_mantenimiento + 1000
        }
        
        calorias_objetivo = objetivos_calorias[user_data['basic']['objetivo_peso']]
        porcentaje_carbos = int(user_data['basic']['porcentaje_carbos'].replace('%', ''))
        
        # Calcular proteínas según objetivo
        proteinas_por_kg = {
            "Bajas (0.8g/kg)": 0.8,
            "Normales (1.6g/kg)": 1.6,
            "Altas (2.2g/kg)": 2.2,
            "Muy altas (2.8g/kg)": 2.8,
            "Adecuadas anabólicos (3.0g/kg)": 3.0,
            "Recuperación entrenamiento (2.4g/kg)": 2.4,
            "Enfoque saciedad (2.6g/kg)": 2.6,
            "Adecuadas patología (según condición)": 2.0
        }
        
        # Calcular macros
        gramos_proteina = proteinas_por_kg[user_data['basic']['objetivo_proteina']] * peso
        calorias_proteina = gramos_proteina * 4
        
        calorias_carbos = (calorias_objetivo * porcentaje_carbos) / 100
        gramos_carbos = calorias_carbos / 4
        
        calorias_restantes = calorias_objetivo - calorias_proteina - calorias_carbos
        gramos_grasa = calorias_restantes / 9

        # Ajustar distribución de calorías según comidas y colaciones
        total_comidas = len(user_data['basic']['comidas_principales'])
        tiene_colaciones = user_data['basic'].get('incluir_colaciones', False)
        
        # Calcular calorías por comida principal (siempre equivalentes)
        if tiene_colaciones:
            calorias_por_comida_principal = (calorias_objetivo * 0.8) / total_comidas  # 80% para comidas principales
            n_colaciones = user_data['basic'].get('n_colaciones_regulares', 0)
            calorias_por_colacion = (calorias_objetivo * 0.2) / n_colaciones  # 20% para colaciones
        else:
            calorias_por_comida_principal = calorias_objetivo / total_comidas
            calorias_por_colacion = 0

        # Calcular macros por comida principal (distribución equitativa)
        macros_por_comida = {
            'proteinas': gramos_proteina / total_comidas,  # Distribución exactamente igual
            'carbos': gramos_carbos / total_comidas,
            'grasas': gramos_grasa / total_comidas
        }

        # Definir perfiles de colaciones según tipo
        colaciones_info = {
            'regulares_dulces': {
                'calorias': calorias_por_colacion,
                'proteinas': 15,
                'carbos': 25,
                'grasas': 5
            },
            'regulares_saladas': {
                'calorias': calorias_por_colacion,
                'proteinas': 15,
                'carbos': 15,
                'grasas': 10
            },
            'pre_entreno': {
                'calorias': 250,
                'proteinas': 15,
                'carbos': 40,
                'grasas': 5
            },
            'intra_entreno': {
                'calorias': 100,
                'proteinas': 0,
                'carbos': 25,
                'grasas': 0
            },
            'post_entreno': {
                'calorias': 300,
                'proteinas': 25,
                'carbos': 35,
                'grasas': 5
            }
        }

        # Generar planes para cada día
        plans = []
        location_context = f"{user_data['basic']['pais']}, {user_data['basic']['provincia']}" if 'provincia' in user_data['basic'] else user_data['basic']['pais']

        for day in range(1, 4):
            prompt = f"""
            Eres un nutricionista deportivo argentino especializado en el Método Tres Días y Carga®️ & Nutrición Evolutiva.
            
            DATOS DEL PACIENTE:
            - Localidad: {location_context}
            - Edad: {user_data['basic']['edad']} años
            - Peso corporal: {user_data['basic']['peso']} kg
            - Talla: {user_data['basic']['altura']} cm
            - Porcentaje de tejido adiposo: {user_data['basic']['grasa']}%
            - Porcentaje de masa muscular: {user_data['basic']['musculo']}%
            - Objetivo Principal: {user_data['basic']['objetivo_principal']}
            - Objetivos Secundarios: {', '.join(user_data['basic']['objetivos_secundarios'])}
            - Duración del plan: {user_data['basic']['tiempo_objetivo']} semanas
            - Patologías de base: {', '.join(user_data['basic']['patologia'])}
            - Suplementación actual: {', '.join(user_data['basic']['suplementacion'])}
            - Alimentos excluidos/Alergias: {', '.join(user_data['basic']['no_consume'])}
            - Preferencias alimentarias: {', '.join(user_data['basic']['preferencias'])}
            - Tipo de entrenamiento: {', '.join(user_data['activity']['tipo_actividad'])}
            - Frecuencia semanal: {user_data['activity']['frecuencia']} días
            - Intensidad del entrenamiento: {user_data['activity']['intensidad']}

            PAUTAS NUTRICIONALES:
            - Valor calórico total: {int(calorias_objetivo)} kcal
            - Objetivo de composición corporal: {user_data['basic']['objetivo_peso']}
            - Proteínas: {int(gramos_proteina)}g ({user_data['basic']['objetivo_proteina']})
            - Hidratos de carbono: {int(gramos_carbos)}g ({porcentaje_carbos}% del VCT)
            - Grasas: {int(gramos_grasa)}g

            DISTRIBUCIÓN DE COMIDAS PRINCIPALES:
            IMPORTANTE: TODAS las comidas principales deben contener EXACTAMENTE:
            - Valor calórico: {int(calorias_por_comida_principal)} kcal (±20 kcal)
            - Proteínas: {int(macros_por_comida['proteinas'])}g (±3g)
            - Hidratos: {int(macros_por_comida['carbos'])}g (±3g)
            - Grasas: {int(macros_por_comida['grasas'])}g (±2g)

            NOTA CRÍTICA: Cada comida principal (Desayuno, Almuerzo, Merienda, Cena) debe mantener 
            EXACTAMENTE la misma distribución de macronutrientes. NO reducir proteínas en ninguna comida.

            {f'''DISTRIBUCIÓN DE COLACIONES:
            
            Colaciones Entre Comidas ({user_data['basic']['tipo_colaciones_regulares']}):
            - Valor calórico: {int(calorias_por_colacion)} kcal
            - Proteínas: {colaciones_info['regulares_dulces' if user_data['basic']['tipo_colaciones_regulares'] == 'Dulces' else 'regulares_saladas']['proteinas']}g
            - Hidratos: {colaciones_info['regulares_dulces' if user_data['basic']['tipo_colaciones_regulares'] == 'Dulces' else 'regulares_saladas']['carbos']}g
            - Grasas: {colaciones_info['regulares_dulces' if user_data['basic']['tipo_colaciones_regulares'] == 'Dulces' else 'regulares_saladas']['grasas']}g

            EJEMPLOS DE COLACIONES:
            {'Opciones dulces: barritas caseras, frutas, budines proteicos caseros' if user_data['basic']['tipo_colaciones_regulares'] in ['Dulces', 'Ambas'] else ''}
            {'Opciones saladas: frutos secos, sandwiches saludables, wraps' if user_data['basic']['tipo_colaciones_regulares'] in ['Saladas', 'Ambas'] else ''}

            {"""COLACIONES DEPORTIVAS:""" if user_data['basic'].get('colaciones_deportivas') else ""}
            {"Pre-entreno:" if "Pre-entreno" in user_data['basic'].get('colaciones_deportivas', []) else ""}
            {f"""- Valor calórico: {colaciones_info['pre_entreno']['calorias']} kcal
            - Proteínas: {colaciones_info['pre_entreno']['proteinas']}g
            - Hidratos: {colaciones_info['pre_entreno']['carbos']}g
            - Grasas: {colaciones_info['pre_entreno']['grasas']}g""" if "Pre-entreno" in user_data['basic'].get('colaciones_deportivas', []) else ""}

            {"Intra-entreno:" if "Intra-entreno" in user_data['basic'].get('colaciones_deportivas', []) else ""}
            {f"""- Valor calórico: {colaciones_info['intra_entreno']['calorias']} kcal
            - Hidratos: {colaciones_info['intra_entreno']['carbos']}g""" if "Intra-entreno" in user_data['basic'].get('colaciones_deportivas', []) else ""}

            {"Post-entreno:" if "Post-entreno" in user_data['basic'].get('colaciones_deportivas', []) else ""}
            {f"""- Valor calórico: {colaciones_info['post_entreno']['calorias']} kcal
            - Proteínas: {colaciones_info['post_entreno']['proteinas']}g
            - Hidratos: {colaciones_info['post_entreno']['carbos']}g
            - Grasas: {colaciones_info['post_entreno']['grasas']}g""" if "Post-entreno" in user_data['basic'].get('colaciones_deportivas', []) else ""}
            ''' if tiene_colaciones else ''}

            PAUTAS CRÍTICAS:
            1. {'Se pueden incluir los suplementos mencionados' if tiene_suplementos else 'NO incluir suplementos deportivos de ningún tipo'}
            2. Fuentes proteicas a priorizar:
               - Cortes magros de carne vacuna
               - Pollo (pechuga, pata y muslo)
               - Pescados
               - Huevos
               - Lácteos (si no hay restricción)
               - Legumbres
            3. Usar marcas disponibles en {location_context}
            4. Priorizar alimentos de temporada

            ESTRUCTURA DE COMIDAS:
            Comidas principales: {', '.join(user_data['basic']['comidas_principales'])}
            {f'''Colaciones regulares: {user_data['basic']['tipo_colaciones_regulares']} 
            Colaciones deportivas: {', '.join(user_data['basic'].get('colaciones_deportivas', []))}''' if tiene_colaciones else 'Sin colaciones'}

            PAUTAS ESPECÍFICAS POR COMIDA:

            DESAYUNO (si incluido):
            - Opciones típicas argentinas: mate, café, té, leche, yogur, tostadas, galletitas, facturas (si corresponde al plan), cereales
            - Valor calórico: {int(calorias_por_comida_principal)} kcal (±20 kcal)
            
            ALMUERZO:
            - Enfoque en proteína principal (carne vacuna, pollo, pescado)
            - Guarniciones típicas argentinas
            - Valor calórico: {int(calorias_por_comida_principal)} kcal (±20 kcal)
            
            MERIENDA (si incluida):
            - Similar al desayuno, adaptado a preferencias locales
            - Valor calórico: {int(calorias_por_comida_principal)} kcal (±20 kcal)
            
            CENA:
            - Más liviana que el almuerzo pero completa
            - Opciones típicas argentinas adaptadas
            - Valor calórico: {int(calorias_por_comida_principal)} kcal (±20 kcal)

            {f'''COLACIONES: 
            - Tipo: {user_data['basic']['tipo_colaciones_regulares']} 
            - Número de colaciones: {user_data['basic']['n_colaciones_regulares']}
            - Valor calórico por colación: {int(calorias_por_colacion)} kcal (±20 kcal)
            - Timing según horarios de entrenamiento
            {'- Opciones dulces: barritas caseras, frutas, budines proteicos caseros' if user_data['basic']['tipo_colaciones_regulares'] in ['Dulces', 'Ambas'] else ''}
            {'- Opciones saladas: frutos secos, sandwiches saludables, wraps' if user_data['basic']['tipo_colaciones_regulares'] in ['Saladas', 'Ambas'] else ''}
            {"""- Colaciones deportivas: """ + ', '.join(user_data['basic'].get('colaciones_deportivas', [])) if user_data['basic'].get('colaciones_deportivas') else ''}''' if tiene_colaciones else ''}

            FORMATO DEL PLAN:

            DÍA {day}

            [COMIDA PRINCIPAL] - Horario sugerido: [XX:XX]
            
            OPCIÓN 1:
            Nombre de la preparación: [nombre]
            
            Ingredientes:
            - [cantidad en gramos] [ingrediente] ([marca1] o [marca2] o [marca3])
            
            Preparación:
            1. [paso detallado]
            2. [paso detallado]
            
            Aporte nutricional:
            - Valor calórico: X kcal
            - Proteínas: X g
            - Hidratos de carbono: X g
            - Grasas: X g
            - Fibra: X g
            - Sodio: X mg
            - Potasio: X mg
            - Magnesio: X mg

            {f'''COLACIÓN [número] - Horario sugerido: [XX:XX]
            (Repetir formato para cada colación programada)''' if tiene_colaciones else ''}

            Balance del Día {day}:
            - Valor calórico total: {int(calorias_objetivo)} kcal
            - Proteínas totales: {int(gramos_proteina)}g
            - Hidratos totales: {int(gramos_carbos)}g
            - Grasas totales: {int(gramos_grasa)}g
            - Observaciones sobre digestibilidad y timing nutricional
            """

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un nutricionista experto en el Método Tres Días y Carga®️ & Nutrición Evolutiva, especializado en planes personalizados con opciones equivalentes en macronutrientes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            plans.append(response.choices[0].message.content)
        
        # Combinar los tres días en un solo plan
        full_plan = "\n\n---\n\n".join(plans)
        
        return full_plan
        
    except Exception as e:
        return f"Error generando el plan: {str(e)}"
        
def create_pdf(content):
    try:
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Configurar fuente y márgenes
        pdf.set_font("Arial", size=10)  # Reducido de 12 a 10
        pdf.set_margins(20, 20, 20)  # Márgenes más pequeños
        
        # Agregar título
        pdf.set_font("Arial", "B", 14)  # Reducido de 16 a 14
        pdf.cell(0, 10, txt="Plan Nutricional Personalizado", ln=True, align='C')
        
        # Restaurar fuente normal
        pdf.set_font("Arial", size=10)
        
        # Procesar el contenido línea por línea
        for line in content.split('\n'):
            # Limpiar la línea
            clean_line = line.strip()
            if not clean_line:
                continue
                
            # Codificar el texto para manejar caracteres especiales
            encoded_line = clean_line.encode('latin-1', 'replace').decode('latin-1')
            
            # Calcular el ancho efectivo de la página
            effective_width = pdf.w - 2 * pdf.l_margin
            
            # Si la línea es muy larga, dividirla en múltiples líneas
            if pdf.get_string_width(encoded_line) > effective_width:
                words = encoded_line.split()
                current_line = ""
                
                for word in words:
                    # Verificar si agregar la siguiente palabra excedería el ancho
                    test_line = current_line + " " + word if current_line else word
                    if pdf.get_string_width(test_line) <= effective_width:
                        current_line = test_line
                    else:
                        # Escribir la línea actual y comenzar una nueva
                        pdf.multi_cell(0, 5, txt=current_line, align='L')
                        current_line = word
                
                # Escribir la última línea si queda algo
                if current_line:
                    pdf.multi_cell(0, 5, txt=current_line, align='L')
            else:
                # La línea cabe en el ancho disponible
                pdf.multi_cell(0, 5, txt=encoded_line, align='L')
        
        # Retornar el PDF como bytes
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"Error creando PDF: {str(e)}")
        return None

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
                
                # Botón para descargar el plan en formato texto
                st.download_button(
                    label="Descargar Plan (TXT)",
                    data=plan,
                    file_name="plan_nutricional.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()