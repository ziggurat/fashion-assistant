import streamlit as st
import os
import asyncio
from agent import FashionAgent
from database import init_db, get_all_products
from utils import display_product_card

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
    if "current_products" not in st.session_state:
        st.session_state.current_products = []


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
        chat_container = st.container(height=500)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("¿Qué estás buscando hoy?"):
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Display user message
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            # Get agent response
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("✨ Buscando las mejores opciones..."):
                        try:
                            # Pass conversation history (excluding the current user message)
                            conversation_history = st.session_state.messages[:-1] if len(st.session_state.messages) > 1 else []
                            response = await st.session_state.agent.process_message(
                                message=prompt,
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
