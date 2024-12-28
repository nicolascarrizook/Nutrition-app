import os
from vector_db import VectorDBManager
from dotenv import load_dotenv

def initialize_knowledge_base():
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar que tenemos las API keys
    if not os.getenv("PINECONE_API_KEY"):
        raise ValueError("No se encontró PINECONE_API_KEY en las variables de entorno")
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("No se encontró OPENAI_API_KEY en las variables de entorno")
    
    # Crear instancia del manager
    db_manager = VectorDBManager()
    
    # Procesar el libro de nutrición
    pdf_path = os.path.join('data', 'libro_nutricion.pdf')
    
    print("Procesando PDF...")
    chunks = db_manager.process_pdf(pdf_path)
    
    print("Creando embeddings y subiendo a Pinecone...")
    db_manager.create_embeddings_and_upload(chunks)
    
    print("Base de conocimientos inicializada exitosamente!")

if __name__ == "__main__":
    initialize_knowledge_base()
