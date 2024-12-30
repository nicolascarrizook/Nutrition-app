from vector_db import VectorDBManager
from dotenv import load_dotenv
import time
from pprint import pprint

def test_detailed_search():
    load_dotenv()
    db = VectorDBManager()
    
    test_cases = [
        {
            'name': 'Restricción Lácteos',
            'queries': [
                'alternativas sin lácteos',
                'opciones sin lactosa',
                'proteínas sin lácteos'
            ]
        },
        {
            'name': 'Suplementación',
            'queries': [
                'suplementación proteína',
                'timing suplementos',
                'dosis creatina'
            ]
        },
        {
            'name': 'Método y Planes',
            'queries': [
                'método tres días y carga',
                'plan alimentación pérdida grasa',
                'nutrición musculación'
            ]
        }
    ]
    
    print("\n=== Test Detallado de Búsqueda ===")
    
    for case in test_cases:
        print(f"\n\n📌 Caso: {case['name']}")
        case_results = []
        
        for query in case['queries']:
            print(f"\nQuery: '{query}'")
            try:
                results = db.search_knowledge(
                    query=query,
                    top_k=2,
                    threshold=0.4  # Threshold más permisivo
                )
                
                if results:
                    print(f"✅ {len(results)} resultados encontrados")
                    for i, result in enumerate(results, 1):
                        print(f"\nResultado {i}:")
                        print(f"• Score: {result['score']:.3f}")
                        print(f"• Sección: {result['section']}")
                        print(f"• Tags: {', '.join(result['tags'])}")
                        print(f"• Texto: {result['text'][:150]}...")
                        case_results.append(result)
                else:
                    print("❌ Sin resultados")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error: {str(e)}")
        
        # Análisis del caso
        if case_results:
            print(f"\n📊 Análisis para {case['name']}:")
            sections = set(r['section'] for r in case_results)
            tags = set(tag for r in case_results for tag in r['tags'])
            scores = [r['score'] for r in case_results]
            
            print(f"• Secciones encontradas: {', '.join(sections)}")
            print(f"• Tags únicos: {', '.join(tags)}")
            print(f"• Rango de scores: {min(scores):.3f} - {max(scores):.3f}")
            print(f"• Total resultados únicos: {len(set(r['text'] for r in case_results))}")
    
    print("\n=== Fin del Test ===")

if __name__ == "__main__":
    test_detailed_search() 