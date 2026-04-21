"""Contact data enrichment."""
from typing import Dict, Optional, List
import asyncio
from ..core.logging import logger
from ..core.errors import ContactEnrichmentError


class ContactEnricher:
    """Enriches prospect data with contact information."""

    @staticmethod
    async def enrich_contact(
        address: str,
        latitude: float,
        longitude: float,
        google_maps_api_key: Optional[str] = None,
    ) -> Dict:
        """Enrich prospect contact information using multiple sources.
        
        Args:
            address: Building address
            latitude: Building latitude
            longitude: Building longitude
            google_maps_api_key: Optional Google Maps API key
        
        Returns:
            Dictionary with contact information
        
        Raises:
            ContactEnrichmentError: If enrichment fails
        """
        logger.info(f"Enriching contact for {address}")
        
        result = {
            "contact_name": None,
            "title": None,
            "email": None,
            "phone": None,
            "business_name": None,
            "business_type": None,
            "data_complete": False,
            "data_source": None,
            "confidence_score": 0.0,
        }
        
        try:
            # Try multiple enrichment sources in parallel
            tasks = [
                ContactEnricher._enrich_from_google_maps(address, google_maps_api_key),
                ContactEnricher._enrich_from_map_data(address),
                ContactEnricher._enrich_from_web_search(address),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Merge results from multiple sources
            for res in results:
                if isinstance(res, dict) and res:
                    for key, value in res.items():
                        if value and not result[key]:
                            result[key] = value
            
            # Score completeness
            fields_filled = sum(1 for v in [
                result.get("contact_name"),
                result.get("email"),
                result.get("phone"),
                result.get("business_name"),
            ] if v)
            
            result["data_complete"] = fields_filled >= 3
            result["confidence_score"] = min(0.95, fields_filled / 4.0)
            
            if result["data_complete"]:
                logger.info(f"Successfully enriched contact for {address}")
            else:
                logger.warning(f"Partial data enrichment for {address}")
            
            return result
            
        except Exception as e:
            logger.error(f"Contact enrichment failed for {address}: {str(e)}")
            # Return partial result rather than failing
            return result

    @staticmethod
    async def _enrich_from_google_maps(
        address: str,
        api_key: Optional[str] = None
    ) -> Optional[Dict]:
        """Enrich from Google Maps API."""
        if not api_key:
            logger.debug("Google Maps API key not configured, skipping")
            return None

        logger.info("Google Maps enrichment integration not enabled in MVP")
        return None

    @staticmethod
    async def _enrich_from_map_data(address: str) -> Optional[Dict]:
        """Enrich from map data providers."""
        logger.info("Map data enrichment integration not enabled in MVP")
        return None

    @staticmethod
    async def _enrich_from_web_search(address: str) -> Optional[Dict]:
        """Enrich from web search."""
        logger.info("Web search enrichment integration not enabled in MVP")
        return None

    @staticmethod
    async def enrich_batch(
        prospects: List[Dict],
        google_maps_api_key: Optional[str] = None,
        concurrency: int = 5,
    ) -> List[Dict]:
        """Batch enrich multiple prospects with rate limiting.
        
        Args:
            prospects: List of prospect dictionaries
            google_maps_api_key: Optional Google Maps API key
            concurrency: Number of concurrent requests
        
        Returns:
            List of enriched prospects
        """
        logger.info(f"Batch enriching {len(prospects)} prospects")
        
        enriched = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def enrich_with_semaphore(prospect):
            async with semaphore:
                contact_data = await ContactEnricher.enrich_contact(
                    address=prospect.get("address", ""),
                    latitude=prospect.get("latitude", 0),
                    longitude=prospect.get("longitude", 0),
                    google_maps_api_key=google_maps_api_key,
                )
                return {**prospect, "contact": contact_data}
        
        tasks = [enrich_with_semaphore(p) for p in prospects]
        enriched = await asyncio.gather(*tasks, return_exceptions=False)
        
        logger.info(f"Finished batch enrichment of {len(enriched)} prospects")
        return enriched
