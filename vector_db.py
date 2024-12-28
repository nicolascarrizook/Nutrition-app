import os
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

class VectorDBManager:
    def __init__(self):
        # Inicializar Pinecone con la nueva sintaxis
        self.pc = Pinecone(
            api_key=os.getenv("PINECONE_API_KEY")
        )
        
        # Inicializar OpenAI Embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Nombre del índice de Pinecone
        self.index_name = "tresdiasycarga"
        
        # Crear o conectar al índice
        self.ensure_index_exists()
    
    def ensure_index_exists(self):
        """Asegura que el índice existe, si no, lo crea"""
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # Dimensión para embeddings de OpenAI
                metric='cosine'
            )
        self.index = self.pc.Index(self.index_name)
    
    def process_pdf(self, pdf_path):
        """Procesa un PDF y lo divide en chunks"""
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        chunks = text_splitter.split_documents(pages)
        
        print(f"PDF procesado en {len(chunks)} chunks")
        return chunks
    
    def create_embeddings_and_upload(self, chunks):
        """Crea embeddings y los sube a Pinecone"""
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            texts = [chunk.page_content for chunk in batch]
            embeddings = self.embeddings.embed_documents(texts)
            
            vectors = []
            for j, (text, embedding) in enumerate(zip(texts, embeddings)):
                metadata = {
                    'text': text,
                    'page': chunks[i + j].metadata.get('page', 0)
                }
                vectors.append((
                    f"chunk_{i + j}",
                    embedding,
                    metadata
                ))
            
            self.index.upsert(vectors=vectors)
            
            print(f"Procesado batch {i//batch_size + 1}")

    def search_knowledge(self, query, top_k=3):
        """Busca conocimiento relevante basado en una consulta"""
        query_embedding = self.embeddings.embed_query(query)
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        relevant_texts = [
            match.metadata['text'] 
            for match in results.matches
        ]
        
        return relevant_texts
