import json
from botbuilder.core import ActivityHandler, TurnContext, ConversationState
from botbuilder.schema import ChannelAccount
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# OpenTelemetry / Arize Imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

class RagState:
    def __init__(self):
        self.history = []  # List of {"role": "...", "content": "..."}

class MyRagBot(ActivityHandler):
    def __init__(self, config, conversation_state: ConversationState):
        self.conversation_state = conversation_state
        self.state_accessor = self.conversation_state.create_property("RagState")
        self.config = config

        # 1. SETUP ARIZE TRACING
        resource = Resource(attributes={"service.name": "teams-rag-bot"})
        provider = TracerProvider(resource=resource)
        
        headers = {}
        if config.ARIZE_API_KEY:
            headers = {
                "api_key": config.ARIZE_API_KEY, 
                "space_id": config.ARIZE_SPACE_ID
            }

        exporter = OTLPSpanExporter(endpoint=config.ARIZE_COLLECTOR_ENDPOINT, headers=headers)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(__name__)

        # 2. INITIALIZE CLIENTS
        self.search_client = SearchClient(
            endpoint=config.AZURE_SEARCH_ENDPOINT,
            index_name=config.AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(config.AZURE_SEARCH_KEY)
        )
        
        self.openai_client = AzureOpenAI(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_KEY,
            api_version="2024-02-15-preview"
        )

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)
        await self.conversation_state.save_changes(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        state = await self.state_accessor.get(turn_context, RagState)
        user_input = turn_context.activity.text
        session_id = turn_context.activity.conversation.id

        # START TRACE
        with self.tracer.start_as_current_span("teams_turn") as root_span:
            root_span.set_attribute("session_id", session_id)
            root_span.set_attribute("input.value", user_input)
            
            # A. QUERY REWRITING (Multi-Turn Logic)
            search_query = user_input
            if len(state.history) > 0:
                with self.tracer.start_as_current_span("rewrite_query") as rewrite_span:
                    rewrite_prompt = [
                        {"role": "system", "content": "Rephrase the user's latest question to be a standalone search query based on the history. Output ONLY the query."},
                        {"role": "user", "content": f"History: {str(state.history[-3:])}\nLast Question: {user_input}"}
                    ]
                    rewrite_resp = self.openai_client.chat.completions.create(
                        model=self.config.AZURE_OPENAI_DEPLOYMENT,
                        messages=rewrite_prompt,
                        temperature=0.3
                    )
                    search_query = rewrite_resp.choices[0].message.content
                    rewrite_span.set_attribute("output.value", search_query)

            # B. RETRIEVAL (Integrated Vectorization)
            with self.tracer.start_as_current_span("azure_search") as search_span:
                vector_query = VectorizableTextQuery(
                    text=search_query, 
                    k_nearest_neighbors=3, 
                    fields="contentVector", # CHANGE THIS to your actual vector field name
                    exhaustive=True
                )
                
                results = self.search_client.search(
                    search_text=None,
                    vector_queries=[vector_query],
                    select=["content", "source"] # CHANGE THIS to your actual text fields
                )
                
                chunks = [f"[{doc.get('source','Doc')}] {doc.get('content','')}" for doc in results]
                search_span.set_attribute("retrieval.documents", json.dumps(chunks))
                root_span.set_attribute("retrieval.documents", json.dumps(chunks))

            # C. GENERATION
            with self.tracer.start_as_current_span("llm_generation") as llm_span:
                # Add current turn to prompt history
                current_turn_msgs = state.history + [{"role": "user", "content": user_input}]
                
                system_msg = {
                    "role": "system", 
                    "content": f"You are a helpful assistant. Use these sources to answer: {json.dumps(chunks)}"
                }
                
                final_messages = [system_msg] + current_turn_msgs
                
                llm_span.set_attribute("llm.input_messages", json.dumps(final_messages))
                llm_span.set_attribute("openinference.span.kind", "LLM")

                response = self.openai_client.chat.completions.create(
                    model=self.config.AZURE_OPENAI_DEPLOYMENT,
                    messages=final_messages
                )
                answer = response.choices[0].message.content
                
                llm_span.set_attribute("output.value", answer)
                root_span.set_attribute("output.value", answer)

            # D. UPDATE SHORT-TERM MEMORY (Rolling Window)
            state.history.append({"role": "user", "content": user_input})
            state.history.append({"role": "assistant", "content": answer})
            if len(state.history) > 6: # Keep last 3 turns
                state.history = state.history[-6:]

            await turn_context.send_activity(answer)

    async def on_members_added_activity(self, members_added: ChannelAccount, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello! I am your RAG Assistant. Ask me anything about your documents.")
