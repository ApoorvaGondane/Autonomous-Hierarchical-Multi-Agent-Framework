import pandas as pd
import yaml
import requests
import chromadb
from datasets import load_dataset
from langchain_community.document_loaders import DataFrameLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

def build_rag_databases():
    print("Initializing local embedding model (CPU-friendly)...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Initialize ChromaDB locally in the /chroma_db directory
    chroma_client = chromadb.PersistentClient(path="../chroma_db")
    rd_collection = chroma_client.get_or_create_collection(name="rd_materials")
    mfg_collection = chroma_client.get_or_create_collection(name="mfg_logistics")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

# ---------------------------------------------------------
    # 1. Ingest Octopart CPL (YAML) for the R&D Agent
    # ---------------------------------------------------------
    print("Fetching Octopart CPL Capacitors...")
    url = "https://raw.githubusercontent.com/octopart/CPL-Data/master/CPL%20for%20Production/Capacitors.yaml"
    response = requests.get(url)
    cpl_data = yaml.safe_load(response.text)
    
    rd_documents = []
    rd_ids = []
    
    doc_idx = 0
    for row in cpl_data.get("rows", []):
        specs = ", ".join([f"{k}: {v}" for k, v in row.get("extravals", {}).items()])
        for part in row.get("parts", []):
            mpn = part.get("mpn", "UNKNOWN")
            content = f"Part: {mpn}. Manufacturer: {part.get('manufacturer', 'Unknown')}. Specs: {specs}."
            
            rd_documents.append(content)
            # Guarantee uniqueness by appending the running index
            rd_ids.append(f"cpl_{doc_idx}_{mpn}")
            doc_idx += 1
            
    if rd_documents:
        # Use upsert instead of add to safely handle re-runs
        rd_collection.upsert(documents=rd_documents, ids=rd_ids)
        print(f"Embedded {len(rd_documents)} hardware components into 'rd_materials'.")

    # ---------------------------------------------------------
    # 2. Ingest DataCo Supply Chain Dataset for Mfg Agent
    # ---------------------------------------------------------
    print("Fetching Supply Chain logistics from Hugging Face...")
    
    # Use the official datasets library to correctly bypass the Git LFS pointer
    hf_dataset = load_dataset("alalfi/SupplyChainDataset", data_files="DataCoSupplyChainDataset1.csv", split="train")
    df = hf_dataset.to_pandas()
    # Add this line to see the exact column names:
    #print("Available columns:", df.columns.tolist())
    # Filter for the exact columns we need
    df = df[['Shipping_Mode', 'Days_for_shipping_(real)', 'Days_for_shipment_(scheduled)', 'Late_delivery_risk', 'Category_Name']]
    
    # Combine the features into a readable text chunk
    df['combined_text'] = df.apply(
        lambda row: f"Category: {row['Category_Name']} | Shipping_Mode: {row['Shipping_Mode']} | Real Days: {row['Days_for_shipping_(real)']} | Scheduled Days: {row['Days_for_shipment_(scheduled)']} | Risk Factor: {row['Late_delivery_risk']}", 
        axis=1
    )
    
    # Sample 1000 rows to save local compute time during this tutorial phase
    df_sample = df.sample(1000, random_state=42)
    loader = DataFrameLoader(df_sample, page_content_column="combined_text")
    mfg_docs = loader.load()
    
    # Chunk the tabular data to fit context windows
    mfg_chunks = text_splitter.split_documents(mfg_docs)
    
    mfg_texts = [chunk.page_content for chunk in mfg_chunks]
    mfg_ids = [f"logistics_{i}" for i in range(len(mfg_texts))]
    
    # Use upsert to handle re-runs smoothly without DuplicateID errors
    mfg_collection.upsert(documents=mfg_texts, ids=mfg_ids)
    
    print(f"Embedded {len(mfg_texts)} supply chain logistics rules into 'mfg_logistics'.")
    print("Database Pipeline Complete. Data is securely stored in /chroma_db.")

if __name__ == "__main__":
    build_rag_databases()