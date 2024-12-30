from vector_db import VectorDBManager
from dotenv import load_dotenv

def main():
    load_dotenv()
    db = VectorDBManager()
    db.test_search()

if __name__ == "__main__":
    main() 