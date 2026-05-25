"""
Prompt Builder for LLM Orchestration

Constructs structured prompts for restaurant ranking and explanation generation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class UserPreferences:
    """Structured user preferences"""
    location: str
    budget: str
    cuisine: str
    min_rating: float
    additional_preferences: Optional[str] = None


@dataclass
class RestaurantCandidate:
    """Restaurant candidate from retrieval layer"""
    name: str
    cuisines: List[str]
    rating: float
    cost_for_two: int
    location: str
    votes: int = 0


class PromptBuilder:
    """Builds structured prompts for LLM-based restaurant ranking"""
    
    def __init__(self):
        self.system_prompt = """You are a restaurant recommendation expert. Your task is to rank restaurant candidates based on user preferences and provide clear, helpful explanations.

Rank the restaurants from most to least suitable for the user. Consider:
1. Cuisine match with user preferences
2. Budget alignment (cost for two people)
3. Rating quality
4. Location convenience
5. Any additional preferences the user specified (e.g. ambience, dietary needs, family-friendly)
6. Overall value proposition

For each restaurant, provide:
- A relevance score (0-100)
- A concise explanation (1-2 sentences) explaining why it's a good match
- Key highlights that make it stand out

Return your response in the following JSON format:
{
  "rankings": [
    {
      "rank": 1,
      "restaurant_name": "Restaurant Name",
      "relevance_score": 95,
      "explanation": "Perfect match for Italian cuisine lovers with excellent ratings and reasonable prices.",
      "highlights": ["Authentic Italian", "Highly rated", "Good value"]
    }
  ],
  "summary": "Brief summary of recommendations"
}"""

    def build_ranking_prompt(self, preferences: UserPreferences, candidates: List[RestaurantCandidate]) -> str:
        """Build a complete prompt for restaurant ranking"""
        
        user_context = self._format_user_preferences(preferences)
        candidates_context = self._format_candidates(candidates)
        
        full_prompt = f"""{self.system_prompt}

USER PREFERENCES:
{user_context}

RESTAURANT CANDIDATES:
{candidates_context}

Please rank these restaurants and provide explanations as specified in the JSON format above."""
        
        return full_prompt
    
    def _format_user_preferences(self, preferences: UserPreferences) -> str:
        """Format user preferences for the prompt"""
        lines = [
            f"- Location: {preferences.location}",
            f"- Budget: {preferences.budget}",
            f"- Preferred Cuisine: {preferences.cuisine}",
            f"- Minimum Rating: {preferences.min_rating}/5.0",
        ]
        extra = (preferences.additional_preferences or "").strip()
        if extra:
            lines.append(f"- Additional preferences: {extra}")
        return "\n".join(lines)
    
    def _format_candidates(self, candidates: List[RestaurantCandidate]) -> str:
        """Format restaurant candidates for the prompt"""
        if not candidates:
            return "No restaurant candidates available."
        
        formatted_candidates = []
        for i, restaurant in enumerate(candidates, 1):
            candidate_text = f"""{i}. {restaurant.name}
   - Cuisines: {', '.join(restaurant.cuisines)}
   - Rating: {restaurant.rating}/5.0
   - Cost for Two: ${restaurant.cost_for_two}
   - Location: {restaurant.location}
   - Votes: {restaurant.votes}"""
            formatted_candidates.append(candidate_text)
        
        return '\n\n'.join(formatted_candidates)
    
    def build_fallback_prompt(self, preferences: UserPreferences) -> str:
        """Build a prompt when no candidates are available"""
        user_context = self._format_user_preferences(preferences)
        
        return f"""{self.system_prompt}

USER PREFERENCES:
{user_context}

No restaurant candidates were found that match the user's criteria. Please provide a helpful response suggesting:
1. Alternative search strategies
2. Broader location or cuisine options
3. Budget range adjustments

Return in JSON format:
{
  "rankings": [],
  "summary": "No matches found. Consider expanding your search criteria...",
  "suggestions": ["Try nearby locations", "Consider different cuisines", "Adjust budget range"]
}"""
