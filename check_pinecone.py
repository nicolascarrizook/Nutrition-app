from vector_db import VectorDBManager
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader
import time

def reindex_book():
    load_dotenv()
    db = VectorDBManager()
    
    # Eliminar índice existente
    print("Eliminando índice existente si existe...")
    if db.index_name in db.pc.list_indexes().names():
        db.pc.delete_index(db.index_name)
        print("Índice eliminado")
        # Esperar a que el índice se elimine completamente
        time.sleep(5)
    
    # Crear nuevo índice
    print("Creando nuevo índice...")
    db.ensure_index_exists()
    # Esperar a que el índice esté listo
    time.sleep(5)
    
    # Procesar el libro
    pdf_path = os.path.join('data', 'libro_nutricion.pdf')
    print(f"\nProcesando PDF: {pdf_path}")
    
    # Verificar el PDF original
    with open(pdf_path, 'rb') as file:
        pdf = PdfReader(file)
        total_pages = len(pdf.pages)
        print(f"\nInformación del PDF original:")
        print(f"Total de páginas: {total_pages}")
    
    # Procesar en chunks
    chunks = db.process_pdf(pdf_path)
    total_chunks = len(chunks)
    print(f"\nProcesamiento del PDF:")
    print(f"Total de chunks generados: {total_chunks}")
    
    # Subir chunks en batches
    print("\nSubiendo chunks a Pinecone...")
    batch_size = 50
    total_uploaded = 0
    
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        print(f"\nProcesando batch {(i//batch_size) + 1} de {(total_chunks-1)//batch_size + 1}")
        
        try:
            # Pasar el índice inicial para este batch
            vectors_uploaded = db.create_embeddings_and_upload(batch, start_index=i)
            total_uploaded += vectors_uploaded
            
            print(f"Progreso: {total_uploaded}/{total_chunks} chunks")
            time.sleep(2)  # Pequeña pausa entre batches
            
        except Exception as e:
            print(f"Error en batch: {str(e)}")
    
    # Verificación final
    time.sleep(5)
    stats = db.index.describe_index_stats()
    print(f"\nVerificación final:")
    print(f"Total de vectores en Pinecone: {stats.total_vector_count}")
    print(f"Total de chunks procesados: {total_chunks}")
    
    if stats.total_vector_count < total_chunks:
        print(f"\n⚠️ ADVERTENCIA: Faltan vectores")
        print(f"Esperados: {total_chunks}")
        print(f"Subidos: {stats.total_vector_count}")
    else:
        print("\n✅ Todos los chunks fueron subidos exitosamente")

if __name__ == "__main__":
    reindex_book()