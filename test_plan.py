from openai import OpenAI
import os
from dotenv import load_dotenv

def generate_test_plan():
    try:
        # 1. Configurar OpenAI
        load_dotenv()
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 2. Datos de prueba
        test_data = {
            'peso': 80,
            'altura': 175,
            'edad': 30,
            'objetivo': 'Pérdida de grasa',
            'restricciones': ['Lácteos'],
            'preferencias': ['Pollo', 'Pescado', 'Arroz']
        }
        
        # 3. Generar prompt
        prompt = f"""
        Genera un plan nutricional de 3 días siguiendo EXACTAMENTE este formato:

        DÍA 1:
        
        DESAYUNO (7:00):
        - Alimentos y cantidades en gramos
        - Macros: Proteínas XXg, Carbos XXg, Grasas XXg
        - Calorías totales: XXX kcal
        
        ALMUERZO (13:00):
        - Alimentos y cantidades en gramos
        - Macros: Proteínas XXg, Carbos XXg, Grasas XXg
        - Calorías totales: XXX kcal
        
        CENA (21:00):
        - Alimentos y cantidades en gramos
        - Macros: Proteínas XXg, Carbos XXg, Grasas XXg
        - Calorías totales: XXX kcal
        
        RESUMEN DÍA 1:
        Total Calorías: XXXX kcal
        Total Proteínas: XXXg
        Total Carbohidratos: XXXg
        Total Grasas: XXXg
        
        [Repetir mismo formato para DÍA 2 y DÍA 3]
        
        DATOS DEL PACIENTE:
        - Peso: {test_data['peso']} kg
        - Altura: {test_data['altura']} cm
        - Edad: {test_data['edad']} años
        - Objetivo: {test_data['objetivo']}
        - No consume: {', '.join(test_data['restricciones'])}
        - Preferencias: {', '.join(test_data['preferencias'])}
        """
        
        # 4. Llamar a la API
        print("Generando plan nutricional...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un nutricionista experto. DEBES seguir EXACTAMENTE el formato solicitado."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        # 5. Guardar resultado
        plan = response.choices[0].message.content
        print("\n=== PLAN NUTRICIONAL GENERADO ===\n")
        print(plan)
        
        with open('plan_test.txt', 'w', encoding='utf-8') as f:
            f.write(plan)
        print("\nPlan guardado en 'plan_test.txt'")
        
        return plan
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    generate_test_plan() 
# Verificar configuración
def check_setup():
    print("Verificando configuración...")
    
    # Verificar API Key
    if not os.getenv("OPENAI_API_KEY"):
        raise Exception("❌ OPENAI_API_KEY no encontrada en variables de entorno")
    
    # Verificar archivo del libro
    if not os.path.exists('data/libro_nutricion.pdf'):
        raise Exception("❌ Libro de nutrición no encontrado en data/libro_nutricion.pdf")
    
    print("✅ Configuración correcta")

# Datos de prueba
test_data = {
    'basic': {
        'edad': 30,
        'altura': 175,
        'peso': 80,
        'grasa': 20,
        'musculo': 40,
        'pais': 'Argentina',
        'provincia': 'Buenos Aires',
        'objetivo_principal': 'Pérdida de grasa',
        'objetivos_secundarios': ['Mejorar energía', 'Definición muscular'],
        'tiempo_objetivo': 12,
        'patologia': ['Ninguna'],
        'suplementacion': ['Proteína', 'Creatina'],
        'no_consume': ['Lácteos'],
        'preferencias': ['Pollo', 'Pescado', 'Arroz'],
        'comidas_principales': ['Desayuno', 'Almuerzo', 'Merienda', 'Cena'],
        'incluir_colaciones': True,
        'tipo_colaciones_regulares': 'Ambas',
        'n_colaciones_regulares': 2,
        'colaciones_deportivas': ['Pre-entreno', 'Post-entreno'],
        'objetivo_peso': 'Pérdida 0.5kg/semana',
        'porcentaje_carbos': '40%',
        'objetivo_proteina': 'Altas (2.2g/kg)'
    },
    'activity': {
        'tipo_actividad': ['Musculación', 'Cardio'],
        'frecuencia': 5,
        'duracion': 60,
        'intensidad': 'Alta',
        'reloj_data': None
    },
    'anabolic': {
        'tiene_ciclo': False
    }
}

def main():
    try:
        # Verificar configuración
        check_setup()
        
        print("\nGenerando plan nutricional...")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 