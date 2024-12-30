from vector_db import VectorDBManager
from dotenv import load_dotenv

def test_specific_queries():
    load_dotenv()
    db = VectorDBManager()
    
    # Queries específicas para probar
    specific_queries = [
        "método tres días y carga pérdida de grasa",
        "nutrición musculación",
        "proteínas para hipertrofia",
        "plan alimentación definición"
    ]
    
    for query in specific_queries:
        print(f"\nTesteando: {query}")
        results = db.search_knowledge(query, top_k=1, threshold=0.1)
        if results:
            print(f"Mejor match (score: {results[0]['score']}):")
            print(results[0]['text'][:200])
        else:
            print("Sin resultados")

if __name__ == "__main__":
    test_specific_queries() 