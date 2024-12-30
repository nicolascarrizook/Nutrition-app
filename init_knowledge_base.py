import os
from vector_db import VectorDBManager
from dotenv import load_dotenv

def initialize_knowledge_base():
    # Cargar variables de entorno
    load_dotenv()
    
    # Crear instancia del manager
    db_manager = VectorDBManager()
    
    # Procesar el libro de nutrición
    pdf_path = os.path.join('data', 'libro_nutricion.pdf')
    
    print("\nIniciando proceso de indexación...")
    print(f"Archivo: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"Error: No se encuentra el archivo en {pdf_path}")
        return
    
    print("\nProcesando PDF...")
    chunks = db_manager.process_pdf(pdf_path)
    print(f"Se generaron {len(chunks)} chunks del libro")
    
    print("\nMuestra de los primeros chunks:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(chunk.page_content[:200], "...")
    
    print("\nCreando embeddings y subiendo a Pinecone...")
    try:
        # Eliminar índice existente si existe
        if db_manager.index_name in db_manager.pc.list_indexes().names():
            db_manager.pc.delete_index(db_manager.index_name)
        
        # Crear nuevo índice
        db_manager.ensure_index_exists()
        
        # Procesar y subir el contenido
        chunks = db_manager.process_pdf(pdf_path)
        db_manager.create_embeddings_and_upload(chunks)
        
        # Verificar la carga
        stats = db_manager.index.describe_index_stats()
        print(f"\nVerificación final:")
        print(f"Total de vectores en Pinecone: {stats.total_vector_count}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    initialize_knowledge_base()
