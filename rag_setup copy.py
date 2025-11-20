import json
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class RAGSetup:
    def __init__(self):
        """ChromaDB va OpenAI ni sozlash"""
        self.client = chromadb.Client(Settings(
            persist_directory="./chroma_db"
        ))
        
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        try:
            self.collection = self.client.get_collection("knowledge_base")
            print("Mavjud collection topildi")
        except:
            self.collection = self.client.create_collection(
                name="knowledge_base",
                metadata={"description": "RAG uchun ma'lumotlar bazasi"}
            )
            print("Yangi collection yaratildi")
    
    def get_embedding(self, text):
        """Matn uchun embedding olish"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def load_data_from_json(self, json_file="data.json"):
        """JSON fayldan ma'lumotlarni yuklash va ChromaDB ga saqlash"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = []
            metadatas = []
            ids = []
            embeddings = []
            
            for doc in data['documents']:
                department_name = doc['Departament nomi']
                index = doc['Index']
                floor = doc['Qavat']
                room = doc['Xona']
                phone_number = doc['Ichki raqam']

                full_text = f"Departament nomi: {department_name}\nIndex: {index}\nQavat: {floor}\nXona: {room}\nIchki raqam: {phone_number}"
                
                documents.append(full_text)
                metadatas.append({
                    "Departament nomi": department_name,
                    "Index": index,
                    "Qavat": floor,
                    "Xona": room,
                    "Ichki raqam": phone_number
                })
                ids.append(index)
                
                embedding = self.get_embedding(full_text)
                embeddings.append(embedding)
                
                print(f"Chunk yaratildi: {department_name} - {index}")
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            print(f"\n✅ Jami {len(documents)} ta chunk ChromaDB ga saqlandi!")
            return True
            
        except Exception as e:
            print(f"❌ Xatolik: {e}")
            return False
    
    def search(self, query, n_results=3):
        """So'rov bo'yicha qidirish"""
        query_embedding = self.get_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return results

if __name__ == "__main__":
    print("🚀 RAG tizimini sozlash boshlandi...\n")
    
    rag = RAGSetup()
    
    rag.load_data_from_json("data.json")
    
    print("\n📊 Test qidiruv:")
    test_query = "Axborot texnologiyalar departamenti"
    results = rag.search(test_query)
    
    print(f"\nSo'rov: {test_query}")
    print(f"Topilgan natijalar soni: {len(results['documents'][0])}")
    for i, doc in enumerate(results['documents'][0]):
        print(f"\n{i+1}. {doc[:100]}...")
    
    print("\n✅ RAG tizimi tayyor!")