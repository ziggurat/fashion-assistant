from sqlalchemy import create_engine, Column, String, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

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
    """Seed database with sample products"""
    db = SessionLocal()
    try:
        # Check if data exists
        if db.query(Product).first():
            logger.info("Database already has data")
            return
        
        sample_products = [
            Product(
                product_id="VES-001-RJ",
                name="Vestido de Noche Satinado Rojo",
                category="vestidos",
                subcategory="noche",
                description="Vestido largo de satén elegante con escote en V, perfecto para eventos formales y fiestas nocturnas",
                attributes={
                    "color_primary": "rojo",
                    "pattern": "liso",
                    "material": "satén",
                    "length": "largo",
                    "fit": "ajustado",
                    "neckline": "escote en V"
                },
                style_tags=["elegante", "formal", "sofisticado", "glamoroso"],
                occasion_tags=["fiesta", "gala", "cena formal", "eventos nocturnos"],
                season_tags=["verano", "primavera", "todo el año"],
                price=89.99,
                images=["https://via.placeholder.com/400x600/DC143C/FFFFFF?text=Vestido+Rojo+Elegante"],
                inventory={"XS": 2, "S": 5, "M": 3, "L": 0, "XL": 1}
            ),
            Product(
                product_id="VES-002-AZ",
                name="Vestido Midi Floral Azul",
                category="vestidos",
                subcategory="casual",
                description="Vestido de largo medio con hermoso estampado floral, ideal para días soleados y ocasiones informales",
                attributes={
                    "color_primary": "azul",
                    "color_secondary": "blanco",
                    "pattern": "floral",
                    "material": "algodón",
                    "length": "midi",
                    "fit": "holgado"
                },
                style_tags=["casual", "romántico", "fresco", "veraniego"],
                occasion_tags=["día", "playa", "brunch", "paseo"],
                season_tags=["verano", "primavera"],
                price=65.00,
                images=["https://via.placeholder.com/400x600/4169E1/FFFFFF?text=Vestido+Azul+Floral"],
                inventory={"XS": 3, "S": 4, "M": 5, "L": 4, "XL": 2}
            ),
            Product(
                product_id="VES-003-NG",
                name="Vestido Cóctel Negro Clásico",
                category="vestidos",
                subcategory="cóctel",
                description="El clásico little black dress, versátil y atemporal para cualquier ocasión elegante",
                attributes={
                    "color_primary": "negro",
                    "pattern": "liso",
                    "material": "poliéster",
                    "length": "corto",
                    "fit": "entallado"
                },
                style_tags=["elegante", "clásico", "versátil", "atemporal"],
                occasion_tags=["cóctel", "fiesta", "cena", "trabajo"],
                season_tags=["todo el año"],
                price=75.00,
                images=["https://via.placeholder.com/400x600/000000/FFFFFF?text=Vestido+Negro+Clasico"],
                inventory={"XS": 4, "S": 6, "M": 5, "L": 3, "XL": 2}
            ),
            Product(
                product_id="ZAP-001-NG",
                name="Stilettos Negros Clásicos",
                category="calzado",
                subcategory="tacones",
                description="Zapatos de tacón alto elegantes y versátiles que combinan con todo",
                attributes={
                    "color_primary": "negro",
                    "material": "cuero",
                    "heel_height": "10cm",
                    "style": "clásico"
                },
                style_tags=["elegante", "clásico", "versátil", "formal"],
                occasion_tags=["fiesta", "trabajo", "formal", "cóctel"],
                season_tags=["todo el año"],
                price=75.00,
                images=["https://via.placeholder.com/400x400/000000/FFFFFF?text=Stilettos+Negros"],
                inventory={"36": 3, "37": 4, "38": 5, "39": 3, "40": 2, "41": 1}
            ),
            Product(
                product_id="ZAP-002-DR",
                name="Sandalias Doradas con Tiras",
                category="calzado",
                subcategory="sandalias",
                description="Sandalias glamorosas con acabado dorado, perfectas para eventos de verano",
                attributes={
                    "color_primary": "dorado",
                    "material": "sintético metalizado",
                    "heel_height": "8cm",
                    "style": "glamoroso"
                },
                style_tags=["glamoroso", "festivo", "veraniego", "brillante"],
                occasion_tags=["fiesta", "boda", "cóctel", "eventos especiales"],
                season_tags=["verano", "primavera"],
                price=70.00,
                images=["https://via.placeholder.com/400x400/FFD700/000000?text=Sandalias+Doradas"],
                inventory={"36": 2, "37": 3, "38": 4, "39": 4, "40": 1}
            ),
            Product(
                product_id="ZAP-003-ND",
                name="Zapatos Nude de Tacón Medio",
                category="calzado",
                subcategory="tacones",
                description="Zapatos en tono nude que alargan la silueta, perfectos para el día a día elegante",
                attributes={
                    "color_primary": "nude",
                    "material": "cuero sintético",
                    "heel_height": "6cm",
                    "style": "elegante casual"
                },
                style_tags=["elegante", "versátil", "cómodo", "profesional"],
                occasion_tags=["trabajo", "día", "eventos", "general"],
                season_tags=["todo el año"],
                price=60.00,
                images=["https://via.placeholder.com/400x400/F5DEB3/FFFFFF?text=Zapatos+Nude"],
                inventory={"36": 5, "37": 6, "38": 7, "39": 5, "40": 3}
            ),
            Product(
                product_id="ACC-001-DR",
                name="Clutch Dorado Pequeño",
                category="accesorios",
                subcategory="bolsos",
                description="Bolso de mano elegante con acabado metalizado, ideal para eventos nocturnos",
                attributes={
                    "color_primary": "dorado",
                    "material": "sintético metalizado",
                    "size": "pequeño",
                    "closure": "magnético"
                },
                style_tags=["elegante", "glamoroso", "sofisticado", "festivo"],
                occasion_tags=["fiesta", "gala", "boda", "eventos formales"],
                season_tags=["todo el año"],
                price=45.00,
                images=["https://via.placeholder.com/400x300/FFD700/000000?text=Clutch+Dorado"],
                inventory={"única": 8}
            ),
            Product(
                product_id="ACC-002-NG",
                name="Bolso Negro de Cuero",
                category="accesorios",
                subcategory="bolsos",
                description="Bolso mediano de cuero genuino, elegante y funcional para el día a día",
                attributes={
                    "color_primary": "negro",
                    "material": "cuero genuino",
                    "size": "mediano",
                    "closure": "cremallera"
                },
                style_tags=["elegante", "clásico", "versátil", "profesional"],
                occasion_tags=["trabajo", "día", "casual elegante"],
                season_tags=["todo el año"],
                price=120.00,
                images=["https://via.placeholder.com/400x300/000000/FFFFFF?text=Bolso+Negro+Cuero"],
                inventory={"única": 5}
            ),
            Product(
                product_id="PAN-001-NG",
                name="Pantalón Negro de Vestir",
                category="pantalones",
                subcategory="formales",
                description="Pantalón de corte recto elegante, perfecto para look profesional",
                attributes={
                    "color_primary": "negro",
                    "material": "poliéster",
                    "fit": "recto",
                    "waist": "alto"
                },
                style_tags=["elegante", "profesional", "clásico", "versátil"],
                occasion_tags=["trabajo", "formal", "casual elegante"],
                season_tags=["todo el año"],
                price=55.00,
                images=["https://via.placeholder.com/400x600/000000/FFFFFF?text=Pantalon+Negro"],
                inventory={"XS": 3, "S": 5, "M": 6, "L": 4, "XL": 3}
            ),
            Product(
                product_id="BLS-001-BC",
                name="Blusa Blanca de Seda",
                category="blusas",
                subcategory="formales",
                description="Blusa elegante de seda con caída perfecta, esencial en todo guardarropa",
                attributes={
                    "color_primary": "blanco",
                    "material": "seda",
                    "fit": "regular",
                    "sleeve": "manga larga"
                },
                style_tags=["elegante", "clásico", "sofisticado", "versátil"],
                occasion_tags=["trabajo", "formal", "eventos", "día"],
                season_tags=["todo el año"],
                price=80.00,
                images=["https://via.placeholder.com/400x600/FFFFFF/000000?text=Blusa+Blanca+Seda"],
                inventory={"XS": 4, "S": 6, "M": 5, "L": 4, "XL": 2}
            )
        ]
        
        db.add_all(sample_products)
        db.commit()
        logger.info(f"Seeded {len(sample_products)} products")
        
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
        "inventory": product.inventory
    }
