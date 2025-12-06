import streamlit as st
import os
import asyncio
import logging
from agent import FashionAgent
from vision_agent import FashionVisionAgent
from database import init_db, get_all_products
from utils import display_product_card

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
    .stApp {        
        margin: 0 auto;
    }
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
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
    if "current_products" not in st.session_state:
        st.session_state.current_products = []
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if "image_analysis" not in st.session_state:
        st.session_state.image_analysis = None


async def main():
    """Main application"""
    # Initialize
    initialize_database()
    init_session_state()
    
    # Header
    st.title("👗 Asistente de Moda con IA")
    st.markdown("*Tu personal shopper virtual*")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Opciones")
        
        # Reset button
        if st.button("🔄 Nueva Conversación", width='stretch'):
            st.session_state.messages = []
            st.session_state.agent.reset_memory()
            st.session_state.current_products = []
            st.rerun()
        
        st.markdown("---")
        
        # Catalog section
        st.header("🛍️ Explorar Catálogo")
        
        if st.button("Ver Todos los Productos", width='stretch'):
            products = get_all_products(limit=20)
            st.session_state.current_products = products
        
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
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    # Chat column
    with col1:
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
                        # If there's an image, analyze it first
                        image_context = ""
                        if image_bytes:
                            with st.spinner("🔍 Analizando la imagen..."):
                                logger.info("🔍 Iniciando análisis de imagen con FashionVisionAgent")
                                vision_result = await st.session_state.vision_agent.analyze_image(
                                    image_bytes=image_bytes,
                                    user_prompt=prompt
                                )

                                if vision_result["success"]:
                                    # Use only the extracted search terms for RAG
                                    search_terms = vision_result['formatted_search_query']
                                    image_context = f"\n\nTérminos de búsqueda extraídos de la imagen:\n{search_terms}"
                                    logger.info("✅ Análisis de imagen exitoso")
                                    logger.info(f"📋 Descripción completa:\n{vision_result['analysis']}")
                                    logger.info(f"🔎 Términos de búsqueda para RAG:\n{search_terms}")
                                    st.info("✅ Imagen analizada correctamente")
                                else:
                                    logger.warning(f"⚠️ Error en análisis de imagen: {vision_result.get('error', 'Error desconocido')}")
                                    st.warning("⚠️ No pude analizar la imagen completamente, continuaré con tu consulta de texto.")

                        # Combine user prompt with image context
                        combined_message = prompt + image_context

                        if image_context:
                            logger.info(f"💬 Mensaje combinado enviado al FashionAgent:\n{combined_message}")

                        # Get fashion agent response
                        with st.spinner("✨ Buscando las mejores opciones..."):
                            # Pass conversation history (excluding the current user message)
                            conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []
                            response = await st.session_state.agent.process_message(
                                message=combined_message,
                                conversation_history=conversation_history
                            )

                            if response["success"]:
                                st.markdown(response["response"])

                                # Add to history
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": response["response"]
                                })

                                # Update products if any were found
                                if response.get("products"):
                                    st.session_state.current_products = response["products"]
                            else:
                                error_msg = "Lo siento, tuve un problema. ¿Puedes reformular tu pregunta?"
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
            "📸 Sube una imagen de referencia (opcional)",
            type=["jpg", "jpeg", "png", "gif", "webp"],
            help="Sube una foto de ropa que te guste para encontrar productos similares",
            key="image_uploader"
        )

        # Store uploaded file in session state for next message
        if uploaded_file is not None:
            st.session_state.temp_uploaded_file = uploaded_file
        else:
            st.session_state.temp_uploaded_file = None

    # Products column
    with col2:
        st.header("🛍️ Productos")
        
        if st.session_state.current_products:
            st.success(f"📦 {len(st.session_state.current_products)} productos encontrados")
            
            # Display products in scrollable container
            products_container = st.container(height=600)
            with products_container:
                for product in st.session_state.current_products:
                    display_product_card(product)
                    st.markdown("---")
        else:
            st.info("🔍 Los productos aparecerán aquí cuando realices una búsqueda")
            
            # Show some sample products
            with st.expander("Ver productos de muestra"):
                sample_products = get_all_products(limit=3)
                for product in sample_products:
                    display_product_card(product) 


if __name__ == "__main__":
    asyncio.run(main())
