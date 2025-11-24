from typing import List, Optional, Dict
from database import SessionLocal, Product, product_to_dict
import logging

logger = logging.getLogger(__name__)


def search_products(
    category: Optional[str] = None,
    colors: Optional[List[str]] = None,
    styles: Optional[List[str]] = None,
    occasion: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    exclude_colors: Optional[List[str]] = None,
    limit: int = 10
) -> List[dict]:
    """
    Search products with multiple filters
    """
    from sqlalchemy import text

    db = SessionLocal()
    try:
        query = db.query(Product)

        # Category filter
        if category:
            query = query.filter(Product.category == category.lower())

        # Color filters - use SQLite JSON functions
        if colors:
            color_conditions = []
            for color in colors:
                color_conditions.append(
                    text("json_extract(attributes, '$.color_primary') LIKE :color").params(color=f"%{color}%")
                )
            if color_conditions:
                query = query.filter(text(" OR ".join([str(condition) for condition in color_conditions])))

        if exclude_colors:
            for color in exclude_colors:
                query = query.filter(
                    ~text("json_extract(attributes, '$.color_primary') LIKE :color").params(color=f"%{color}%")
                )

        # Style filters - check if array contains style using JSON
        if styles:
            style_conditions = []
            for style in styles:
                style_conditions.append(
                    text("json_extract(style_tags, '$') LIKE :style").params(style=f'%"{style.lower()}"%')
                )
            if style_conditions:
                query = query.filter(text(" OR ".join([str(condition) for condition in style_conditions])))

        # Occasion filter - check if array contains occasion using JSON
        if occasion:
            query = query.filter(
                text("json_extract(occasion_tags, '$') LIKE :occasion").params(occasion=f'%"{occasion.lower()}"%')
            )

        # Price filters
        if price_min is not None:
            query = query.filter(Product.price >= price_min)

        if price_max is not None:
            query = query.filter(Product.price <= price_max)

        # Execute query
        products = query.limit(limit).all()
        results = [product_to_dict(p) for p in products]

        logger.info(f"Found {len(results)} products")
        return results

    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return []
    finally:
        db.close()


def check_inventory(product_ids: List[str]) -> Dict[str, dict]:
    """
    Check inventory availability for multiple products
    """
    db = SessionLocal()
    try:
        results = {}
        
        for product_id in product_ids:
            product = db.query(Product).filter(
                Product.product_id == product_id
            ).first()
            
            if not product:
                results[product_id] = {
                    "available": False,
                    "stock": 0,
                    "sizes_available": [],
                    "message": "Producto no encontrado"
                }
                continue
            
            # Calculate stock
            inventory = product.inventory or {}
            total_stock = sum(inventory.values())
            available_sizes = [size for size, stock in inventory.items() if stock > 0]
            
            results[product_id] = {
                "product_name": product.name,
                "available": total_stock > 0,
                "stock": total_stock,
                "sizes_available": available_sizes,
                "inventory_by_size": inventory,
                "price": product.price
            }
        
        logger.info(f"Checked inventory for {len(product_ids)} products")
        return results
        
    except Exception as e:
        logger.error(f"Error checking inventory: {e}")
        return {}
    finally:
        db.close()


def analyze_style_compatibility(product_ids: List[str]) -> dict:
    """
    Analyze if products form a compatible outfit
    """
    db = SessionLocal()
    try:
        products = db.query(Product).filter(
            Product.product_id.in_(product_ids)
        ).all()
        
        if not products:
            return {
                "compatible": False,
                "score": 0.0,
                "message": "No se encontraron productos"
            }
        
        # Simple compatibility analysis
        colors = set()
        styles = set()
        occasions = set()
        
        for product in products:
            if product.attributes and "color_primary" in product.attributes:
                colors.add(product.attributes["color_primary"])
            
            if product.style_tags:
                styles.update(product.style_tags)
            
            if product.occasion_tags:
                occasions.update(product.occasion_tags)
        
        # Calculate compatibility score
        score = 0.7  # Base score
        
        # Check style consistency
        common_styles = len(styles) > 0
        if common_styles:
            score += 0.1
        
        # Check occasion match
        common_occasions = len(occasions) > 0
        if common_occasions:
            score += 0.1
        
        # Color harmony (simplified)
        if len(colors) <= 3:  # Not too many colors
            score += 0.1
        
        suggestions = []
        if len(colors) > 3:
            suggestions.append("Considera reducir la cantidad de colores")
        
        if not common_occasions:
            suggestions.append("Verifica que las prendas sean apropiadas para la misma ocasión")
        
        return {
            "compatible": score >= 0.7,
            "score": min(score, 1.0),
            "colors": list(colors),
            "styles": list(styles),
            "occasions": list(occasions),
            "suggestions": suggestions if suggestions else ["¡Excelente combinación!"],
            "message": "Compatible" if score >= 0.7 else "Podría mejorarse"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing compatibility: {e}")
        return {
            "compatible": False,
            "score": 0.0,
            "message": f"Error: {str(e)}"
        }
    finally:
        db.close()
