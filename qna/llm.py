

import os
import redis 
from langchain.vectorstores.redis import Redis
from langchain.schema import Document
from langchain.llms.base import LLM
from langchain.embeddings.base import Embeddings
from typing import List
import time, os
from dotenv import load_dotenv
from genai.credentials import Credentials
from genai.model import Model
from genai.schemas import GenerateParams
from genai.extensions.langchain import LangChainInterface
from datasets import load_dataset

load_dotenv()
api_key = os.getenv("GENAI_KEY", None) 
api_url = os.getenv("GENAI_API", None)
creds = Credentials(api_key, api_endpoint=api_url)
params = GenerateParams(decoding_method="greedy")

# Env Vars and constants
CACHE_TYPE = os.getenv("CACHE_TYPE")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE", "openai")
OPENAI_COMPLETIONS_ENGINE = os.getenv("OPENAI_COMPLETIONS_ENGINE", "text-davinci-003")
INDEX_NAME = "wiki"


def get_llm() -> LLM:
    langchain_model = LangChainInterface(model="google/flan-t5-xxl", params=params, credentials=creds)

def get_embeddings() -> Embeddings:
    # TODO - work around rate limits for embedding providers
    from langchain.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return embeddings

# def get_cache():
#     # construct cache implementation based on env var
#     if CACHE_TYPE == "semantic":
#         from langchain.cache import RedisSemanticCache
#         print("Using semantic cache")
#         embeddings = get_embeddings()
#         return RedisSemanticCache(
#             redis_url=REDIS_URL,
#             embedding=embeddings,
#             score_threshold=0.2
#         )
#     elif CACHE_TYPE == "standard":
#         from redis import Redis
#         from langchain.cache import RedisCache
#         return RedisCache(Redis.from_url(REDIS_URL))
#     return None

def get_documents() -> List[Document]:
    docs = load_dataset("Cohere/wikipedia-22-12-simple-embeddings", split="train")
    redis_client = redis.from_url(REDIS_URL)
    pipe = redis_client.pipeline()
 
    index = 0
    for doc in docs:
        pipe.json().set(f"wiki:{doc['id']}", '$', doc)
        if index % 500 == 0:
            pipe.execute()
        index += 1
    
    pipe.execute()
    # import pandas as pd
    # # Load and prepare wikipedia documents
    # datasource = pd.read_csv(
    #     "https://cdn.openai.com/API/examples/data/olympics_sections_text.csv"
    # ).to_dict("records")
    # # Create documents
    # documents = [
    #     Document(
    #         page_content=doc["content"],
    #         metadata={
    #             "title": doc["title"],
    #             "heading": doc["heading"],
    #             "tokens": doc["tokens"]
    #         }
    #     ) for doc in datasource
    # ]
    # return documents

def create_vectorstore() -> Redis:
    """Create the Redis vectorstore."""

    embeddings = get_embeddings()

    try:
        vectorstore = Redis.from_existing_index(
            embedding=embeddings,
            index_name=INDEX_NAME,
            redis_url=REDIS_URL
        )
        return vectorstore
    except:
        pass

    # Load Redis with documents
    documents = get_documents()
    vectorstore = Redis.from_documents(
        documents=documents,
        embedding=embeddings,
        index_name=INDEX_NAME,
        redis_url=REDIS_URL
    )
    return vectorstore

def make_qna_chain(query):
    """Create the QA chain."""
    # from langchain.prompts import PromptTemplate
    from langchain.chains import RetrievalQA

    # Create Redis Vector DB
    redis = create_vectorstore()
    # Create retreival QnA Chain
    chain = RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",
        retriever=redis.as_retriever()
    )
    answer=chain.run(query)
    return answer