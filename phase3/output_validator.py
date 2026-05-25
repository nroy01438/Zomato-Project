"""
Output Schema and Validator

Validates and parses LLM responses with retry logic for invalid outputs.
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pydantic import BaseModel, ValidationError, Field

logger = logging.getLogger(__name__)


class RestaurantRanking(BaseModel):
    """Schema for individual restaurant ranking"""
    rank: int = Field(..., ge=1, description="Rank position")
    restaurant_name: str = Field(..., min_length=1, description="Restaurant name")
    relevance_score: int = Field(..., ge=0, le=100, description="Relevance score 0-100")
    explanation: str = Field(..., min_length=1, description="Why this restaurant is recommended")
    highlights: List[str] = Field(default_factory=list, description="Key highlights")


class RecommendationResponse(BaseModel):
    """Schema for complete recommendation response"""
    rankings: List[RestaurantRanking] = Field(default_factory=list, description="Ranked restaurant list")
    summary: str = Field(..., min_length=1, description="Summary of recommendations")
    suggestions: Optional[List[str]] = Field(default=None, description="Alternative suggestions")


@dataclass
class ValidationResult:
    """Result of validation attempt"""
    is_valid: bool
    parsed_data: Optional[RecommendationResponse] = None
    error_message: Optional[str] = None
    raw_response: Optional[str] = None


class OutputValidator:
    """Validates and parses LLM responses with retry logic"""
    
    def __init__(self, max_retries: int = 3, fallback_enabled: bool = True):
        self.max_retries = max_retries
        self.fallback_enabled = fallback_enabled
    
    def validate_and_parse(self, llm_response: str) -> ValidationResult:
        """Validate and parse LLM response"""
        try:
            # Clean and extract JSON from response
            cleaned_json = self._extract_json(llm_response)
            
            if not cleaned_json:
                return ValidationResult(
                    is_valid=False,
                    error_message="No valid JSON found in response",
                    raw_response=llm_response
                )
            
            # Parse JSON and validate schema
            parsed_data = json.loads(cleaned_json)
            validated_response = RecommendationResponse(**parsed_data)
            
            # Additional business logic validation
            if self._validate_business_rules(validated_response):
                return ValidationResult(
                    is_valid=True,
                    parsed_data=validated_response,
                    raw_response=llm_response
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    error_message="Response failed business rule validation",
                    raw_response=llm_response
                )
                
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"JSON parsing error: {str(e)}",
                raw_response=llm_response
            )
        except ValidationError as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Schema validation error: {str(e)}",
                raw_response=llm_response
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unexpected validation error: {str(e)}",
                raw_response=llm_response
            )
    
    def _extract_json(self, response: str) -> Optional[str]:
        """Extract JSON from LLM response"""
        # Try to find JSON between ```json and ``` markers
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try to find JSON between { and } (first occurrence)
        brace_pattern = r'\{.*\}'
        match = re.search(brace_pattern, response, re.DOTALL)
        if match:
            return match.group(0).strip()
        
        # Try to parse the entire response as JSON
        try:
            json.loads(response.strip())
            return response.strip()
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _validate_business_rules(self, response: RecommendationResponse) -> bool:
        """Validate business logic rules"""
        # Check rankings are sequential
        if response.rankings:
            expected_ranks = list(range(1, len(response.rankings) + 1))
            actual_ranks = [ranking.rank for ranking in response.rankings]
            if actual_ranks != expected_ranks:
                logger.warning(f"Rank positions not sequential: expected {expected_ranks}, got {actual_ranks}")
                return False
        
        # Check relevance scores are within bounds
        for ranking in response.rankings:
            if not (0 <= ranking.relevance_score <= 100):
                logger.warning(f"Invalid relevance score: {ranking.relevance_score}")
                return False
        
        # Check summary exists
        if not response.summary or len(response.summary.strip()) == 0:
            logger.warning("Empty summary")
            return False
        
        return True
    
    def create_fallback_response(self, error_message: str) -> RecommendationResponse:
        """Create a fallback response when validation fails"""
        return RecommendationResponse(
            rankings=[],
            summary="Unable to generate recommendations due to a technical issue. Please try again.",
            suggestions=["Try again later", "Contact support if issue persists"]
        )
    
    def format_error_for_retry(self, validation_result: ValidationResult) -> str:
        """Format validation error for retry prompt"""
        error_context = f"""
The previous response was invalid. Please fix the following issues:

ERROR: {validation_result.error_message}

INVALID RESPONSE:
{validation_result.raw_response}

Please provide a valid response in the exact JSON format specified:
{{
  "rankings": [
    {{
      "rank": 1,
      "restaurant_name": "Restaurant Name",
      "relevance_score": 95,
      "explanation": "Brief explanation",
      "highlights": ["highlight1", "highlight2"]
    }}
  ],
  "summary": "Brief summary of recommendations"
}}

Requirements:
- Rankings must be sequential (1, 2, 3...)
- Relevance scores must be 0-100
- All string fields must be non-empty
- Response must be valid JSON
"""
        return error_context


class RetryHandler:
    """Handles retry logic for failed LLM responses"""
    
    def __init__(self, validator: OutputValidator, llm_client):
        self.validator = validator
        self.llm_client = llm_client
    
    async def get_validated_response(self, prompt: str, max_retries: Optional[int] = None) -> Tuple[RecommendationResponse, int]:
        """Get validated response with retries"""
        max_retries = max_retries or self.validator.max_retries
        last_validation_result = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                if attempt == 0:
                    # First attempt
                    response = await self.llm_client.generate_response(prompt)
                else:
                    # Retry with error context
                    retry_prompt = prompt + self.validator.format_error_for_retry(last_validation_result)
                    response = await self.llm_client.generate_response(retry_prompt)
                
                # Validate response
                validation_result = self.validator.validate_and_parse(response)
                
                if validation_result.is_valid:
                    logger.info(f"Valid response obtained on attempt {attempt + 1}")
                    return validation_result.parsed_data, attempt + 1
                else:
                    last_validation_result = validation_result
                    logger.warning(f"Validation failed on attempt {attempt + 1}: {validation_result.error_message}")
                    
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}")
                last_validation_result = ValidationResult(
                    is_valid=False,
                    error_message=str(e),
                    raw_response=None
                )
        
        # All retries failed, return fallback
        logger.error(f"All {max_retries + 1} attempts failed, using fallback response")
        fallback_response = self.validator.create_fallback_response(
            last_validation_result.error_message if last_validation_result else "Unknown error"
        )
        return fallback_response, max_retries + 1
