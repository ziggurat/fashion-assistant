from sqlalchemy import create_engine, Column, String, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./fashion_catalog.db"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Product(Base):
    """Product model"""
    __tablename__ = "products"
    
    product_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    subcategory = Column(String)
    description = Column(String)
    attributes = Column(JSON)
    style_tags = Column(JSON)
    occasion_tags = Column(JSON)
    season_tags = Column(JSON)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    images = Column(JSON)
    inventory = Column(JSON)
    search_text = Column(String, index=True)  # Texto optimizado para embeddings y búsqueda semántica


def init_db():
    """Initialize database and seed data"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        
        # Seed sample data
        seed_sample_data()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


def seed_sample_data():
    """Seed database with products from JSON file"""
    db = SessionLocal()
    try:
        # Check if data exists
        if db.query(Product).first():
            logger.info("Database already has data")
            return
        
        # Load products from JSON file
        products_file = Path(__file__).parent / "data" / "products.json"
        
        if not products_file.exists():
            logger.error(f"❌ Products file not found: {products_file}")
            logger.error("Please generate products.json by running: python export_products.py")
            return
        
        logger.info(f"Loading products from {products_file}")
        with open(products_file, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
        
        # Create Product objects
        products = []
        for data in products_data:
            product = Product(
                product_id=data['product_id'],
                name=data['name'],
                category=data['category'],
                subcategory=data.get('subcategory'),
                description=data.get('description'),
                attributes=data.get('attributes', {}),
                style_tags=data.get('style_tags', []),
                occasion_tags=data.get('occasion_tags', []),
                season_tags=data.get('season_tags', []),
                price=data.get('price', 0.0),
                currency=data.get('currency', 'USD'),
                images=data.get('images', []),
                inventory=data.get('inventory', {}),
                search_text=data.get('search_text', '')
            )
            products.append(product)
        
        # Bulk insert
        db.bulk_save_objects(products)
        db.commit()
        logger.info(f"✅ Seeded {len(products):,} products from JSON file")
        
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_all_products(limit: int = 50):
    """Get all products"""
    db = SessionLocal()
    try:
        products = db.query(Product).limit(limit).all()
        return [product_to_dict(p) for p in products]
    finally:
        db.close()


def product_to_dict(product: Product):
    """Convert product to dictionary"""
    return {
        "product_id": product.product_id,
        "name": product.name,
        "category": product.category,
        "subcategory": product.subcategory,
        "description": product.description,
        "attributes": product.attributes,
        "style_tags": product.style_tags,
        "occasion_tags": product.occasion_tags,
        "season_tags": product.season_tags,
        "price": product.price,
        "currency": product.currency,
        "images": product.images,
        "inventory": product.inventory,
        "search_text": product.search_text
    }
