"""
title: Weaviate VectorDb/Hybrid Retriever Pipeline
author: jellz77
date: 2024-06-03
version: 1.0
license: MIT
description: A pipeline for retrieving relevant information from a knowledge base using the Langchain and Weaviate.
requirements: langchain-community langchain weaviate-client langchain-core
"""
import logging
from typing import List, Union, Generator, Iterator
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.retrievers.weaviate_hybrid_search import WeaviateHybridSearchRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.chat_models import ChatOllama
import weaviate
from weaviate.classes.config import Configure
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self):        
        self.retriever = None
        self.client = None
        self.weaviate_client = None
        self.llm = None
    async def on_startup(self):      
        
        #index_name = "Pipeline_testa"
        index_name="Pipeline_testa"    

        self._connect_to_client()
        self._delete_and_add_collections(index_name)
        self._setup_retriever(index_name)
        self._ingest_docs("/Users/liamstone/Downloads/SCCHS Notes") #you can change this to the openwebui docs folder if you just want to iterate through those docs...this is just a local test 

        

    def _connect_to_client(self):
        """
        Connect to the Weaviate and Ollama clients.
        """
        try:
            #if you don't have weaviate running in docker, run the below...this also assumes you have nomic-embed-text downloaded and you're running ollama 
            #docker run -p 8081:8080 -p 50051:50051 -e ENABLE_MODULES=text2vec-ollama cr.weaviate.io/semitechnologies/weaviate:1.25.1
            self.client = weaviate.Client("http://localhost:8081")#connection
            self.weaviate_client = weaviate.connect_to_local("localhost", "8081")#client
            logger.info("Connection to Weaviate successful!")
            self.llm = ChatOllama(model="jonphi")
            logger.info("Connection to Ollama successful")
        except Exception as e:
            logger.error(f"Error connecting to clients: {e}")

    def _delete_and_add_collections(self, index_name: str):
        """
        Delete existing collections and add new ones.
        
        Parameters:
        - index_name (str): The name of the index to create.
        """
        try:
            self.weaviate_client.collections.delete_all()
            self.weaviate_client.collections.create(
                index_name,
                vectorizer_config=Configure.Vectorizer.text2vec_ollama(
                    model="nomic-embed-text",
                    api_endpoint="http://host.docker.internal:11434", #change to localhost if you have ollama running outside of docker 
                )
            )
            logger.info(f"Collection {index_name} successfully created!")
        except Exception as e:
            logger.error(f"Error managing collections: {e}")

    def _setup_retriever(self, index_name: str):
        """
        Set up the retriever with the given index name.
        
        Parameters:
        - index_name (str): The name of the index to use for the retriever.
        """
        try:
            self.retriever = WeaviateHybridSearchRetriever(
                client=self.client,
                index_name=index_name,
                text_key="text",
                attributes=[],
                create_schema_if_missing=True,
                k=4
            )
            logger.info("Retriever setup")#hi
        except Exception as e:
            logger.error(f"Error setting up retriever: {e}")

    def _ingest_docs(self, directory_path: str):
        """
        Ingest documents from the specified directory path.
        
        Parameters:
        - directory_path (str): The path to the directory containing documents to ingest.
        """
        try:
            documents = DirectoryLoader(directory_path).load()
            for d in documents:
                loader = TextLoader(d.metadata.get('source'))
                documents = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100) #horrible cpu and just want to focus on keyword search results
                docs = text_splitter.split_documents(documents)
                self.retriever.add_documents(docs)
                logger.info(f"{d.metadata.get('source')} has been added")
            logger.info("Retriever add complete")
        except Exception as e:
            logger.error(f"Error ingesting documents: {e}")

        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        pass    

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:        
        print(user_message)
        print(messages)
        after_rag_template = """
        You are to only answer based on the data found between the <context> tags below.
        <context>
        {context}
        </context>
        Question: {question}
        """
        after_rag_prompt = ChatPromptTemplate.from_template(after_rag_template)
        after_rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | after_rag_prompt
            | self.llm
            | StrOutputParser()
        )
        response = after_rag_chain.invoke(user_message)

        return response

    
