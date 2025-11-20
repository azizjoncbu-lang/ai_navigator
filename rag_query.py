import chromadb
from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()

class RAGQuery:
    def __init__(self):
        """RAG tizimini ishga tushirish"""
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        try:
            self.collection = self.client.get_collection("knowledge_base")
            print("✅ Knowledge base topildi!")
        except Exception as e:
            raise Exception(f"❌ Knowledge base topilmadi! Avval 'python rag_setup.py' ni ishga tushiring.\nXatolik: {e}")
        
        # data.json ni yuklash (departamentlar ro'yxati uchun)
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except:
            self.data = {"departments": []}
    
    def get_embedding(self, text):
        """Matn uchun embedding olish"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def search_departments(self, query, n_results=5):
        """Departamentlarni qidirish"""
        query_embedding = self.get_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"type": "department"}
        )
        
        return results
    
    def get_department_by_id(self, dept_id):
        """ID bo'yicha departamentni olish"""
        for dept in self.data['departments']:
            if dept['id'] == dept_id:
                return dept
        return None
    
    def get_department_info(self, dept_name):
        """Departament ma'lumotini olish"""
        query_embedding = self.get_embedding(dept_name)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
            where={"type": "department"}
        )
        
        if results['documents'][0]:
            metadata = results['metadatas'][0][0]
            dept = self.get_department_by_id(metadata['id'])
            return dept, results['documents'][0][0]
        
        return None, None
    
    def get_subdivision_info(self, subdiv_name):
        """Boshqarma ma'lumotini olish"""
        query_embedding = self.get_embedding(subdiv_name)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
            where={"type": "subdivision"}
        )
        
        if results['documents'][0]:
            return results['metadatas'][0][0], results['documents'][0][0]
        
        return None, None
    
    def generate_answer(self, query):
        """RAG yordamida javob generatsiya qilish"""
        try:
            query_embedding = self.get_embedding(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=3
            )
            
            if not results['documents'][0]:
                return "❌ Kechirasiz, bu mavzu bo'yicha ma'lumot topilmadi."
            
            context = "\n\n".join(results['documents'][0])
            
            prompt = f"""Siz Markaziy bank ma'lumot yordamchisisiz. Quyidagi kontekst asosida foydalanuvchi savoliga aniq, qisqa va tushunarli javob bering.

KONTEKST:
{context}

FOYDALANUVCHI SAVOLI: {query}

JAVOB BERISH QOIDALARI:
1. Faqat kontekstdagi ma'lumotlardan foydalaning
2. Departament yoki boshqarma nomi, telefon, manzilni aniq ko'rsating
3. Agar bir nechta variant bo'lsa, hammasini sanab o'ting
4. Javobni strukturali va o'qish oson qilib yozing
5. Emoji ishlatish mumkin (📞, 📍, 🏢)

JAVOB:"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Siz Markaziy bank ma'lumot yordamchisisiz. Aniq va qisqa javoblar berasiz."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            answer = response.choices[0].message.content
            return answer
            
        except Exception as e:
            return f"❌ Xatolik yuz berdi: {str(e)}"

if __name__ == "__main__":
    print("🔍 RAG Query Test\n")
    
    try:
        rag = RAGQuery()
        
        test_queries = [
            "Axborot texnologiyalari departamenti haqida ma'lumot",
            "Yuridik departament telefoni",
            "Pul kredit siyosati departamenti qayerda joylashgan",
        ]
        
        for query in test_queries:
            print(f"\n{'='*70}")
            print(f"❓ Savol: {query}")
            answer = rag.generate_answer(query)
            print(f"\n💡 Javob:\n{answer}")
        
    except Exception as e:
        print(f"❌ Xatolik: {e}")