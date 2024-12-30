from vector_db import VectorDBManager
from dotenv import load_dotenv
import time

def test_specific_queries():
    load_dotenv()
    db = VectorDBManager()
    
    # Casos de prueba específicos
    test_cases = [
        {
            'name': 'Restricción lácteos',
            'query': 'alternativas sin lácteos',
            'expected_sections': ['nutricion', 'planes']
        },
        {
            'name': 'Suplementación',
            'query': 'suplementación proteína creatina',
            'expected_sections': ['suplementacion', 'nutricion']
        },
        {
            'name': 'Método base',
            'query': 'método tres días y carga',
            'expected_sections': ['metodologia']
        },
        {
            'name': 'Plan pérdida grasa',
            'query': 'plan alimentación pérdida de grasa',
            'expected_sections': ['nutricion', 'planes']
        }
    ]
    
    print("\n=== Test de Queries Específicas ===")
    
    for case in test_cases:
        print(f"\n📌 Probando: {case['name']}")
        print(f"Query: '{case['query']}'")
        print(f"Secciones esperadas: {case['expected_sections']}")
        
        try:
            results = db.search_knowledge(
                query=case['query'],
                top_k=2,
                threshold=0.5
            )
            
            if results:
                print(f"\n✅ Encontrados {len(results)} resultados:")
                for i, result in enumerate(results, 1):
                    print(f"\nResultado {i}:")
                    print(f"• Score: {result['score']:.3f}")
                    print(f"• Sección: {result['section']}")
                    print(f"• Tags: {result['tags']}")
                    print(f"• Texto: {result['text'][:150]}...")
                    
                # Verificar secciones
                found_sections = set(r['section'] for r in results)
                expected = set(case['expected_sections'])
                if found_sections.intersection(expected):
                    print(f"\n✓ Secciones correctas encontradas")
                else:
                    print(f"\n⚠️ No se encontraron todas las secciones esperadas")
                    print(f"Esperadas: {expected}")
                    print(f"Encontradas: {found_sections}")
            else:
                print("❌ Sin resultados")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("\n=== Fin del Test ===")

if __name__ == "__main__":
    test_specific_queries() 