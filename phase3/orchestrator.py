"""
Main Orchestration Module

Ties together all Phase 3 components for LLM-based restaurant ranking and explanation.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import asdict

try:
    from .prompt_builder import PromptBuilder, UserPreferences, RestaurantCandidate
    from .llm_client import LLMClient
    from .output_validator import OutputValidator, RetryHandler, RecommendationResponse
except ImportError:
    from prompt_builder import PromptBuilder, UserPreferences, RestaurantCandidate
    from llm_client import LLMClient
    from output_validator import OutputValidator, RetryHandler, RecommendationResponse

logger = logging.getLogger(__name__)


class RecommendationOrchestrator:
    """
    Main orchestrator for Phase 3 LLM operations.
    
    Coordinates prompt building, LLM communication, and output validation
    to generate ranked restaurant recommendations with explanations.
    """
    
    def __init__(self, 
                 llm_provider: str = "mock",
                 llm_config: Optional[Dict[str, Any]] = None,
                 max_retries: int = 3,
                 enable_fallback: bool = True):
        """
        Initialize the orchestrator
        
        Args:
            llm_provider: LLM provider to use ('openai', 'anthropic', 'mock')
            llm_config: Provider-specific configuration
            max_retries: Maximum number of retries for invalid responses
            enable_fallback: Whether to enable fallback responses
        """
        self.prompt_builder = PromptBuilder()
        self.llm_client = LLMClient(provider=llm_provider, **(llm_config or {}))
        self.output_validator = OutputValidator(max_retries=max_retries, fallback_enabled=enable_fallback)
        self.retry_handler = RetryHandler(self.output_validator, self.llm_client)
        
        logger.info(f"Initialized RecommendationOrchestrator with {llm_provider} provider")
    
    async def generate_recommendations(self, 
                                    preferences: UserPreferences, 
                                    candidates: List[RestaurantCandidate]) -> RecommendationResponse:
        """
        Generate ranked restaurant recommendations with explanations
        
        Args:
            preferences: User preferences for restaurant search
            candidates: List of restaurant candidates from retrieval layer
            
        Returns:
            RecommendationResponse with ranked restaurants and explanations
        """
        try:
            # Build appropriate prompt
            if candidates:
                prompt = self.prompt_builder.build_ranking_prompt(preferences, candidates)
                logger.info(f"Built ranking prompt for {len(candidates)} candidates")
            else:
                prompt = self.prompt_builder.build_fallback_prompt(preferences)
                logger.info("Built fallback prompt (no candidates)")
            
            # Get validated response with retries
            response, attempts = await self.retry_handler.get_validated_response(prompt)
            
            logger.info(f"Generated recommendations after {attempts} attempt(s)")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return self.output_validator.create_fallback_response(str(e))
    
    def format_recommendations_for_ui(self, response: RecommendationResponse) -> Dict[str, Any]:
        """
        Format recommendations for UI consumption
        
        Args:
            response: Validated recommendation response
            
        Returns:
            Dictionary formatted for UI display
        """
        formatted_rankings = []
        
        for ranking in response.rankings:
            formatted_ranking = {
                "rank": ranking.rank,
                "name": ranking.restaurant_name,
                "score": ranking.relevance_score,
                "explanation": ranking.explanation,
                "highlights": ranking.highlights
            }
            formatted_rankings.append(formatted_ranking)
        
        return {
            "rankings": formatted_rankings,
            "summary": response.summary,
            "suggestions": response.suggestions or [],
            "total_results": len(response.rankings)
        }
    
    async def batch_generate_recommendations(self, 
                                           preference_candidates_pairs: List[tuple]) -> List[RecommendationResponse]:
        """
        Generate recommendations for multiple preference/candidate pairs
        
        Args:
            preference_candidates_pairs: List of (preferences, candidates) tuples
            
        Returns:
            List of recommendation responses
        """
        logger.info(f"Processing batch of {len(preference_candidates_pairs)} requests")
        
        responses = []
        for i, (preferences, candidates) in enumerate(preference_candidates_pairs):
            try:
                response = await self.generate_recommendations(preferences, candidates)
                responses.append(response)
                logger.info(f"Completed batch item {i+1}/{len(preference_candidates_pairs)}")
            except Exception as e:
                logger.error(f"Failed to process batch item {i+1}: {e}")
                fallback = self.output_validator.create_fallback_response(str(e))
                responses.append(fallback)
        
        return responses
    
    def validate_input_data(self, 
                           preferences: UserPreferences, 
                           candidates: List[RestaurantCandidate]) -> tuple[bool, Optional[str]]:
        """
        Validate input data before processing
        
        Args:
            preferences: User preferences to validate
            candidates: Restaurant candidates to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate preferences
        if not preferences.location or len(preferences.location.strip()) == 0:
            return False, "Location is required"
        
        if not preferences.cuisine or len(preferences.cuisine.strip()) == 0:
            return False, "Cuisine preference is required"
        
        if preferences.min_rating < 0 or preferences.min_rating > 5:
            return False, "Minimum rating must be between 0 and 5"
        
        # Validate candidates
        for i, candidate in enumerate(candidates):
            if not candidate.name or len(candidate.name.strip()) == 0:
                return False, f"Candidate {i+1}: Restaurant name is required"
            
            if not candidate.cuisines or len(candidate.cuisines) == 0:
                return False, f"Candidate {i+1}: At least one cuisine is required"
            
            if candidate.rating < 0 or candidate.rating > 5:
                return False, f"Candidate {i+1}: Rating must be between 0 and 5"
            
            if candidate.cost_for_two < 0:
                return False, f"Candidate {i+1}: Cost for two must be positive"
        
        return True, None
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and configuration
        
        Returns:
            Dictionary with system status information
        """
        return {
            "llm_provider": self.llm_client.provider_name,
            "max_retries": self.output_validator.max_retries,
            "fallback_enabled": self.output_validator.fallback_enabled,
            "components": {
                "prompt_builder": "active",
                "llm_client": "active", 
                "output_validator": "active",
                "retry_handler": "active"
            }
        }


# Convenience function for quick usage
async def quick_recommend(preferences: UserPreferences, 
                         candidates: List[RestaurantCandidate],
                         provider: str = "mock") -> RecommendationResponse:
    """
    Quick convenience function for generating recommendations
    
    Args:
        preferences: User preferences
        candidates: Restaurant candidates
        provider: LLM provider to use
        
    Returns:
        RecommendationResponse with ranked restaurants
    """
    orchestrator = RecommendationOrchestrator(llm_provider=provider)
    return await orchestrator.generate_recommendations(preferences, candidates)
