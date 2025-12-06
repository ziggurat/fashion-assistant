import base64
import logging
import imghdr
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from config import settings

logger = logging.getLogger(__name__)

VISION_SYSTEM_PROMPT = """Eres un experto en análisis de moda e indumentaria. Tu tarea es analizar imágenes de ropa y generar términos de búsqueda precisos para un sistema RAG (Retrieval Augmented Generation).

ANALIZA LA IMAGEN E IDENTIFICA:

1. TIPO DE PRENDA(S): categoría exacta (vestido, pantalón, camisa, zapatos, etc.)
2. COLORES: colores principales y secundarios
3. ESTILO: casual, formal, deportivo, elegante, vintage, moderno, etc.
4. PATRONES: liso, rayas, flores, cuadros, estampado, etc.
5. OCASIÓN: oficina, fiesta, casual, deportivo, noche, día, etc.
6. CARACTERÍSTICAS: manga larga/corta, largo/corto, ajustado/holgado, etc.

FORMATO DE RESPUESTA REQUERIDO:
Responde ÚNICAMENTE con una sección llamada "## Términos de Búsqueda Recomendados" seguida de términos clave separados por comas.

EJEMPLO DE RESPUESTA:
## Términos de Búsqueda Recomendados
vestido largo, elegante, negro, manga larga, ocasión formal, corte ajustado, estilo moderno

NO incluyas descripciones largas ni explicaciones adicionales. Solo los términos de búsqueda.
"""


class FashionVisionAgent:
    """Agent for analyzing fashion images using Claude Vision"""

    def __init__(self):
        self.llm = None

    def _get_vision_llm(self):
        """Initialize Claude with vision capabilities"""
        if not self.llm:
            self.llm = ChatAnthropic(
                model=settings.DEFAULT_MODEL,
                temperature=0.3,  # Lower temperature for more consistent analysis
                api_key=settings.ANTHROPIC_API_KEY
            )
        return self.llm

    def _detect_image_type(self, image_bytes):
        """
        Detect image type from bytes

        Returns:
            str: MIME type (e.g., 'image/jpeg', 'image/png', 'image/gif', 'image/webp')
        """
        # Try to detect using imghdr
        image_type = imghdr.what(None, h=image_bytes)

        # Map imghdr types to MIME types
        mime_type_map = {
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }

        if image_type in mime_type_map:
            detected_type = mime_type_map[image_type]
            logger.info(f"🔍 Tipo de imagen detectado: {detected_type}")
            return detected_type

        # Default to JPEG if detection fails
        logger.warning(f"⚠️ No se pudo detectar el tipo de imagen, usando image/jpeg por defecto")
        return 'image/jpeg'

    def _encode_image(self, image_bytes):
        """Encode image to base64"""
        return base64.b64encode(image_bytes).decode('utf-8')

    async def analyze_image(self, image_bytes, user_prompt=None):
        """
        Analyze a fashion image and extract detailed information

        Args:
            image_bytes: Image file in bytes
            user_prompt: Optional additional context from user

        Returns:
            dict with analysis results
        """
        try:
            logger.info(f"📸 Iniciando análisis de imagen (tamaño: {len(image_bytes)} bytes)")
            if user_prompt:
                logger.info(f"💬 Contexto del usuario: {user_prompt}")

            llm = self._get_vision_llm()

            # Detect image type
            media_type = self._detect_image_type(image_bytes)

            # Encode image
            logger.info("🔄 Codificando imagen a base64...")
            image_base64 = self._encode_image(image_bytes)
            logger.info(f"✅ Imagen codificada (base64 length: {len(image_base64)} chars)")

            # Prepare prompt
            prompt = VISION_SYSTEM_PROMPT
            if user_prompt:
                prompt += f"\n\nCONTEXTO DEL USUARIO: {user_prompt}"

            # Create message with image
            message = HumanMessage(
                content=[
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            )

            # Get analysis from Claude
            logger.info("🤖 Enviando imagen a Claude para análisis...")
            response = await llm.ainvoke([message])

            logger.info("✅ Análisis de imagen completado exitosamente")
            logger.info(f"📝 Longitud de la respuesta: {len(response.content)} caracteres")

            return {
                "success": True,
                "analysis": response.content,
                "formatted_search_query": self._extract_search_terms(response.content)
            }

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis": "No pude analizar la imagen. Por favor, intenta con otra imagen o describe lo que buscas."
            }

    def _extract_search_terms(self, analysis_text):
        """
        Extract key search terms from the analysis
        Looks for "## Términos de Búsqueda Recomendados" section
        """
        # Try to find the search terms section
        if "## Términos de Búsqueda Recomendados" in analysis_text:
            # Split by the header
            parts = analysis_text.split("## Términos de Búsqueda Recomendados")
            if len(parts) > 1:
                # Get everything after the header
                search_terms = parts[1].strip()
                # Remove any additional markdown sections that might come after
                if "##" in search_terms:
                    search_terms = search_terms.split("##")[0].strip()
                logger.info(f"🔎 Términos de búsqueda extraídos: {search_terms}")
                return search_terms

        # If no specific section found, return the whole text
        logger.warning("⚠️ No se encontró la sección de términos de búsqueda, usando texto completo")
        return analysis_text
