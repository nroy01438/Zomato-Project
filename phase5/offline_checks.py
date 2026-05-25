"""
Offline Checks for Restaurant Recommendation System

Implements constraint satisfaction, diversity, and coverage checks
to prevent regressions and ensure quality.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from collections import defaultdict, Counter

# Import from previous phases
try:
    from ..phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from ..phase3.output_validator import RecommendationResponse, RestaurantRanking
except ImportError:
    from phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from phase3.output_validator import RecommendationResponse, RestaurantRanking


@dataclass
class CheckResult:
    """Result of an offline check"""
    check_name: str
    passed: bool
    score: float
    details: Dict[str, Any]
    message: str


@dataclass
class OfflineCheckReport:
    """Complete report of all offline checks"""
    total_checks: int
    passed_checks: int
    failed_checks: int
    overall_score: float
    check_results: List[CheckResult]
    recommendations: List[str]


class OfflineChecks:
    """Implements offline quality checks for recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def run_all_checks(self, 
                    preferences: UserPreferences,
                    candidates: List[RestaurantCandidate],
                    response: RecommendationResponse) -> OfflineCheckReport:
        """Run all offline checks and return comprehensive report"""
        
        self.logger.info("Running offline checks for recommendation quality")
        
        all_results = []
        
        # Constraint Satisfaction Checks
        constraint_results = self._check_constraint_satisfaction(preferences, candidates, response)
        all_results.extend(constraint_results)
        
        # Diversity Checks
        diversity_results = self._check_diversity(candidates, response)
        all_results.extend(diversity_results)
        
        # Coverage Checks
        coverage_results = self._check_coverage(preferences, candidates, response)
        all_results.extend(coverage_results)
        
        # Ranking Quality Checks
        ranking_results = self._check_ranking_quality(response)
        all_results.extend(ranking_results)
        
        # Business Logic Checks
        business_results = self._check_business_logic(preferences, response)
        all_results.extend(business_results)
        
        # Calculate overall metrics
        total_checks = len(all_results)
        passed_checks = sum(1 for result in all_results if result.passed)
        failed_checks = total_checks - passed_checks
        overall_score = passed_checks / total_checks if total_checks > 0 else 0.0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_results)
        
        return OfflineCheckReport(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            overall_score=overall_score,
            check_results=all_results,
            recommendations=recommendations
        )
    
    def _check_constraint_satisfaction(self, 
                                 preferences: UserPreferences,
                                 candidates: List[RestaurantCandidate],
                                 response: RecommendationResponse) -> List[CheckResult]:
        """Check if constraints are satisfied"""
        
        results = []
        
        # Check location constraint
        location_satisfied = all(
            candidate.location.lower() == preferences.location.lower()
            for candidate in candidates
        )
        results.append(CheckResult(
            check_name="Location Constraint",
            passed=location_satisfied,
            score=1.0 if location_satisfied else 0.0,
            details={"required_location": preferences.location, "candidates": [c.location for c in candidates]},
            message=f"Location constraint {'satisfied' if location_satisfied else 'not satisfied'}"
        ))
        
        # Check budget constraint
        budget_ranges = {"Low": (0, 1500), "Medium": (1500, 3000), "High": (3000, float('inf'))}
        min_budget, max_budget = budget_ranges.get(preferences.budget, (0, float('inf')))
        
        budget_satisfied = all(
            min_budget <= candidate.cost_for_two <= max_budget
            for candidate in candidates
        )
        results.append(CheckResult(
            check_name="Budget Constraint",
            passed=budget_satisfied,
            score=1.0 if budget_satisfied else 0.0,
            details={
                "budget_range": preferences.budget,
                "min_budget": min_budget,
                "max_budget": max_budget,
                "candidate_costs": [c.cost_for_two for c in candidates]
            },
            message=f"Budget constraint {'satisfied' if budget_satisfied else 'not satisfied'}"
        ))
        
        # Check rating constraint
        rating_satisfied = all(
            candidate.rating >= preferences.min_rating
            for candidate in candidates
        )
        results.append(CheckResult(
            check_name="Rating Constraint",
            passed=rating_satisfied,
            score=1.0 if rating_satisfied else 0.0,
            details={
                "min_rating": preferences.min_rating,
                "candidate_ratings": [c.rating for c in candidates]
            },
            message=f"Rating constraint {'satisfied' if rating_satisfied else 'not satisfied'}"
        ))
        
        # Check cuisine constraint
        cuisine_satisfied = any(
            preferences.cuisine.lower() in [c.lower() for c in candidate.cuisines]
            for candidate in candidates
        )
        results.append(CheckResult(
            check_name="Cuisine Constraint",
            passed=cuisine_satisfied,
            score=1.0 if cuisine_satisfied else 0.0,
            details={
                "preferred_cuisine": preferences.cuisine,
                "candidate_cuisines": [c.cuisines for c in candidates]
            },
            message=f"Cuisine constraint {'satisfied' if cuisine_satisfied else 'not satisfied'}"
        ))
        
        return results
    
    def _check_diversity(self, 
                        candidates: List[RestaurantCandidate],
                        response: RecommendationResponse) -> List[CheckResult]:
        """Check diversity of recommendations"""
        
        results = []
        
        if not response.rankings:
            return results
        
        # Cuisine diversity
        cuisine_types = []
        for ranking in response.rankings:
            candidate = next((c for c in candidates if c.name == ranking.restaurant_name), None)
            if candidate:
                cuisine_types.extend(candidate.cuisines)
        
        unique_cuisines = len(set(cuisine_types))
        total_cuisines = len(cuisine_types)
        cuisine_diversity_score = unique_cuisines / total_cuisines if total_cuisines > 0 else 1.0
        
        results.append(CheckResult(
            check_name="Cuisine Diversity",
            passed=cuisine_diversity_score >= 0.5,  # At least 50% unique cuisines
            score=cuisine_diversity_score,
            details={
                "unique_cuisines": unique_cuisines,
                "total_cuisines": total_cuisines,
                "cuisine_list": cuisine_types
            },
            message=f"Cuisine diversity: {unique_cuisines}/{total_cuisines} unique"
        ))
        
        # Price range diversity
        prices = []
        for ranking in response.rankings:
            candidate = next((c for c in candidates if c.name == ranking.restaurant_name), None)
            if candidate:
                prices.append(candidate.cost_for_two)
        
        if prices:
            price_range = max(prices) - min(prices)
            avg_price = sum(prices) / len(prices)
            price_diversity_score = min(price_range / avg_price, 1.0) if avg_price > 0 else 0.0
            
            results.append(CheckResult(
                check_name="Price Diversity",
                passed=price_diversity_score >= 0.3,  # At least 30% price range variation
                score=price_diversity_score,
                details={
                    "price_range": price_range,
                    "avg_price": avg_price,
                    "prices": prices
                },
                message=f"Price diversity: ₹{price_range:.0f} range"
            ))
        
        # Rating diversity
        ratings = []
        for ranking in response.rankings:
            candidate = next((c for c in candidates if c.name == ranking.restaurant_name), None)
            if candidate:
                ratings.append(candidate.rating)
        
        if ratings:
            rating_range = max(ratings) - min(ratings)
            avg_rating = sum(ratings) / len(ratings)
            rating_diversity_score = min(rating_range / avg_rating, 1.0) if avg_rating > 0 else 0.0
            
            results.append(CheckResult(
                check_name="Rating Diversity",
                passed=rating_diversity_score >= 0.1,  # At least 10% rating variation
                score=rating_diversity_score,
                details={
                    "rating_range": rating_range,
                    "avg_rating": avg_rating,
                    "ratings": ratings
                },
                message=f"Rating diversity: {rating_range:.1f} range"
            ))
        
        return results
    
    def _check_coverage(self, 
                    preferences: UserPreferences,
                    candidates: List[RestaurantCandidate],
                    response: RecommendationResponse) -> List[CheckResult]:
        """Check coverage of user preferences"""
        
        results = []
        
        if not response.rankings:
            return results
        
        # Location coverage
        recommended_locations = set()
        for ranking in response.rankings:
            candidate = next((c for c in candidates if c.name == ranking.restaurant_name), None)
            if candidate:
                recommended_locations.add(candidate.location)
        
        location_coverage = len(recommended_locations) > 0
        results.append(CheckResult(
            check_name="Location Coverage",
            passed=location_coverage,
            score=1.0 if location_coverage else 0.0,
            details={
                "required_location": preferences.location,
                "recommended_locations": list(recommended_locations)
            },
            message=f"Location coverage: {'covered' if location_coverage else 'not covered'}"
        ))
        
        # Budget coverage
        budget_ranges = {"Low": (0, 1500), "Medium": (1500, 3000), "High": (3000, float('inf'))}
        min_budget, max_budget = budget_ranges.get(preferences.budget, (0, float('inf')))
        
        budget_coverage = all(
            min_budget <= candidate.cost_for_two <= max_budget
            for ranking in response.rankings
            for candidate in [c for c in candidates if c.name == ranking.restaurant_name]
        )
        results.append(CheckResult(
            check_name="Budget Coverage",
            passed=budget_coverage,
            score=1.0 if budget_coverage else 0.0,
            details={
                "budget_range": preferences.budget,
                "min_budget": min_budget,
                "max_budget": max_budget
            },
            message=f"Budget coverage: {'covered' if budget_coverage else 'not covered'}"
        ))
        
        return results
    
    def _check_ranking_quality(self, response: RecommendationResponse) -> List[CheckResult]:
        """Check quality of ranking logic"""
        
        results = []
        
        if not response.rankings:
            return results
        
        # Check sequential ranking
        expected_ranks = list(range(1, len(response.rankings) + 1))
        actual_ranks = [ranking.rank for ranking in response.rankings]
        sequential_ranking = actual_ranks == expected_ranks
        
        results.append(CheckResult(
            check_name="Sequential Ranking",
            passed=sequential_ranking,
            score=1.0 if sequential_ranking else 0.0,
            details={
                "expected_ranks": expected_ranks,
                "actual_ranks": actual_ranks
            },
            message=f"Ranking sequence: {'correct' if sequential_ranking else 'incorrect'}"
        ))
        
        # Check relevance score distribution
        scores = [ranking.relevance_score for ranking in response.rankings]
        if scores:
            avg_score = sum(scores) / len(scores)
            score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            
            # Good distribution should have some variance but not too much
            good_variance = 100 <= score_variance <= 400  # Reasonable variance range
            results.append(CheckResult(
                check_name="Score Distribution",
                passed=good_variance,
                score=1.0 if good_variance else 0.5,
                details={
                    "avg_score": avg_score,
                    "score_variance": score_variance,
                    "scores": scores
                },
                message=f"Score variance: {score_variance:.1f}"
            ))
        
        # Check explanation quality
        explanations = [ranking.explanation for ranking in response.rankings]
        explanation_lengths = [len(exp) for exp in explanations]
        
        if explanation_lengths:
            avg_length = sum(explanation_lengths) / len(explanation_lengths)
            good_explanations = 20 <= avg_length <= 200  # Reasonable explanation length
            
            results.append(CheckResult(
                check_name="Explanation Quality",
                passed=good_explanations,
                score=1.0 if good_explanations else 0.5,
                details={
                    "avg_length": avg_length,
                    "lengths": explanation_lengths
                },
                message=f"Explanation avg length: {avg_length:.0f} chars"
            ))
        
        return results
    
    def _check_business_logic(self, 
                          preferences: UserPreferences,
                          response: RecommendationResponse) -> List[CheckResult]:
        """Check business logic and edge cases"""
        
        results = []
        
        if not response.rankings:
            return results
        
        # Check for empty results when candidates exist
        has_recommendations = len(response.rankings) > 0
        results.append(CheckResult(
            check_name="Results Availability",
            passed=has_recommendations,
            score=1.0 if has_recommendations else 0.0,
            details={"recommendation_count": len(response.rankings)},
            message=f"Recommendations available: {has_recommendations}"
        ))
        
        # Check summary quality
        summary_quality = (
            len(response.summary) > 10 and  # Minimum length
            any(word in response.summary.lower() for word in ['restaurant', 'recommend', 'found', 'matching'])
        )
        
        results.append(CheckResult(
            check_name="Summary Quality",
            passed=summary_quality,
            score=1.0 if summary_quality else 0.5,
            details={"summary_length": len(response.summary)},
            message=f"Summary quality: {'good' if summary_quality else 'needs improvement'}"
        ))
        
        return results
    
    def _generate_recommendations(self, check_results: List[CheckResult]) -> List[str]:
        """Generate actionable recommendations based on check results"""
        
        recommendations = []
        
        failed_checks = [r for r in check_results if not r.passed]
        
        if failed_checks:
            recommendations.append("Fix failed constraint satisfaction checks")
            recommendations.append("Improve diversity in recommendations")
            recommendations.append("Enhance ranking quality logic")
            
            # Specific recommendations based on failed checks
            for check in failed_checks:
                if "Constraint" in check.check_name:
                    recommendations.append(f"Review {check.check_name.lower()} logic")
                elif "Diversity" in check.check_name:
                    recommendations.append(f"Improve {check.check_name.lower()}")
                elif "Ranking" in check.check_name:
                    recommendations.append(f"Fix {check.check_name.lower()}")
        
        if len(recommendations) == 0:
            recommendations.append("All checks passed - system performing well")
        
        return recommendations
    
    def get_check_summary(self, report: OfflineCheckReport) -> Dict[str, Any]:
        """Get summary of check results for reporting"""
        
        return {
            "overall_score": report.overall_score,
            "pass_rate": report.passed_checks / report.total_checks if report.total_checks > 0 else 0,
            "total_checks": report.total_checks,
            "passed_checks": report.passed_checks,
            "failed_checks": report.failed_checks,
            "critical_failures": [r.check_name for r in report.check_results if not r.passed],
            "recommendations": report.recommendations
        }
