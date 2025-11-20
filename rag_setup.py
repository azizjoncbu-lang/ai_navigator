import json
import chromadb
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class RAGSetup:
    def __init__(self):
        """ChromaDB va OpenAI ni sozlash"""
        os.makedirs("./chroma_db", exist_ok=True)
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Eski collectionni o'chirish
        try:
            self.client.delete_collection("knowledge_base")
            print("🗑️ Eski collection o'chirildi")
        except:
            pass
        
        # Yangi collection yaratish
        self.collection = self.client.create_collection(
            name="knowledge_base",
            metadata={"description": "Departamentlar va boshqarmalar ma'lumotlari"}
        )
        print("✅ Yangi collection yaratildi")
    
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
            
            # Har bir departament uchun
            for dept in data['departments']:
                dept_id = dept['id']
                dept_name = dept['name']
                dept_index = dept['index']
                dept_floor = dept.get('floor', '')
                dept_room = dept.get('room', '')
                dept_phone = dept['phone']
                dept_desc = dept.get('description', '')
                has_subdivisions = dept.get('has_subdivisions', False)
                
                # Departament ma'lumotini saqlash
                if has_subdivisions:
                    # Agar boshqarmalar bo'lsa
                    subdiv_names = [s['name'] for s in dept.get('subdivisions', [])]
                    subdiv_list = "\n".join([f"  • {name}" for name in subdiv_names])
                    
                    dept_text = f"""Departament: {dept_name}
Index: {dept_index}
Manzil: {dept_floor}-qavat, {dept_room}-xona
Telefon: {dept_phone}
Tavsif: {dept_desc}

Bu departamentda quyidagi boshqarmalar mavjud:
{subdiv_list}"""
                else:
                    # Agar boshqarmalar bo'lmasa
                    dept_text = f"""Departament: {dept_name}
Index: {dept_index}
Manzil: {dept_floor}-qavat, {dept_room}-xona
Telefon: {dept_phone}
Tavsif: {dept_desc}

Bu departamentda alohida boshqarmalar yo'q."""
                
                documents.append(dept_text)
                metadatas.append({
                    "type": "department",
                    "id": dept_id,
                    "name": dept_name,
                    "index": dept_index,
                    "floor": dept_floor,
                    "room": dept_room,
                    "phone": dept_phone,
                    "has_subdivisions": has_subdivisions
                })
                ids.append(dept_id)
                
                embedding = self.get_embedding(dept_text)
                embeddings.append(embedding)
                
                print(f"📦 Departament saqlandi: {dept_name}")
                
                # Boshqarmalarni saqlash
                if has_subdivisions:
                    for subdiv in dept.get('subdivisions', []):
                        subdiv_id = subdiv['id']
                        subdiv_name = subdiv['name']
                        subdiv_desc = subdiv.get('description', '')
                        subdiv_floor = subdiv.get('floor', '')
                        subdiv_room = subdiv.get('room', '')
                        subdiv_phone = subdiv.get('phone', '')
                        subdiv_head = subdiv.get('head', '')
                        
                        subdiv_text = f"""Boshqarma: {subdiv_name}
Departament: {dept_name}
Tavsif: {subdiv_desc}
Manzil: {subdiv_floor}-qavat, {subdiv_room}-xona
Telefon: {subdiv_phone}
Rahbar: {subdiv_head}"""
                        
                        documents.append(subdiv_text)
                        metadatas.append({
                            "type": "subdivision",
                            "id": subdiv_id,
                            "name": subdiv_name,
                            "department_id": dept_id,
                            "department_name": dept_name,
                            "floor": subdiv_floor,
                            "room": subdiv_room,
                            "phone": subdiv_phone,
                            "head": subdiv_head
                        })
                        ids.append(subdiv_id)
                        
                        embedding = self.get_embedding(subdiv_text)
                        embeddings.append(embedding)
                        
                        print(f"   ├─ Boshqarma saqlandi: {subdiv_name}")
            
            # ChromaDB ga saqlash
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            print(f"\n✅ Jami {len(documents)} ta yozuv ChromaDB ga saqlandi!")
            print(f"   • Departamentlar: {len([m for m in metadatas if m['type'] == 'department'])}")
            print(f"   • Boshqarmalar: {len([m for m in metadatas if m['type'] == 'subdivision'])}")
            return True
            
        except Exception as e:
            print(f"❌ Xatolik: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query, n_results=5):
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
    
    # Ma'lumotlarni yuklash
    success = rag.load_data_from_json("data.json")
    
    if success:
        print("\n📊 Test qidiruv:")
        test_queries = [
            "Axborot texnologiyalari departamenti",
            "Pul kredit siyosati",
            "Yuridik departament"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"🔍 So'rov: {query}")
            results = rag.search(query, n_results=3)
            
            for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"\n{i+1}. [{meta['type'].upper()}] {meta['name']}")
                print(f"   {doc[:150]}...")
    
    print("\n✅ RAG tizimi tayyor!")