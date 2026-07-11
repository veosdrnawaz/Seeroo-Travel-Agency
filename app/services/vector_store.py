import logging
import os
import chromadb
from app.services.embedding_service import chroma_client, get_embedding

# Configure logger
logger = logging.getLogger("seeroo_vector_store")

def search(query: str, filters: dict = None, top_k: int = 5):
    """
    Performs similarity search in the ChromaDB collection 'seeroo_tours'.
    Supports metadata filtering for:
    - category (exact match)
    - max_price (price_per_head <= max_price)
    - month (exact match)
    - tour_id (exact match)
    
    If no matches are found, returns the string "NO_MATCH_FOUND".
    """
    logger.info(f"Initiating vector search: '{query}' with filters={filters}")
    
    try:
        # Get collection (will raise exception if it doesn't exist yet)
        collection = chroma_client.get_collection(name="seeroo_tours")
    except Exception as e:
        logger.error(f"Collection 'seeroo_tours' not initialized yet: {str(e)}")
        return "NO_MATCH_FOUND"

    try:
        # 1. Generate query embedding vector
        query_vector = get_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {str(e)}")
        return "NO_MATCH_FOUND"

    # 2. Build metadata filter matching Chroma query syntax
    where_clauses = []
    if filters:
        if "category" in filters and filters["category"]:
            where_clauses.append({"category": {"$eq": filters["category"]}})
        if "max_price" in filters and filters["max_price"] is not None:
            where_clauses.append({"price_per_head": {"$lte": int(filters["max_price"])}})
        if "month" in filters and filters["month"]:
            where_clauses.append({"month": {"$eq": filters["month"]}})
        if "tour_id" in filters and filters["tour_id"]:
            where_clauses.append({"tour_id": {"$eq": filters["tour_id"]}})

    where_dict = None
    if len(where_clauses) > 1:
        where_dict = {"$and": where_clauses}
    elif len(where_clauses) == 1:
        where_dict = where_clauses[0]

    # 3. Query vector database
    try:
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_dict
        )
        
        # Check if we have results
        if not results or not results["documents"] or len(results["documents"][0]) == 0:
            logger.info("Search executed successfully, but returned 0 results.")
            return "NO_MATCH_FOUND"
            
        # Format results nicely for consumption
        formatted_matches = []
        for i in range(len(results["documents"][0])):
            match = {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results and results["distances"] else None
            }
            formatted_matches.append(match)
            
        logger.info(f"Vector search returned {len(formatted_matches)} matches.")
        return formatted_matches
        
    except Exception as e:
        logger.error(f"Error executing search query in ChromaDB: {str(e)}")
        return "NO_MATCH_FOUND"
