from vector_db import VectorDBManager
from dotenv import load_dotenv

def verify_content_coverage():
    load_dotenv()
    db = VectorDBManager()
    
    # Aspectos críticos a verificar
    critical_aspects = {
        'metodologia': [
            'método tres días y carga',
            'distribución de comidas',
            'timing nutricional'
        ],
        'alimentos': [
            'alimentos permitidos',
            'porciones recomendadas',
            'alternativas alimentarias'
        ],
        'planes': [
            'ejemplo plan pérdida grasa',
            'ejemplo plan ganancia muscular',
            'ejemplo plan mantenimiento'
        ],
        'ajustes': [
            'ajustes por objetivo',
            'ajustes por restricciones',
            'ajustes por actividad'
        ]
    }
    
    coverage = {}
    
    print("\n=== Verificación de Cobertura de Contenido ===")
    
    for category, queries in critical_aspects.items():
        print(f"\n📌 Verificando {category}:")
        coverage[category] = []
        
        for query in queries:
            results = db.search_knowledge(query=query, top_k=1, threshold=0.5)
            
            if results:
                coverage[category].append({
                    'query': query,
                    'found': True,
                    'score': results[0]['score'],
                    'section': results[0]['section']
                })
                print(f"✅ {query}: Encontrado (score: {results[0]['score']:.2f})")
            else:
                coverage[category].append({
                    'query': query,
                    'found': False
                })
                print(f"❌ {query}: No encontrado")
    
    # Análisis de cobertura
    print("\n📊 Análisis de Cobertura:")
    for category, results in coverage.items():
        found = len([r for r in results if r['found']])
        total = len(results)
        percentage = (found / total) * 100
        print(f"\n{category}:")
        print(f"• Cobertura: {percentage:.1f}% ({found}/{total})")
        
        if percentage < 100:
            print("• Faltantes:")
            for result in results:
                if not result['found']:
                    print(f"  - {result['query']}")
    
    return coverage

if __name__ == "__main__":
    coverage = verify_content_coverage() 