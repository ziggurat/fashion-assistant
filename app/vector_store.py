"""
Vector Store using FAISS for semantic search on fashion products
Stores embeddings of product search_text with product_id as metadata
"""

import os
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from database import SessionLocal, Product

logger = logging.getLogger(__name__)


class FashionVectorStore:
    """
    Vector store for fashion products using FAISS.
    
    Architecture:
    - Generates embeddings from product.search_text
    - Stores embeddings in FAISS index
    - Stores product_id in metadata for reference to SQLite
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_path: str = "app/data/faiss_index",
        metadata_path: str = "app/data/faiss_metadata.pkl"
    ):
        """
        Initialize vector store.
        
        Args:
            model_name: Sentence transformer model for embeddings
            index_path: Path to save/load FAISS index
            metadata_path: Path to save/load metadata (product_ids)
        """
        self.model_name = model_name
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        
        # Load embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # FAISS index and metadata
        self.index: Optional[faiss.Index] = None
        self.product_ids: List[str] = []
        
        # Try to load existing index
        if self.index_path.exists() and self.metadata_path.exists():
            self.load()
        else:
            logger.info("No existing index found. Call build_index() to create one.")
    
    def build_index(self, batch_size: int = 100):
        """
        Build FAISS index from all products in database.
        
        Args:
            batch_size: Number of products to process at once
        """
        logger.info("Building FAISS index from products...")
        
        # Get all products from database
        db = SessionLocal()
        try:
            total_products = db.query(Product).count()
            logger.info(f"Total products to index: {total_products:,}")
            
            # Initialize lists
            all_embeddings = []
            all_product_ids = []
            
            # Process in batches
            processed = 0
            for offset in range(0, total_products, batch_size):
                products = db.query(Product).offset(offset).limit(batch_size).all()
                
                # Extract search texts and product IDs
                search_texts = []
                product_ids = []
                
                for product in products:
                    if product.search_text:
                        search_texts.append(product.search_text)
                        product_ids.append(product.product_id)
                
                # Generate embeddings
                if search_texts:
                    embeddings = self.model.encode(
                        search_texts,
                        show_progress_bar=False,
                        convert_to_numpy=True
                    )
                    
                    all_embeddings.append(embeddings)
                    all_product_ids.extend(product_ids)
                
                processed += len(products)
                if processed % 1000 == 0:
                    logger.info(f"Processed {processed:,} / {total_products:,} products")
            
            # Combine all embeddings
            embeddings_matrix = np.vstack(all_embeddings).astype('float32')
            logger.info(f"Generated {len(embeddings_matrix):,} embeddings")
            
            # Create FAISS index
            # Using IndexFlatL2 for exact search (good for <100k vectors)
            # For larger datasets, consider IndexIVFFlat or IndexHNSW
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            
            # Add embeddings to index
            self.index.add(embeddings_matrix)
            self.product_ids = all_product_ids
            
            logger.info(f"✅ FAISS index built with {self.index.ntotal:,} vectors")
            
            # Save index
            self.save()
            
        finally:
            db.close()
    
    def search(
        self,
        query: str,
        k: int = 5,
        return_scores: bool = False
    ) -> Union[List[str], List[Tuple[str, float]]]:
        """
        Search for similar products using semantic similarity.
        
        Args:
            query: Search query text
            k: Number of results to return
            return_scores: If True, return (product_id, similarity_score) tuples
        
        Returns:
            List of product_ids or list of (product_id, score) tuples
        """
        if self.index is None or not self.product_ids:
            logger.error("Index not loaded. Call build_index() first.")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True).astype('float32')
        
        # Search in FAISS
        # distances are L2 distances (lower is better)
        distances, indices = self.index.search(query_embedding, k)
        
        # Get product IDs
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.product_ids):
                product_id = self.product_ids[idx]
                
                if return_scores:
                    # Convert L2 distance to similarity score (0-1, higher is better)
                    # Using inverse of distance, normalized
                    similarity = 1 / (1 + distance)
                    results.append((product_id, float(similarity)))
                else:
                    results.append(product_id)
        
        return results
    
    def get_products_by_ids(self, product_ids: List[str]) -> List[Dict]:
        """
        Retrieve full product details from SQLite using product IDs.
        
        Args:
            product_ids: List of product IDs to retrieve
        
        Returns:
            List of product dictionaries
        """
        db = SessionLocal()
        try:
            products = db.query(Product).filter(
                Product.product_id.in_(product_ids)
            ).all()
            
            # Convert to dictionaries maintaining order
            product_dict = {p.product_id: self._product_to_dict(p) for p in products}
            return [product_dict[pid] for pid in product_ids if pid in product_dict]
            
        finally:
            db.close()
    
    def search_products(
        self,
        query: str,
        k: int = 5,
        return_scores: bool = False
    ) -> Union[List[Dict], List[Tuple[Dict, float]]]:
        """
        Search for products and return full product details.
        
        Args:
            query: Search query text
            k: Number of results to return
            return_scores: If True, return (product, score) tuples
        
        Returns:
            List of product dicts or list of (product_dict, score) tuples
        """
        # Get product IDs and scores from FAISS
        search_results = self.search(query, k, return_scores=True)
        
        if not search_results:
            return []
        
        # Extract product IDs
        product_ids = [pid for pid, _ in search_results]
        
        # Get full product details from SQLite
        products = self.get_products_by_ids(product_ids)
        
        if return_scores:
            # Combine products with scores
            scores_dict = {pid: score for pid, score in search_results}
            return [
                (product, scores_dict.get(product['product_id'], 0.0))
                for product in products
            ]
        else:
            return products
    
    def save(self):
        """Save FAISS index and metadata to disk."""
        # Create directory if it doesn't exist
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        logger.info(f"Saved FAISS index to {self.index_path}")
        
        # Save metadata (product IDs)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.product_ids, f)
        logger.info(f"Saved metadata to {self.metadata_path}")
    
    def load(self):
        """Load FAISS index and metadata from disk."""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            logger.info(f"Loaded FAISS index from {self.index_path} ({self.index.ntotal:,} vectors)")
            
            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                self.product_ids = pickle.load(f)
            logger.info(f"Loaded metadata with {len(self.product_ids):,} product IDs")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            self.index = None
            self.product_ids = []
    
    def _product_to_dict(self, product: Product) -> Dict:
        """Convert Product ORM object to dictionary."""
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
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_products": len(self.product_ids),
            "embedding_dim": self.embedding_dim,
            "model": self.model_name,
            "index_type": type(self.index).__name__ if self.index else None
        }


# Singleton instance
_vector_store: Optional[FashionVectorStore] = None


def get_vector_store() -> FashionVectorStore:
    """Get or create singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FashionVectorStore()
    return _vector_store

