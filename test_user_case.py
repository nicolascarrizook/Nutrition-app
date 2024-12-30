from vector_db import VectorDBManager
from dotenv import load_dotenv
import time

def test_user_case():
    load_dotenv()
    db = VectorDBManager()
    
    # Simular datos reales de app2.py
    user_data = {
        'basic': {
            'objetivo_principal': 'pérdida de grasa',
            'objetivos_secundarios': ['mejorar energía', 'definición muscular'],
            'patologia': ['Ninguna'],
            'peso': 85,
            'altura': 175,
            'edad': 30,
            'objetivo_peso': 'bajar',
            'objetivo_proteina': 'alto',
            'suplementacion': ['creatina', 'proteína'],
            'no_consume': ['lácteos'],
            'preferencias': ['pollo', 'pescado']
        },
        'activity': {
            'tipo_actividad': ['musculación', 'cardio'],
            'intensidad': 'alta',
            'frecuencia': 5
        }
    }
    
    print("\n=== Test con Datos Reales de Usuario ===")
    print("\nPerfil del usuario:")
    print(f"• Objetivo principal: {user_data['basic']['objetivo_principal']}")
    print(f"• Objetivos secundarios: {', '.join(user_data['basic']['objetivos_secundarios'])}")
    print(f"• Actividad: {', '.join(user_data['activity']['tipo_actividad'])} ({user_data['activity']['intensidad']})")
    print(f"• Suplementación: {', '.join(user_data['basic']['suplementacion'])}")
    print(f"• Restricciones: {', '.join(user_data['basic']['no_consume'])}")
    
    # Queries específicas basadas en el perfil
    test_queries = [
        f"método tres días y carga para {user_data['basic']['objetivo_principal']}",
        f"nutrición {user_data['activity']['tipo_actividad'][0]} {user_data['basic']['objetivo_principal']}",
        f"suplementación {' '.join(user_data['basic']['suplementacion'])} para {user_data['basic']['objetivo_principal']}",
        f"alternativas sin {' '.join(user_data['basic']['no_consume'])}",
        f"plan alimentación {user_data['basic']['objetivo_peso']} proteína {user_data['basic']['objetivo_proteina']}"
    ]
    
    print("\nRealizando búsquedas...")
    all_results = []
    all_tags = set()
    
    for query in test_queries:
        print(f"\n📍 Query: '{query}'")
        try:
            results = db.search_knowledge(
                query=query,
                top_k=2,
                threshold=0.5
            )
            
            if results:
                print(f"✅ {len(results)} resultados encontrados")
                for i, result in enumerate(results, 1):
                    print(f"\nResultado {i}:")
                    print(f"Score: {result['score']:.3f}")
                    print(f"Sección: {result['section']}")
                    print(f"Tags: {result['tags']}")
                    print(f"Texto: {result['text'][:150]}...")
                    all_results.extend(results)
                    all_tags.update(result['tags'])
            else:
                print("❌ Sin resultados")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Análisis de resultados
    print("\n=== Análisis de Resultados ===")
    print(f"• Total de búsquedas: {len(test_queries)}")
    print(f"• Resultados únicos: {len(set(r['text'] for r in all_results))}")
    print(f"• Secciones cubiertas: {len(set(r['section'] for r in all_results))}")
    print("\nTags encontrados:")
    for tag in sorted(all_tags):
        print(f"• {tag}")

if __name__ == "__main__":
    test_user_case() 