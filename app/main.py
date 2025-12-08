import streamlit as st
import os
import asyncio
import logging
import hashlib
from agent import FashionAgent
from vision_agent import FashionVisionAgent
from database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Asistente de Moda IA",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    h1 {
        font-size: 12px;  
    }
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 0.75rem;
        margin: 0.25rem 0;
        background: white;
    }
    .chat-message {
        padding: 0.75rem;
        border-radius: 10px;
        margin: 0.25rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    [data-testid="stSidebar"] {
        width: 20vw !important;
    }
    /* Reduce spacing for various Streamlit elements */
    .stMarkdown {
        margin-bottom: 0.5rem !important;
    }
    .stButton > button {
        margin: 0.25rem 0 !important;
    }
    .stTextInput > div > div > input {
        margin: 0.25rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_agent():
    """Initialize the fashion agent (cached)"""
    return FashionAgent()


@st.cache_resource
def initialize_database():
    """Initialize database (cached)"""
    init_db()


def init_session_state():
    """Initialize session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = initialize_agent()
    if "vision_agent" not in st.session_state:
        st.session_state.vision_agent = FashionVisionAgent()
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if "image_analysis" not in st.session_state:
        st.session_state.image_analysis = None
    if "image_analysis_cache" not in st.session_state:
        st.session_state.image_analysis_cache = {}


async def main():
    """Main application"""
    # Initialize
    initialize_database()
    init_session_state()
    
    # Header
    st.title("👗 Asistente de Moda con IA")
    st.markdown("*Tu personal shopper virtual*")    
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Opciones")
        
        # Reset button
        if st.button("🔄 Nueva Conversación", width='stretch'):
            st.session_state.messages = []
            st.session_state.agent.reset_memory()
            st.session_state.image_analysis_cache = {}
            st.rerun()
        
        st.markdown("---")
        
        # Info section
        st.markdown("""
        ### 💡 Ejemplos de preguntas
        
        - "Quiero un vestido elegante para una fiesta"
        - "Busco zapatos que combinen con un vestido rojo"
        - "Necesito un outfit completo para una cena"
        - "¿Qué me recomiendas para el verano?"
        
        ### ✨ Puedo ayudarte a:
        - 🔍 Buscar prendas específicas
        - 👔 Armar outfits completos
        - 🎨 Recomendar combinaciones
        - 📦 Verificar disponibilidad
        - 💰 Ajustar a tu presupuesto
        """)
    
    # Main layout - Full width for chat
    st.header("💬 Conversación")

    # Display chat history
    chat_container = st.container(height=450)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                # Display image if present in message
                if "image" in message and message["image"]:
                    st.image(message["image"], width=200)

    # Chat input
    if prompt := st.chat_input("¿Qué estás buscando hoy?"):
        # Get uploaded file if present
        uploaded_file = st.session_state.get("temp_uploaded_file", None)
        # Prepare user message
        user_message = {
            "role": "user",
            "content": prompt
        }

        # Check if there's an uploaded image
        image_bytes = None
        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            user_message["image"] = uploaded_file
            logger.info(f"📸 Imagen cargada: {uploaded_file.name}, Tamaño: {len(image_bytes)} bytes")

        # Add user message
        st.session_state.messages.append(user_message)

        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
                if uploaded_file is not None:
                    st.image(uploaded_file, width=200)

        # Get agent response
        with chat_container:
            with st.chat_message("assistant"):
                try:
                    # Handle image analysis if present
                    image_context = ""

                    # If there's an image, analyze it first (with caching)
                    if image_bytes:
                        # Compute hash of image bytes for caching
                        image_hash = hashlib.sha256(image_bytes).hexdigest()
                        logger.info(f"🖼️ Hash de imagen: {image_hash}")

                        # Check if analysis is already cached
                        if image_hash in st.session_state.image_analysis_cache:
                            vision_result = st.session_state.image_analysis_cache[image_hash]
                            logger.info("✅ Usando análisis de imagen desde caché")
                        else:
                            with st.spinner("🔍 Analizando la imagen..."):
                                logger.info("🔍 Iniciando análisis de imagen con FashionVisionAgent")
                                vision_result = await st.session_state.vision_agent.analyze_image(
                                    image_bytes=image_bytes,
                                    user_prompt=prompt
                                )

                                # Cache the result
                                if vision_result["success"]:
                                    st.session_state.image_analysis_cache[image_hash] = vision_result
                                    logger.info("💾 Análisis de imagen guardado en caché")
                                else:
                                    logger.warning(f"⚠️ Error en análisis de imagen: {vision_result.get('error', 'Error desconocido')}")

                        if vision_result["success"]:
                            # Use the formatted search query as context for the agent
                            image_context = vision_result['formatted_search_query']
                            logger.info("✅ Análisis de imagen exitoso")
                            logger.info(f"📋 Descripción completa:\n{vision_result['analysis']}")
                            logger.info(f"🔎 Contexto de imagen para agente:\n{image_context}")
                        else:
                            image_context = ""

                    # Get fashion agent response (agent will call tools as needed)
                    with st.spinner("✨ Generando respuesta..."):
                        # Pass conversation history (excluding the current user message)
                        conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []

                        # Agent will handle product search via tools, so pass empty products list
                        response = await st.session_state.agent.process_message(
                            message=prompt,
                            products=[],  # Agent handles search internally via tools
                            conversation_history=conversation_history,
                            image_context=image_context
                        )

                        if response["success"]:
                            st.markdown(response["response"])

                            # Add to history
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response["response"]
                            })

                            logger.info("✅ Respuesta del agente generada exitosamente")
                        else:
                            error_msg = "Lo siento, tuve un problema procesando tu solicitud. ¿Puedes reformular tu pregunta?"
                            st.error(error_msg)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": error_msg
                            })
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    print(e)
                    st.error(error_msg)

    # Image upload section (below chat input)
    st.markdown("---")
    uploaded_file = st.file_uploader(
        "📷 Sube una imagen de referencia (opcional)",
        type=["jpg", "jpeg", "png", "gif", "webp"],
        help="Sube una foto de ropa que te guste para encontrar productos similares",
        key="image_uploader"
    )

    # Store uploaded file in session state for next message
    if uploaded_file is not None:
        st.session_state.temp_uploaded_file = uploaded_file
    else:
        st.session_state.temp_uploaded_file = None


if __name__ == "__main__":
    asyncio.run(main())
