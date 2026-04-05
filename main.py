import faiss
import numpy as np
dimension = 384
index = faiss.IndexFlatL2(dimension)
doc_mapping = []
from fastapi import FastAPI
from jose import jwt 
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
SECRET_KEY = "mysrcretkey"
ALGORITHM="HS256"

def get_current_user(token:str):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    
        return payload["username"]
    except:
        return None

app=FastAPI()
@app.get("/")
def home():
    return { "message":"hello,Financial api is running"}

users=[]
roles = []
@app.post("/auth/register")
def register(username:str,password:str):
    user={
        "id":len(users)+1,
        "username":username,
        "password":password,
        "role":None
    }
    users.append(user)
    return {"message":"user registered"}

@app.post("/auth/login")
def login(username: str, password: str):
    for user in users:
        if user["username"] == username and user["password"] == password:
            token = jwt.encode({"username": username},SECRET_KEY,algorithm=ALGORITHM)
            return {
                "access_token": token,
                "message": "login successful"
            }

    return {"message": "invalid credentials"}   

@app.post("/roles/create")
def create_role(name:str):
    if name=="Admin":
        permissions=["upload","view","delete","search"]
    elif name=="Analyst":
        permissions=["upload","view","search"]
    elif name=="Client":
        permissions=["view"]
    elif name=="Auditor":
        permissions=["view","search"]
    else :
        permissions=[]
    role={
        "name":name,
        "permissions":permissions
    }
    roles.append(role)
    return {"message":"role created"}

@app.post("/users/assign-role")
def assign_role(user_id:int,role_name:str):
    for user in users:
        if user["id"]==user_id:
            for role in roles:
                if role["name"]==role_name:
                    user["role"]=role_name
                    return {"message":"role assigned"}
            return {"message":"role not found"}
    return {"message":"user not found"}

documents=[]
@app.post("/documents/upload")
def upload_document(title:str,company_name:str,document_type:str,token:str,created_at:str):
    username = get_current_user(token)

    if username is None:
        return {"message": "invalid token"}
    for user in users:
        if user["username"]==username:
            role_name=user["role"]
            for role in roles:
                if role["name"]==role_name:
                    if "upload" in role["permissions"]:
                         document={
                            "id":len(documents) + 1,
                            "title":title,
                            "company_name":company_name,
                            "document_type":document_type,
                            "uploaded_by":username,
                            "created_at":"2026-04-05"
                         }
                         documents.append(document)
                         text=f"{title} is a {document_type} for {company_name}"
                         embedding= model.encode(text)
                         embedding= np.array([embedding]).astype("float32")
                         index.add(embedding)
                         doc_mapping.append(document)
                         return {"message": " Uploaded"}
                    else:
                        return {"message":"permission denied"}
            return{"message":" role not found"}
    return{"message":"user not found"}

@app.get("/documents")
def get_documents():
    return documents


@app.get("/documents/search")
def search_documents(company_name:str):
    result=[]
    for doc in documents:
        if doc["company_name"]==company_name:
            result.append(doc)
    return result  

@app.get("/documents/{doc_id}")
def get_document(doc_id:int):
    for doc in documents:
        if doc["id"]==doc_id:
            return doc
    return {"message": "document not found"} 

 

@app.delete("/documents/{doc_id}")
def delete_document(doc_id:int,token:str):
    username = get_current_user(token)

    if username is None:
        return {"message": "invalid token"}
    for user in users:
        if user["username"]==username:
            role_name=user["role"]
            for role in roles:
                if role["name"]==role_name:
                    if "delete" in role["permissions"]:


                        for doc in documents:
                            if doc["id"]==doc_id:
                                documents.remove(doc)
                                return {"message":"Document deleted"}
                        
                        return {"message":"document not found"}
                    else:
                        return{"message":"permission denied"}
            return {"message":"role not found"}        
    return {"message":"user not found"}

@app.get("/users")
def get_users():
    return users

@app.get("/user/{user_id}/roles")
def get_user_role(user_id:int):
    for user in users:
        if user["id"]==user_id:
            return {"role":user["role"]}
    return {"message":"user not found"}

@app.get("/user/{user_id}/permissions")
def permissions(user_id:int):
    for user in users:
        if user["id"]==user_id:
            role_name=user["role"]
            for role in roles:
                if role["name"]==role_name:
                    return {"permissions":role["permissions"]}
            return {"message":"role not found"}
    return {"message":"user not found"}


@app.get("/rag/search")
def rag_search(query:str):
    query_vector = model.encode(query)
    query_vector = np.array([query_vector]).astype("float32")
    D,I = index.search(query_vector,k=5)
    results = []
    for i in I[0]:
        if i < len(doc_mapping):
            results.append(doc_mapping[i])
    return results