import os
import requests
import chromadb
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains import LLMMathChain
from langchain_community.llms import Ollama

# 1. RAG Tool for R&D
# class RAGSearchInput(BaseModel):
#     query: str = Field(..., description="The component or material to search for.")

class ComponentRAGTool(BaseTool):
    name: str = "Component Catalog Search"
    description: str = "Search the local database for components. Action Input must be a single simple string, like 'solar panel' or 'battery'."
    
    # args_schema line is deleted entirely
    
    def _run(self, query: str) -> str:
        try:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            client = chromadb.PersistentClient(path="/app/chroma_db")
            collection = client.get_collection(name="rd_materials")
            query_embedding = embeddings.embed_query(query)
            results = collection.query(query_embeddings=[query_embedding], n_results=3)
            if not results['documents'][0]:
                return "No matching components found."
            return "\n".join(results['documents'][0])
        except Exception as e:
            return f"Action Input Error: {str(e)}"
    # name: str = "Component Catalog Search"
    # description: str = "Search the local vector database for real-world electronic components and materials."
    # args_schema: type[BaseModel] = RAGSearchInput

    # def _run(self, query: str) -> str:
    #     try:
    #         embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    #         client = chromadb.PersistentClient(path="/app/chroma_db")
    #         collection = client.get_collection(name="rd_materials") # Ensure the Logistics tool uses "mfg_logistics"
    #         query_embedding = embeddings.embed_query(query)
    #         results = collection.query(query_embeddings=[query_embedding], n_results=3)
    #         if not results['documents'][0]:
    #             return "No matching components found."
    #         return "\n".join(results['documents'][0])
    #     except Exception as e:
    #         return f"Action Input Error: Database connection failed. Details: {str(e)}"
        
# 2. RAG Tool for Logistics
# class LogisticsSearchInput(BaseModel):
#     query: str = Field(..., description="The shipping or logistics rule to search for.")

class LogisticsRAGTool(BaseTool):
    name: str = "Logistics and Shipping Search"
    description: str = "Search the local vector database for manufacturing lead times and shipping risks."
    

    def _run(self, query: str) -> str:
        try:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            client = chromadb.PersistentClient(path="/app/chroma_db")
            collection = client.get_collection(name="rd_materials") # Ensure the Logistics tool uses "mfg_logistics"
            query_embedding = embeddings.embed_query(query)
            results = collection.query(query_embeddings=[query_embedding], n_results=3)
            if not results['documents'][0]:
                return "No matching components found."
            return "\n".join(results['documents'][0])
        except Exception as e:
            return f"Action Input Error: Database connection failed. Details: {str(e)}"
        # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        # client = chromadb.PersistentClient(path="/app/chroma_db")
        # collection = client.get_collection(name="mfg_logistics")
        # query_embedding = embeddings.embed_query(query)
        # results = collection.query(query_embeddings=[query_embedding], n_results=3)
        # if not results['documents'][0]:
        #     return "No logistics data found."
        # return "\n".join(results['documents'][0])

# 3. Math Tool for Manufacturing
# class MathInput(BaseModel):
#     equation: str = Field(..., description="The mathematical equation to calculate.")

class ExactMathTool(BaseTool):
    name: str = "Exact Calculator"
    description: str = "Executes precise mathematical arithmetic. Always use this for budget and margin calculations."
    

    def _run(self, equation: str) -> str:
        llm = Ollama(model="llama3:8b", base_url="[http://host.docker.internal:11434](http://host.docker.internal:11434)")
        math_chain = LLMMathChain.from_llm(llm=llm)
        try:
            return math_chain.run(equation)
        except Exception as e:
            return f"Action Input Error: Provide only numeric equations. Details: {str(e)}"

# 4. Web Search Tool for Marketing
# class WebSearchInput(BaseModel):
#     query: str = Field(..., description="The market trend or competitor pricing to search for.")

class MarketSearchTool(BaseTool):
    name: str = "Market Web Search"
    description: str = "Search the live internet for current competitor pricing."
    

    def _run(self, query: str) -> str:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return "Search API failed: Missing SERPER_API_KEY. Fall back to offline market heuristics."
        url = "https://google.serper.dev/search"
        payload = {"q": query}
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        try:
            response = requests.post(url, json=payload, headers=headers)
            results = response.json().get("organic", [])
            return "\n".join([f"Title: {r.get('title')} | Snippet: {r.get('snippet')}" for r in results[:3]])
        except Exception:
            return "Search API failed. Fall back to offline market heuristics."