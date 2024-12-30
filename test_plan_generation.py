from app2 import generate_nutrition_plan
from vector_db import VectorDBManager
from openai import OpenAI
from dotenv import load_dotenv
import os

def analyze_plan(plan_text):
    plan_lines = plan_text.split('\n')
    
    analysis = {
        'dias': len([l for l in plan_lines if l.strip().startswith('DÍA')]),
        'comidas': len([l for l in plan_lines if any(meal in l for meal in ['DESAYUNO', 'ALMUERZO', 'MERIENDA', 'CENA'])]),
        'macros': len([l for l in plan_lines if l.strip().startswith('• Macros:')]),
        'calorias_totales': []
    }
    
    # Extraer calorías totales por día
    current_day = None
    for line in plan_lines:
        if line.strip().startswith('DÍA'):
            current_day = line.strip()
        if 'Total calorías:' in line:
            try:
                cals = int(line.split('kcal')[0].split(':')[1].strip())
                analysis['calorias_totales'].append((current_day, cals))
            except:
                continue
    
    return analysis

def test_plan_generation():
    # Configurar servicios
    load_dotenv()
    openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    db_manager = VectorDBManager()
    
    # Caso de prueba
    test_user_data = {
        'basic': {
            'edad': 30,
            'altura': 175,
            'peso': 80,
            'grasa': 20,
            'musculo': 40,
            'pais': 'Argentina',
            'provincia': 'Buenos Aires',
            'objetivo_principal': 'pérdida de grasa',
            'objetivos_secundarios': ['Mejorar energía', 'Definición muscular'],
            'tiempo_objetivo': 12,
            'objetivo_peso': 'Pérdida 0.5kg/semana',
            'porcentaje_carbos': '40%',
            'objetivo_proteina': 'Altas (2.2g/kg)',
            'patologia': ['Ninguna'],
            'suplementacion': ['Proteína', 'Creatina'],
            'no_consume': ['Lácteos'],
            'preferencias': ['Pollo', 'Pescado', 'Huevos'],
            'comidas_principales': ['Desayuno', 'Almuerzo', 'Merienda', 'Cena'],
            'incluir_colaciones': True,
            'tipo_colaciones_regulares': 'Ambas',
            'n_colaciones_regulares': 2,
            'colaciones_deportivas': ['Pre-entreno', 'Post-entreno']
        },
        'activity': {
            'tipo_actividad': ['Musculación'],
            'frecuencia': 5,
            'duracion': 60,
            'intensidad': 'Alta'
        }
    }
    
    print("\n=== Iniciando Generación de Plan de Prueba ===")
    print("\nDatos del usuario de prueba:")
    print(f"• Objetivo: {test_user_data['basic']['objetivo_principal']}")
    print(f"• Restricciones: {test_user_data['basic']['no_consume']}")
    print(f"• Actividad: {test_user_data['activity']['tipo_actividad']}")
    
    try:
        print("\n🔍 Generando plan nutricional...")
        plan = generate_nutrition_plan(test_user_data)
        
        if plan:
            print("\n✅ Plan generado exitosamente!")
            
            # Análisis del plan
            analysis = analyze_plan(plan)
            print("\n📊 Análisis del Plan:")
            print(f"• Días incluidos: {analysis['dias']}")
            print(f"• Comidas totales: {analysis['comidas']}")
            print(f"• Cálculos de macros: {analysis['macros']}")
            print("\nCalorías por día:")
            for day, cals in analysis['calorias_totales']:
                print(f"• {day}: {cals} kcal")
            
            # Verificar restricciones
            if 'Lácteos' in test_user_data['basic']['no_consume']:
                lacteos = ['leche', 'queso', 'yogur', 'yogurt', 'whey']
                lacteos_found = []
                for line in plan.split('\n'):
                    for lacteo in lacteos:
                        if lacteo in line.lower():
                            lacteos_found.append(f"{lacteo} en: {line.strip()}")
                
                if lacteos_found:
                    print("\n⚠️ ADVERTENCIA: Se encontraron lácteos:")
                    for found in lacteos_found:
                        print(f"  • {found}")
                else:
                    print("\n✅ No se encontraron menciones a lácteos (restricción respetada)")
            
            # Guardar el plan
            with open('plan_nutricional_test.txt', 'w', encoding='utf-8') as f:
                f.write(plan)
            print("\n📝 Plan guardado en 'plan_nutricional_test.txt'")
            
        else:
            print("\n❌ Error: No se pudo generar el plan")
            
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {str(e)}")
        import traceback
        print("\nDetalles del error:")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_plan_generation() 