import streamlit as st


def display_product_card(product: dict):
    """Display a product card in Streamlit"""
    
    with st.container():
        # Product image
        if product.get("images") and len(product["images"]) > 0:
            st.image(product["images"][0], width='stretch')
        
        # Product name and category
        st.markdown(f"### {product['name']}")
        st.caption(f"📂 {product.get('category', 'N/A').title()} | {product.get('subcategory', 'N/A').title()}")
        
        # Description
        if product.get('description'):
            st.write(product['description'])
        
        # Price
        price = product.get('price', 0)
        currency = product.get('currency', 'USD')
        st.markdown(f"**💰 ${price:.2f} {currency}**")
        
        # Attributes
        attrs = product.get('attributes', {})
        if attrs:
            col1, col2 = st.columns(2)
            with col1:
                if 'color_primary' in attrs:
                    st.write(f"🎨 **Color:** {attrs['color_primary'].title()}")
                if 'material' in attrs:
                    st.write(f"📏 **Material:** {attrs['material'].title()}")
            with col2:
                if 'fit' in attrs:
                    st.write(f"👔 **Corte:** {attrs['fit'].title()}")
                if 'length' in attrs:
                    st.write(f"📐 **Largo:** {attrs['length'].title()}")
        
        # Tags
        if product.get('style_tags'):
            st.write("**Estilo:**", ", ".join([tag.title() for tag in product['style_tags'][:3]]))
        
        if product.get('occasion_tags'):
            st.write("**Ocasión:**", ", ".join([tag.title() for tag in product['occasion_tags'][:3]]))
        
        # Inventory
        inventory = product.get('inventory', {})
        if inventory:
            total_stock = sum(inventory.values())
            available_sizes = [size for size, stock in inventory.items() if stock > 0]
            
            if available_sizes:
                st.success(f"✅ **Disponible** - Tallas: {', '.join(available_sizes)}")
            else:
                st.error("❌ **Sin stock**")
        
        # Action button
        if st.button(f"Ver detalles", key=f"btn_{product['product_id']}", width='stretch'):
            st.info(f"Producto ID: {product['product_id']}")


def format_price(price: float, currency: str = "USD") -> str:
    """Format price for display"""
    return f"${price:.2f} {currency}"


def get_color_emoji(color: str) -> str:
    """Get emoji for color"""
    color_emojis = {
        "rojo": "🔴",
        "azul": "🔵",
        "negro": "⚫",
        "blanco": "⚪",
        "verde": "🟢",
        "amarillo": "🟡",
        "rosa": "💗",
        "dorado": "🟡",
        "plateado": "⚪",
    }
    return color_emojis.get(color.lower(), "🎨")


def get_category_emoji(category: str) -> str:
    """Get emoji for category"""
    category_emojis = {
        "vestidos": "👗",
        "calzado": "👠",
        "accesorios": "👜",
        "pantalones": "👖",
        "blusas": "👚",
        "chaquetas": "🧥",
    }
    return category_emojis.get(category.lower(), "🛍️")
