import os
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import time

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
                metric='cosine',
                spec={
                    "serverless": {
                        "cloud": "aws",
                        "region": "us-east-1"
                    }
                }
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
        
        # Agregar metadata más rica
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'chunk_id': i,
                'source': 'libro_nutricion',
                'type': 'nutrition_knowledge'
            })
        
        return chunks
    
    def create_embeddings_and_upload(self, chunks, start_index):
        """
        Crea embeddings y los sube a Pinecone con IDs únicos basados en el índice global
        
        Args:
            chunks: Lista de chunks a procesar
            start_index: Índice inicial para generar IDs únicos
        """
        try:
            total_vectors = 0
            
            # Crear embeddings para todos los chunks del batch
            texts = [chunk.page_content for chunk in chunks]
            print(f"Generando embeddings para {len(texts)} textos...")
            embeddings = self.embeddings.embed_documents(texts)
            
            # Preparar vectores con IDs únicos basados en el índice global
            vectors = []
            for j, (text, embedding) in enumerate(zip(texts, embeddings)):
                chunk = chunks[j]
                vector_id = f"chunk_{start_index + j}"  # ID único basado en el índice global
                metadata = {
                    'text': text,
                    'page': chunk.metadata.get('page', 0),
                    'chunk_id': vector_id,
                    'source': 'libro_nutricion',
                    'type': 'nutrition_knowledge',
                    'tags': self._extract_tags(text),
                    'section': self._identify_section(text),
                    'global_index': start_index + j
                }
                vectors.append((
                    vector_id,
                    embedding,
                    metadata
                ))
            
            # Subir vectores a Pinecone
            print(f"Subiendo {len(vectors)} vectores...")
            self.index.upsert(vectors=vectors)
            total_vectors = len(vectors)
            
            # Verificar la subida
            stats = self.index.describe_index_stats()
            print(f"Vectores en índice después de la subida: {stats.total_vector_count}")
            
            return total_vectors
            
        except Exception as e:
            print(f"Error en create_embeddings_and_upload: {str(e)}")
            return 0

    def _extract_tags(self, text):
        """Extrae tags relevantes del texto"""
        tags = []
        keywords = {
            'tres_dias_y_carga': ['tres días y carga', 'método', 'carga'],
            'nutricion': ['nutrición', 'alimentación', 'dieta'],
            'objetivos': ['pérdida de grasa', 'ganancia muscular', 'definición'],
            'entrenamiento': ['ejercicio', 'entrenamiento', 'actividad física'],
            'suplementacion': ['suplementos', 'suplementación', 'vitaminas'],
            'macros': ['proteínas', 'carbohidratos', 'grasas', 'macronutrientes'],
            'planificacion': ['plan', 'menú', 'comidas', 'recetas']
        }
        
        for category, words in keywords.items():
            if any(word.lower() in text.lower() for word in words):
                tags.append(category)
        
        return tags

    def _identify_section(self, text):
        """Identifica la sección del libro basada en el contenido"""
        sections = {
            'introduccion': ['introducción', 'prólogo', 'sobre el autor'],
            'metodologia': ['método', 'tres días y carga', 'cómo funciona'],
            'nutricion': ['nutrición', 'alimentación', 'macronutrientes'],
            'planes': ['plan', 'ejemplo', 'menú', 'recetas'],
            'suplementacion': ['suplementos', 'suplementación', 'vitaminas'],
            'entrenamiento': ['ejercicio', 'entrenamiento', 'actividad física'],
            'objetivos': ['pérdida de grasa', 'ganancia muscular', 'definición']
        }
        
        for section, keywords in sections.items():
            if any(keyword.lower() in text.lower() for keyword in keywords):
                return section
        
        return 'general'

    def search_knowledge(self, query, top_k=5, threshold=0.5):
        try:
            query = query.lower().strip()
            
            # Palabras clave específicas por tipo de búsqueda
            query_keywords = {
                'sin lácteos': {
                    'required_words': ['alternativas', 'sin lácteos', 'vegetal'],
                    'excluded_words': ['whey', 'suero de leche', 'lácteos'],
                    'min_matches': 1
                },
                'suplementación': {
                    'required_words': ['suplemento', 'dosis', 'timing'],
                    'excluded_words': ['metodologia', 'tres días'],
                    'min_matches': 1
                }
            }
            
            # Identificar tipo de query
            active_keywords = None
            for key, keywords in query_keywords.items():
                if key in query:
                    active_keywords = keywords
                    break
            
            # Realizar búsqueda
            query_embedding = self.embeddings.embed_query(query)
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k * 3,  # Aumentamos para tener más candidatos
                include_metadata=True
            )
            
            filtered_results = []
            for match in results.matches:
                if match.score < threshold:
                    continue
                    
                text = match.metadata.get('text', '').lower()
                section = match.metadata.get('section', '')
                
                # Aplicar filtros específicos si hay keywords activos
                if active_keywords:
                    # Verificar palabras requeridas
                    required_matches = sum(1 for word in active_keywords['required_words'] 
                                        if word in text)
                    # Verificar palabras excluidas
                    has_excluded = any(word in text for word in active_keywords['excluded_words'])
                    
                    if required_matches < active_keywords['min_matches'] or has_excluded:
                        continue
                
                # Calcular boost
                boost = 0.0
                if active_keywords:
                    boost += 0.1 * required_matches
                if query in text:
                    boost += 0.1
                    
                result = {
                    'text': match.metadata.get('text', ''),
                    'score': match.score + boost,
                    'page': match.metadata.get('page', 0),
                    'section': section,
                    'tags': match.metadata.get('tags', []),
                    'matches': required_matches if active_keywords else 0
                }
                filtered_results.append(result)
            
            # Ordenar y diversificar resultados
            unique_results = []
            seen_texts = set()
            sections_count = {}
            
            for result in sorted(filtered_results, key=lambda x: (x['score'], x['matches']), reverse=True):
                text_snippet = result['text'][:100]
                section = result['section']
                
                if (text_snippet not in seen_texts and 
                    sections_count.get(section, 0) < 2):  # máximo 2 por sección
                    unique_results.append(result)
                    seen_texts.add(text_snippet)
                    sections_count[section] = sections_count.get(section, 0) + 1
                    
                    if len(unique_results) >= top_k:
                        break
            
            return unique_results
            
        except Exception as e:
            print(f"Error en search_knowledge: {str(e)}")
            raise

    def test_search(self):
        """
        Método de prueba para verificar la funcionalidad de búsqueda
        """
        test_queries = [
            "nutrición básica",
            "método tres días y carga",
            "proteínas y ejercicio",
            "plan alimentación",
            "suplementación deportiva"
        ]
        
        print("\n=== Test de Búsqueda ===")
        print(f"Total vectores en índice: {self.index.describe_index_stats().total_vector_count}")
        
        for query in test_queries:
            print(f"\nProbando query: '{query}'")
            try:
                results = self.search_knowledge(
                    query=query,
                    top_k=1,
                    threshold=0.1  # Umbral bajo para pruebas
                )
                
                if results:
                    print(f"✓ Encontrado - Score: {results[0]['score']}")
                    print(f"Texto: {results[0]['text'][:100]}...")
                else:
                    print("✗ Sin resultados")
                    
            except Exception as e:
                print(f"Error: {str(e)}")

    def query_book_context(self, query: str, n_results: int = 5) -> str:
        """
        Consulta el contexto del libro basado en una query
        
        Args:
            query (str): Consulta para buscar en el libro
            n_results (int): Número de resultados a retornar
            
        Returns:
            str: Contexto relevante del libro
        """
        try:
            # Realizar la búsqueda usando el método existente
            results = self.search_knowledge(
                query=query,
                top_k=n_results,
                threshold=0.5
            )
            
            # Formatear los resultados
            context = []
            for result in results:
                context.append(f"• {result['text']}")
            
            # Unir todo el contexto
            return "\n\n".join(context)
            
        except Exception as e:
            print(f"Error en query_book_context: {str(e)}")
            return "Base de conocimientos no disponible."
