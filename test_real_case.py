from vector_db import VectorDBManager
from dotenv import load_dotenv
import time

def test_real_case():
    load_dotenv()
    db = VectorDBManager()
    
    # Simular el caso real de usuario
    user_profile = {
        'objetivo_principal': 'pérdida de grasa',
        'restricciones': ['sin lácteos'],
        'suplementacion': ['proteína', 'creatina'],
        'actividad': 'musculación',
        'intensidad': 'alta'
    }
    
    # Queries basadas en el perfil
    test_queries = [
        # Queries para restricciones alimentarias
        f"alternativas sin lácteos para {user_profile['objetivo_principal']}",
        "proteínas sin lácteos",
        
        # Queries para suplementación
        f"suplementación {' '.join(user_profile['suplementacion'])}",
        "timing suplementos proteína",
        
        # Queries para el método y plan
        f"método tres días y carga para {user_profile['objetivo_principal']}",
        f"plan alimentación {user_profile['objetivo_principal']} {user_profile['actividad']}"
    ]
    
    print("\n=== Test Caso Real ===")
    print("\nPerfil del usuario:")
    for key, value in user_profile.items():
        print(f"• {key}: {value}")
    
    all_results = []
    
    for query in test_queries:
        print(f"\n\n📝 Query: '{query}'")
        try:
            results = db.search_knowledge(
                query=query,
                top_k=2,
                threshold=0.4
            )
            
            if results:
                print(f"\n✅ Encontrados {len(results)} resultados:")
                for i, result in enumerate(results, 1):
                    print(f"\nResultado {i}:")
                    print(f"• Score: {result['score']:.3f}")
                    print(f"• Sección: {result['section']}")
                    print(f"• Tags: {', '.join(result['tags'])}")
                    print(f"• Texto: {result['text'][:200]}...")
                    all_results.extend(results)
            else:
                print("❌ Sin resultados")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Análisis final
    if all_results:
        print("\n\n📊 Análisis General:")
        unique_texts = set(r['text'][:100] for r in all_results)  # Primeros 100 chars para comparar
        sections = set(r['section'] for r in all_results)
        tags = set(tag for r in all_results for tag in r['tags'])
        
        print(f"\nEstadísticas:")
        print(f"• Total de queries: {len(test_queries)}")
        print(f"• Resultados únicos: {len(unique_texts)}")
        print(f"• Secciones cubiertas: {', '.join(sections)}")
        print(f"• Tags encontrados: {', '.join(tags)}")
        
        # Análisis por sección
        print("\nDistribución por sección:")
        section_counts = {}
        for r in all_results:
            section_counts[r['section']] = section_counts.get(r['section'], 0) + 1
        
        for section, count in section_counts.items():
            print(f"• {section}: {count} resultados")
    
    print("\n=== Fin del Test ===")

if __name__ == "__main__":
    test_real_case() 