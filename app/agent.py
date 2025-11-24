from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.tools import tool
import logging

from config import settings
from services import search_products, check_inventory

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Eres un asistente experto en moda y ventas de indumentaria. Tu objetivo es:

1. COMPRENDER preferencias del usuario mediante conversación natural
2. RECOMENDAR outfits completos del catálogo disponible
3. AJUSTAR recomendaciones según feedback del usuario
4. VALIDAR disponibilidad en inventario antes de sugerir

REGLAS ESTRICTAS:
- Solo recomienda productos que existan en el catálogo actual
- Verifica disponibilidad en inventario antes de cada recomendación
- Si un artículo no está disponible, busca alternativas similares
- Describe cada prenda con detalles (color, estilo, material, ocasión)
- Mantén coherencia de estilo en cada outfit

CAPACIDADES:
- Análisis de imágenes subidas por usuarios (prendas de referencia)
- Búsqueda por múltiples criterios (tipo, color, estilo, ocasión, precio)
- Combinación de prendas para crear outfits completos
- Explicación de por qué ciertas prendas combinan bien

FORMATO DE RESPUESTA:
- Conversación natural y amigable en español
- Preguntas clarificadoras cuando sea necesario
- Recomendaciones estructuradas con detalles
- Sugerencias de complementos (accesorios, calzado)
- Usa emojis ocasionalmente para dar personalidad (👗 💃 ✨ 👠 💫)
"""


class FashionAgent:
    """Main fashion assistant agent using LangChain"""

    def __init__(self):
        self.agent_chain = None
        
    def _get_llm(self):
        """Initialize LLM based on configuration"""
        if settings.DEFAULT_LLM_PROVIDER == "anthropic":
            return ChatAnthropic(
                model=settings.DEFAULT_MODEL,
                temperature=settings.TEMPERATURE,
                anthropic_api_key=settings.ANTHROPIC_API_KEY
            )
        else:
            return ChatOpenAI(
                model=settings.DEFAULT_MODEL,
                temperature=settings.TEMPERATURE,
                openai_api_key=settings.OPENAI_API_KEY
            )
    
    def _create_tools(self):
        """Create tools for the agent"""

        @tool
        def search_catalog_tool(
            category: str = None,
            colors: list = None,
            styles: list = None,
            occasion: str = None,
            price_min: float = None,
            price_max: float = None,
            exclude_colors: list = None
        ):
            """Busca productos en el catálogo según criterios múltiples"""
            results = search_products(
                category=category,
                colors=colors,
                styles=styles,
                occasion=occasion,
                price_min=price_min,
                price_max=price_max,
                exclude_colors=exclude_colors
            )
            return results

        @tool
        def check_inventory_tool(product_ids: list):
            """Verifica disponibilidad de productos en inventario"""
            return check_inventory(product_ids)

        @tool
        def analyze_image_tool(image_data: str):
            """Analiza una imagen para extraer información de moda"""
            # For now, return a placeholder since we don't have image analysis in services
            return {"message": "Análisis de imagen no implementado aún", "image_data": image_data}

        return [search_catalog_tool, check_inventory_tool, analyze_image_tool]
    
    def initialize(self, session_id: str = "default"):
        """Initialize the agent"""
        llm = self._get_llm()
        tools = self._create_tools()

        # Create agent using LangChain v1 API
        self.agent_chain = create_agent(
            model=llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT
        )

        logger.info(f"Fashion agent initialized for session: {session_id}")
    
    async def process_message(self, message: str, images: list = None, conversation_history: list = None):
        """Process user message and return response"""
        if not self.agent_chain:
            self.initialize()

        try:
            # Prepare message content
            content = message
            if images:
                content = f"{message}\n[Usuario ha subido {len(images)} imagen(es)]"

            # Prepare messages list with conversation history
            messages = []

            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user message
            messages.append({"role": "user", "content": content})

            # Execute agent using v1 API
            result = await self.agent_chain.ainvoke({
                "messages": messages
            })

            return {
                "response": result["messages"][-1].content,
                "success": True
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": "Lo siento, tuve un problema procesando tu solicitud. ¿Puedes reformular tu pregunta?",
                "success": False,
                "error": str(e)
            }

    def reset_memory(self):
        """Reset conversation memory - stub method for UI compatibility"""
        # LangChain v1 handles memory automatically, so this is a no-op
