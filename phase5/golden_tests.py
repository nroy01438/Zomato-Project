"""
Golden Test Cases for Restaurant Recommendation System

Fixed inputs with expected structured output shapes for regression testing.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import asyncio

# Import from previous phases
try:
    from ..phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from ..phase3.output_validator import RecommendationResponse, RestaurantRanking
except ImportError:
    from phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from phase3.output_validator import RecommendationResponse, RestaurantRanking


@dataclass
class GoldenTestCase:
    """Represents a golden test case with input and expected output"""
    name: str
    description: str
    input_preferences: UserPreferences
    input_candidates: List[RestaurantCandidate]
    expected_output_shape: Dict[str, Any]
    expected_behavior: str


class GoldenTestSuite:
    """Manages and executes golden test cases"""
    
    def __init__(self):
        self.test_cases = self._create_test_cases()
    
    def _create_test_cases(self) -> List[GoldenTestCase]:
        """Create comprehensive golden test cases"""
        
        test_cases = []
        
        # Test Case 1: Basic Italian Restaurant Search
        test_cases.append(GoldenTestCase(
            name="basic_italian_search",
            description="Basic search for Italian restaurants in New York with medium budget",
            input_preferences=UserPreferences(
                location="New York",
                budget="Medium",
                cuisine="Italian",
                min_rating=4.0
            ),
            input_candidates=[
                RestaurantCandidate(
                    name="Tony's Italian Bistro",
                    cuisines=["Italian", "Pizza"],
                    rating=4.5,
                    cost_for_two=60,
                    location="New York",
                    votes=1250
                ),
                RestaurantCandidate(
                    name="Luigi's Trattoria",
                    cuisines=["Italian", "Mediterranean"],
                    rating=4.2,
                    cost_for_two=45,
                    location="New York",
                    votes=890
                )
            ],
            expected_output_shape={
                "rankings_count": 2,
                "min_rank": 1,
                "max_rank": 2,
                "summary_min_length": 10,
                "summary_contains": ["restaurant", "recommend"],
                "relevance_score_range": [0, 100],
                "explanation_min_length": 5,
                "highlights_present": True
            },
            expected_behavior="Should rank Italian restaurants by relevance score with explanations"
        ))
        
        # Test Case 2: High Budget Constraint
        test_cases.append(GoldenTestCase(
            name="high_budget_constraint",
            description="Search with high budget constraint in San Francisco",
            input_preferences=UserPreferences(
                location="San Francisco",
                budget="High",
                cuisine="Japanese",
                min_rating=4.5
            ),
            input_candidates=[
                RestaurantCandidate(
                    name="Sushi Master",
                    cuisines=["Japanese", "Sushi"],
                    rating=4.7,
                    cost_for_two=90,
                    location="San Francisco",
                    votes=890
                ),
                RestaurantCandidate(
                    name="Tokyo Dreams",
                    cuisines=["Japanese", "Ramen"],
                    rating=4.5,
                    cost_for_two=60,
                    location="San Francisco",
                    votes=2100
                ),
                RestaurantCandidate(
                    name="Quick Sushi",
                    cuisines=["Japanese", "Fast Food"],
                    rating=3.9,
                    cost_for_two=40,
                    location="San Francisco",
                    votes=1500
                )
            ],
            expected_output_shape={
                "rankings_count": 2,  # Only 4.5+ rated
                "min_rank": 1,
                "max_rank": 2,
                "summary_min_length": 10,
                "relevance_score_range": [0, 100],
                "explanation_min_length": 5,
                "highlights_present": True
            },
            expected_behavior="Should filter out low-rated restaurant and rank remaining by relevance"
        ))
        
        # Test Case 3: No Matching Candidates
        test_cases.append(GoldenTestCase(
            name="no_matching_candidates",
            description="Search with constraints that match no candidates",
            input_preferences=UserPreferences(
                location="Boston",
                budget="Low",
                cuisine="French",
                min_rating=4.8
            ),
            input_candidates=[
                RestaurantCandidate(
                    name="Cafe Paris",
                    cuisines=["French", "Cafe"],
                    rating=4.2,
                    cost_for_two=80,
                    location="Boston",
                    votes=300
                ),
                RestaurantCandidate(
                    name="Le Bistro",
                    cuisines=["French", "Bistro"],
                    rating=4.5,
                    cost_for_two=120,
                    location="Boston",
                    votes=450
                )
            ],
            expected_output_shape={
                "rankings_count": 0,
                "min_rank": None,
                "max_rank": None,
                "summary_min_length": 10,
                "suggestions_present": True,
                "explanation_min_length": 0
            },
            expected_behavior="Should return empty rankings with suggestions for alternatives"
        ))
        
        # Test Case 4: Multiple Cuisine Types
        test_cases.append(GoldenTestCase(
            name="multiple_cuisine_types",
            description="Search with diverse cuisine candidates",
            input_preferences=UserPreferences(
                location="Chicago",
                budget="Medium",
                cuisine="Asian",
                min_rating=3.5
            ),
            input_candidates=[
                RestaurantCandidate(
                    name="Sushi Place",
                    cuisines=["Japanese", "Asian"],
                    rating=4.3,
                    cost_for_two=70,
                    location="Chicago",
                    votes=800
                ),
                RestaurantCandidate(
                    name="Thai Kitchen",
                    cuisines=["Thai", "Asian"],
                    rating=4.1,
                    cost_for_two=50,
                    location="Chicago",
                    votes=600
                ),
                RestaurantCandidate(
                    name="Chinese Dragon",
                    cuisines=["Chinese", "Asian"],
                    rating=4.0,
                    cost_for_two=45,
                    location="Chicago",
                    votes=900
                )
            ],
            expected_output_shape={
                "rankings_count": 3,
                "min_rank": 1,
                "max_rank": 3,
                "summary_min_length": 10,
                "relevance_score_range": [0, 100],
                "explanation_min_length": 5,
                "highlights_present": True
            },
            expected_behavior="Should rank diverse Asian restaurants with good diversity"
        ))
        
        # Test Case 5: Edge Case - Single Candidate
        test_cases.append(GoldenTestCase(
            name="single_candidate",
            description="Search with only one matching candidate",
            input_preferences=UserPreferences(
                location="Seattle",
                budget="Medium",
                cuisine="American",
                min_rating=4.0
            ),
            input_candidates=[
                RestaurantCandidate(
                    name="Burger Joint",
                    cuisines=["American", "Burgers"],
                    rating=4.2,
                    cost_for_two=40,
                    location="Seattle",
                    votes=2100
                )
            ],
            expected_output_shape={
                "rankings_count": 1,
                "min_rank": 1,
                "max_rank": 1,
                "summary_min_length": 10,
                "relevance_score_range": [0, 100],
                "explanation_min_length": 5,
                "highlights_present": True
            },
            expected_behavior="Should return single ranking with highest relevance score"
        ))
        
        return test_cases
    
    async def run_test_case(self, test_case: GoldenTestCase, orchestrator) -> Dict[str, Any]:
        """Run a single golden test case"""
        
        try:
            # Generate recommendations
            response = await orchestrator.generate_recommendations(
                test_case.input_preferences, 
                test_case.input_candidates
            )
            
            # Validate output shape
            validation_results = self._validate_output_shape(response, test_case.expected_output_shape)
            
            return {
                "test_name": test_case.name,
                "description": test_case.description,
                "passed": all(result["passed"] for result in validation_results),
                "validation_results": validation_results,
                "response": response,
                "expected_behavior": test_case.expected_behavior
            }
            
        except Exception as e:
            return {
                "test_name": test_case.name,
                "description": test_case.description,
                "passed": False,
                "error": str(e),
                "expected_behavior": test_case.expected_behavior
            }
    
    def _validate_output_shape(self, response: RecommendationResponse, expected_shape: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate response shape against expected structure"""
        
        results = []
        
        # Check rankings count
        actual_count = len(response.rankings)
        expected_count = expected_shape.get("rankings_count", 0)
        results.append({
            "check": "rankings_count",
            "expected": expected_count,
            "actual": actual_count,
            "passed": actual_count == expected_count,
            "message": f"Rankings count: {actual_count} (expected: {expected_count})"
        })
        
        # Check rank sequence
        if response.rankings:
            actual_ranks = [r.rank for r in response.rankings]
            expected_min = expected_shape.get("min_rank")
            expected_max = expected_shape.get("max_rank")
            
            if expected_min is not None and expected_max is not None:
                expected_ranks = list(range(expected_min, expected_max + 1))
                rank_sequence_correct = actual_ranks == expected_ranks
                results.append({
                    "check": "rank_sequence",
                    "expected": expected_ranks,
                    "actual": actual_ranks,
                    "passed": rank_sequence_correct,
                    "message": f"Rank sequence: {actual_ranks} (expected: {expected_ranks})"
                })
        
        # Check summary length
        summary_length = len(response.summary)
        min_summary_length = expected_shape.get("summary_min_length", 0)
        results.append({
            "check": "summary_length",
            "expected": f">={min_summary_length}",
            "actual": summary_length,
            "passed": summary_length >= min_summary_length,
            "message": f"Summary length: {summary_length} (min: {min_summary_length})"
        })
        
        # Check summary content
        summary_contains = expected_shape.get("summary_contains", [])
        if summary_contains:
            summary_lower = response.summary.lower()
            all_words_found = all(word.lower() in summary_lower for word in summary_contains)
            results.append({
                "check": "summary_content",
                "expected": summary_contains,
                "actual": response.summary,
                "passed": all_words_found,
                "message": f"Summary contains required words: {all_words_found}"
            })
        
        # Check relevance score range
        if response.rankings:
            scores = [r.relevance_score for r in response.rankings]
            min_score, max_score = min(scores), max(scores)
            expected_range = expected_shape.get("relevance_score_range", [0, 100])
            
            score_range_valid = (
                min_score >= expected_range[0] and 
                max_score <= expected_range[1]
            )
            results.append({
                "check": "relevance_score_range",
                "expected": expected_range,
                "actual": [min_score, max_score],
                "passed": score_range_valid,
                "message": f"Score range: [{min_score}, {max_score}] (expected: {expected_range})"
            })
        
        # Check explanation length
        if response.rankings:
            explanation_lengths = [len(r.explanation) for r in response.rankings]
            min_exp_length = expected_shape.get("explanation_min_length", 0)
            
            exp_lengths_valid = all(length >= min_exp_length for length in explanation_lengths)
            results.append({
                "check": "explanation_length",
                "expected": f">={min_exp_length}",
                "actual": explanation_lengths,
                "passed": exp_lengths_valid,
                "message": f"Explanation lengths: {explanation_lengths} (min: {min_exp_length})"
            })
        
        # Check highlights presence
        highlights_expected = expected_shape.get("highlights_present", False)
        if highlights_expected:
            highlights_present = all(
                hasattr(r, 'highlights') and r.highlights 
                for r in response.rankings
            )
            results.append({
                "check": "highlights_present",
                "expected": True,
                "actual": highlights_present,
                "passed": highlights_present,
                "message": f"Highlights present: {highlights_present}"
            })
        
        # Check suggestions presence when no rankings
        suggestions_expected = expected_shape.get("suggestions_present", False)
        if not response.rankings and suggestions_expected:
            suggestions_present = (
                hasattr(response, 'suggestions') and 
                response.suggestions and 
                len(response.suggestions) > 0
            )
            results.append({
                "check": "suggestions_present",
                "expected": True,
                "actual": suggestions_present,
                "passed": suggestions_present,
                "message": f"Suggestions present: {suggestions_present}"
            })
        
        return results
    
    async def run_all_tests(self, orchestrator) -> Dict[str, Any]:
        """Run all golden test cases"""
        
        results = []
        
        for test_case in self.test_cases:
            print(f"🧪 Running test: {test_case.name}")
            result = await self.run_test_case(test_case, orchestrator)
            results.append(result)
            
            # Print result summary
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"   {status} - {test_case.description}")
            
            if not result["passed"] and "error" in result:
                print(f"   Error: {result['error']}")
            else:
                failed_checks = [r for r in result["validation_results"] if not r["passed"]]
                if failed_checks:
                    print(f"   Failed checks: {[r['check'] for r in failed_checks]}")
        
        # Calculate overall metrics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r["passed"])
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "pass_rate": pass_rate,
            "test_results": results,
            "summary": f"Golden Tests: {passed_tests}/{total_tests} passed ({pass_rate:.1%})"
        }
    
    def get_test_report(self, results: Dict[str, Any]) -> str:
        """Generate formatted test report"""
        
        report = []
        report.append("=" * 80)
        report.append("🧪 GOLDEN TEST SUITE RESULTS")
        report.append("=" * 80)
        report.append(f"📊 Summary: {results['summary']}")
        report.append(f"📈 Pass Rate: {results['pass_rate']:.1%}")
        report.append("")
        
        for test_result in results["test_results"]:
            status = "✅ PASS" if test_result["passed"] else "❌ FAIL"
            report.append(f"{status} - {test_result['name']}")
            report.append(f"   {test_result['description']}")
            
            if not test_result["passed"]:
                if "error" in test_result:
                    report.append(f"   ❌ Error: {test_result['error']}")
                else:
                    failed_checks = [r for r in test_result["validation_results"] if not r["passed"]]
                    for check in failed_checks:
                        report.append(f"   ❌ {check['message']}")
            
            report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)
    
    def save_test_results(self, results: Dict[str, Any], filepath: str):
        """Save test results to file"""
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📁 Test results saved to: {filepath}")
        except Exception as e:
            print(f"❌ Failed to save test results: {e}")
