from __future__ import annotations  # Add this for forward references
from dataclasses import dataclass, field
from query import  Query
from typing import List, Union
from datetime import datetime
import time  # Add this import
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
import os



@dataclass
class QueryState:
    query: Query
    retrieved_documents: List[dict] = field(default_factory=list)
    responses: List[dict] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)

@dataclass
class PolicyQueryClassifier(BaseNode):
    """Classifies policy queries into types (coverage, claims, excess, etc)"""
    
    async def run(self, ctx: GraphRunContext) -> Union[PolicyDocumentRetriever, End]:
        try:
            query_type = self.classify_query(ctx.state.query.question)
            ctx.state.query_type = query_type
            return PolicyDocumentRetriever()
        except Exception as e:
            return End(f"Error classifying query: {str(e)}")
    
    def classify_query(self, question: str) -> str:
        # Simple keyword-based classification for now
        question = question.lower()
        if "claim" in question:
            return "claims"
        elif "cover" in question or "covered" in question:
            return "coverage"
        elif "excess" in question:
            return "excess"
        return "general"

@dataclass
class PolicyDocumentRetriever(DocumentRetriever):
    """Policy-specific document retrieval with optimizations"""
    
    async def run(self, ctx: GraphRunContext) -> Union[PolicyResponseGenerator, End]:
        try:
            start_time = time.time()
            
            # Cache query classification results
            query_hash = hash(ctx.state.query.question)
            if hasattr(self, '_query_cache') and query_hash in self._query_cache:
                docs = self._query_cache[query_hash]
            else:
                docs = await self.retrieve_documents(
                    ctx.state.query.question,
                    ctx.state.query.context
                )
                if not hasattr(self, '_query_cache'):
                    self._query_cache = {}
                self._query_cache[query_hash] = docs

            retrieval_time = time.time() - start_time

            # Only process and log if documents were found
            if docs:
                ctx.state.retrieved_documents = docs
                ctx.state.retrieval_time = retrieval_time
                return PolicyResponseGenerator()

            return End("No relevant documents found. Please ensure documents are properly loaded in the correct directory.")

        except Exception as e:
            print(f"Error in PolicyDocumentRetriever: {str(e)}")
            return End(f"Error retrieving documents: {str(e)}")

@dataclass
class PolicyResponseGenerator(ResponseGenerator):
    """Policy-specific response preparation with streaming support"""

    # Initialise the llm with the prompt


    async def run(self, ctx: GraphRunContext) -> Union[ResponseValidator, End]:
        try:
            start_time = time.time()

            prompt_version = os.getenv("POLICY_PROMPT_VERSION")
            retriever_prompt = self.create_base_prompt(prompts[prompt_version]['base'], ctx.state.retrieved_documents)

            # Construct the full prompt
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=prompts[prompt_version]['system']),
                ChatMessage(role=MessageRole.TOOL, content=retriever_prompt),
                ChatMessage(role=MessageRole.USER, content=ctx.state.query.question),
            ]

            # No longer handle non-streaming vs streaming differently
            # Just prepare the context and return it
            generation_context = {
                "status": "ready",
                "prompt_context": {
                    "messages": messages,
                    "retrieved_docs": ctx.state.retrieved_documents,
                    "retrieval_time": getattr(ctx.state, 'retrieval_time', 0),
                    "start_time": start_time
                }
            }
            return End(generation_context)

        except Exception as e:
            print(f"Error in PolicyResponseGenerator: {str(e)}")
            return End(f"Error preparing response context: {str(e)}")

# Update graph with validator
policy_query_graph = Graph(
    nodes=[
        # PolicyQueryClassifier(),
        PolicyDocumentRetriever(),
        PolicyResponseGenerator(),
        ResponseValidator()
    ]
)
