from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from typing import Optional, Type, List, Dict, Any
import logging
import json

from config import settings
from vector_store import get_vector_store
from services import check_inventory

logger = logging.getLogger(__name__)


class ProductSearchTool(BaseTool):
    """Tool for searching fashion products in the vector database"""

    name: str = "search_products"
    description: str = "Busca productos en el catálogo de moda usando búsqueda semántica. Usa esta herramienta cuando el usuario pregunte por prendas, outfits, o quiera recomendaciones de productos. La búsqueda considera el historial completo de la conversación para encontrar productos relevantes."

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Synchronous run method"""
        try:
            logger.info(f"🔍 Searching products with query: {query}")

            # Get vector store instance
            vector_store = get_vector_store()

            # Search for products with scores
            products_with_scores = vector_store.search_products(
                query=query,
                k=30,  # Get more results, we'll filter by inventory
                return_scores=True
            )

            # Sort by score descending (higher similarity first)
            products_with_scores.sort(key=lambda x: x[1], reverse=True)

            # Extract product IDs for inventory check
            product_ids = [product['product_id'] for product, score in products_with_scores]
            logger.info(f"🔍 Checking inventory for {len(product_ids)} products")

            # Check inventory for all products
            inventory_data = check_inventory(product_ids)

            # Filter products with stock > 0, maintaining score order
            available_products = []
            filtered_count = 0

            for product, score in products_with_scores:
                product_id = product['product_id']
                inventory_info = inventory_data.get(product_id, {})

                if inventory_info.get('stock', 0) > 0:
                    available_products.append(product)
                else:
                    filtered_count += 1
                    logger.debug(f"⚠️ Product {product_id} ({product['name']}) filtered due to no stock")

            logger.info(f"📦 Found {len(available_products)} products with stock (filtered {filtered_count} out of stock)")

            # Format results for the agent
            if not available_products:
                return "No se encontraron productos disponibles en el catálogo que coincidan con tu búsqueda."

            # Return formatted product data as JSON string for the agent to use
            return json.dumps(available_products, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error in product search: {e}")
            return f"Error searching products: {str(e)}"

    async def _arun(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Asynchronous run method"""
        # For now, just call the sync method since vector store operations are fast
        return self._run(query, run_manager)


TOOL_SYSTEM_PROMPT = """Eres un asistente experto en moda y ventas de indumentaria. Tu objetivo es:

1. COMPRENDER preferencias del usuario mediante conversación natural
2. RECOMENDAR outfits completos del catálogo disponible
3. AJUSTAR recomendaciones según feedback del usuario
4. VALIDAR disponibilidad en inventario antes de sugerir

REGLAS ESTRICTAS:
- Solo recomienda productos que existan en el catálogo actual
- Verifica disponibilidad en inventario antes de cada recomendación (la herramienta ya filtra por stock)
- Si un artículo no está disponible, busca alternativas similares
- Describe cada prenda con detalles (color, estilo, material, ocasión)
- Mantén coherencia de estilo en cada outfit

CAPACIDADES:
- Análisis de imágenes subidas por usuarios (prendas de referencia)
- Búsqueda por múltiples criterios (tipo, color, estilo, ocasión, precio)
- Combinación de prendas para crear outfits completos
- Explicación de por qué ciertas prendas combinan bien

INSTRUCCIONES PARA HERRAMIENTAS:
- Usa la herramienta "search_products" cuando el usuario pregunte por prendas específicas, outfits, o quiera recomendaciones
- La herramienta ya incluye verificación de inventario, así que confía en los resultados que devuelve
- Si no encuentras productos relevantes, sugiere refinar la búsqueda o pregunta por más detalles
- Considera el historial completo de la conversación al decidir qué buscar

FORMATO DE RESPUESTA:
- Conversación natural y amigable en español
- Preguntas clarificadoras cuando sea necesario
- Recomendaciones estructuradas con detalles
- Sugerencias de complementos (accesorios, calzado)
- Usa emojis ocasionalmente para dar personalidad (👗 💃 ✨ 👠 💫)
- Muestra el inventario (inventory) disponible de los productos recomendados
- Muestra el id de los productos recomendados
"""


class FashionAgent:
    """Fashion assistant using LangChain AgentExecutor with tools"""

    def __init__(self):
        self.llm = None
        self.agent_executor = None
        self.tools = None

    def _get_llm(self):
        """Initialize LLM based on configuration"""
        if not self.llm:
            if settings.DEFAULT_LLM_PROVIDER == "anthropic":
                self.llm = ChatAnthropic(
                    model=settings.DEFAULT_MODEL,
                    temperature=settings.TEMPERATURE,
                    anthropic_api_key=settings.ANTHROPIC_API_KEY
                )
            elif settings.DEFAULT_LLM_PROVIDER == "gemini":
                self.llm = ChatGoogleGenerativeAI(
                    model=settings.DEFAULT_MODEL,
                    temperature=settings.TEMPERATURE,
                    google_api_key=settings.GOOGLE_API_KEY
                )
            else:
                self.llm = ChatOpenAI(
                    model=settings.DEFAULT_MODEL,
                    temperature=settings.TEMPERATURE,
                    openai_api_key=settings.OPENAI_API_KEY
                )
        return self.llm

    def _get_agent_executor(self):
        """Initialize agent executor with tools"""
        if not self.agent_executor:
            llm = self._get_llm()

            # Initialize tools
            self.tools = [ProductSearchTool()]

            # Create agent using LangGraph
            self.agent_executor = create_react_agent(llm, self.tools)

        return self.agent_executor

    async def process_message(
        self,
        message: str,
        products: list = None,  # No longer used, kept for compatibility
        conversation_history: list = None,
        image_context: str = None
    ):
        """
        Process user message using agent with tools

        Args:
            message: User message
            products: Ignored (for backward compatibility)
            conversation_history: Previous conversation messages
            image_context: Optional context from image analysis
        """
        try:
            agent_executor = self._get_agent_executor()

            # Build input for agent
            input_message = message

            if image_context:
                input_message += f"\n\nContexto de imagen analizada: {image_context}"

            # Prepare messages for agent
            messages = []

            # Add system prompt as first message
            messages.append(SystemMessage(content=TOOL_SYSTEM_PROMPT))

            # Add conversation history
            if conversation_history:
                for msg in conversation_history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg.get("content", "")))

            # Add current user message
            messages.append(HumanMessage(content=input_message))

            # Run agent
            logger.info("🤖 Ejecutando agente con herramientas")
            response = await agent_executor.ainvoke({
                "messages": messages
            })

            # Extract the last message content
            last_message = response["messages"][-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)

            return {
                "response": response_content,
                "success": True
            }

        except Exception as e:
            logger.error(f"Error processing message with agent: {e}")
            return {
                "response": "Lo siento, tuve un problema procesando tu solicitud. ¿Puedes reformular tu pregunta?",
                "success": False,
                "error": str(e)
            }

    def reset_memory(self):
        """Reset conversation memory"""
        # Reset agent executor to clear any cached state
        self.agent_executor = None
        logger.info("🔄 Memoria del agente reiniciada")
