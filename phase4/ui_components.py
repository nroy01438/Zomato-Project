"""
UI Components for Results Rendering

Provides components for displaying restaurant recommendations
in different formats (cards, tables, etc.).
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# Import from Phase 3
try:
    from ..phase3.output_validator import RecommendationResponse, RestaurantRanking
except ImportError:
    from phase3.output_validator import RecommendationResponse, RestaurantRanking


@dataclass
class RenderConfig:
    """Configuration for UI rendering"""
    theme: str = "modern"  # modern, classic, minimal
    show_scores: bool = True
    show_highlights: bool = True
    max_items_per_page: int = 10
    currency_symbol: str = "$"


class UIComponents:
    """UI components for rendering restaurant recommendations"""
    
    def __init__(self, config: Optional[RenderConfig] = None):
        self.config = config or RenderConfig()
    
    def render_cards(self, response: RecommendationResponse) -> Dict[str, Any]:
        """Render recommendations as card layout"""
        cards = []
        
        for ranking in response.rankings:
            card = self._create_card(ranking)
            cards.append(card)
        
        return {
            "layout": "cards",
            "summary": response.summary,
            "total_results": len(response.rankings),
            "cards": cards,
            "suggestions": response.suggestions or []
        }
    
    def _create_card(self, ranking: RestaurantRanking) -> Dict[str, Any]:
        """Create individual card for a restaurant"""
        card = {
            "rank": ranking.rank,
            "restaurant_name": ranking.restaurant_name,
            "explanation": ranking.explanation
        }
        
        if self.config.show_scores:
            card["relevance_score"] = {
                "value": ranking.relevance_score,
                "display": f"{ranking.relevance_score}/100",
                "color": self._get_score_color(ranking.relevance_score)
            }
        
        if self.config.show_highlights and ranking.highlights:
            card["highlights"] = ranking.highlights
        
        return card
    
    def _get_score_color(self, score: int) -> str:
        """Get color based on relevance score"""
        if score >= 90:
            return "#10b981"  # green
        elif score >= 75:
            return "#3b82f6"  # blue
        elif score >= 60:
            return "#f59e0b"  # amber
        else:
            return "#6b7280"  # gray
    
    def render_table(self, response: RecommendationResponse) -> Dict[str, Any]:
        """Render recommendations as table layout"""
        headers = ["Rank", "Restaurant", "Score", "Explanation"]
        rows = []
        
        for ranking in response.rankings:
            row = [
                ranking.rank,
                ranking.restaurant_name,
                f"{ranking.relevance_score}/100" if self.config.show_scores else "N/A",
                ranking.explanation
            ]
            
            if self.config.show_highlights and ranking.highlights:
                row.append(", ".join(ranking.highlights))
                if len(headers) == 4:  # Add highlights header if not present
                    headers.append("Highlights")
            
            rows.append(row)
        
        return {
            "layout": "table",
            "summary": response.summary,
            "total_results": len(response.rankings),
            "headers": headers,
            "rows": rows,
            "suggestions": response.suggestions or []
        }
    
    def render_compact(self, response: RecommendationResponse) -> Dict[str, Any]:
        """Render recommendations in compact format"""
        items = []
        
        for ranking in response.rankings:
            item = f"{ranking.rank}. {ranking.restaurant_name}"
            if self.config.show_scores:
                item += f" ({ranking.relevance_score}/100)"
            items.append(item)
        
        return {
            "layout": "compact",
            "summary": response.summary,
            "total_results": len(response.rankings),
            "items": items,
            "suggestions": response.suggestions or []
        }
    
    def render_detailed(self, response: RecommendationResponse) -> Dict[str, Any]:
        """Render recommendations with full details"""
        details = []
        
        for ranking in response.rankings:
            detail = {
                "rank": ranking.rank,
                "restaurant_name": ranking.restaurant_name,
                "explanation": ranking.explanation,
                "metadata": {}
            }
            
            if self.config.show_scores:
                detail["metadata"]["relevance_score"] = ranking.relevance_score
                detail["metadata"]["score_category"] = self._get_score_category(ranking.relevance_score)
            
            if self.config.show_highlights and ranking.highlights:
                detail["metadata"]["highlights"] = ranking.highlights
            
            details.append(detail)
        
        return {
            "layout": "detailed",
            "summary": response.summary,
            "total_results": len(response.rankings),
            "details": details,
            "suggestions": response.suggestions or []
        }
    
    def _get_score_category(self, score: int) -> str:
        """Get category based on relevance score"""
        if score >= 90:
            return "Excellent Match"
        elif score >= 75:
            return "Great Match"
        elif score >= 60:
            return "Good Match"
        else:
            return "Fair Match"
    
    def render_json(self, response: RecommendationResponse) -> Dict[str, Any]:
        """Render recommendations as JSON API response"""
        return {
            "success": True,
            "data": {
                "summary": response.summary,
                "total_results": len(response.rankings),
                "rankings": [
                    {
                        "rank": ranking.rank,
                        "restaurant_name": ranking.restaurant_name,
                        "relevance_score": ranking.relevance_score,
                        "explanation": ranking.explanation,
                        "highlights": ranking.highlights
                    }
                    for ranking in response.rankings
                ],
                "suggestions": response.suggestions or []
            }
        }
    
    def render_html_cards(self, response: RecommendationResponse) -> str:
        """Render recommendations as HTML cards"""
        html_cards = []
        
        for ranking in response.rankings:
            card_html = self._create_html_card(ranking)
            html_cards.append(card_html)
        
        html = f"""
        <div class="restaurant-recommendations">
            <div class="summary">
                <h2>Restaurant Recommendations</h2>
                <p>{response.summary}</p>
            </div>
            <div class="cards-container">
                {''.join(html_cards)}
            </div>
        </div>
        """
        
        return html.strip()
    
    def _create_html_card(self, ranking: RestaurantRanking) -> str:
        """Create HTML card for a restaurant"""
        score_color = self._get_score_color(ranking.relevance_score)
        
        highlights_html = ""
        if self.config.show_highlights and ranking.highlights:
            highlights_html = f"""
            <div class="highlights">
                <strong>Highlights:</strong>
                <ul>
                    {''.join(f'<li>{highlight}</li>' for highlight in ranking.highlights)}
                </ul>
            </div>
            """
        
        score_html = ""
        if self.config.show_scores:
            score_html = f"""
            <div class="score" style="color: {score_color};">
                <strong>Relevance:</strong> {ranking.relevance_score}/100
            </div>
            """
        
        return f"""
        <div class="restaurant-card">
            <div class="rank">#{ranking.rank}</div>
            <div class="restaurant-name">
                <h3>{ranking.restaurant_name}</h3>
            </div>
            {score_html}
            <div class="explanation">
                <p>{ranking.explanation}</p>
            </div>
            {highlights_html}
        </div>
        """
    
    def render_html_table(self, response: RecommendationResponse) -> str:
        """Render recommendations as HTML table"""
        headers = ["Rank", "Restaurant", "Score", "Explanation"]
        rows = []
        
        for ranking in response.rankings:
            score_cell = f"<td>{ranking.relevance_score}/100</td>" if self.config.show_scores else "<td>N/A</td>"
            
            highlights_cell = ""
            if self.config.show_highlights and ranking.highlights:
                highlights_cell = f"<td>{', '.join(ranking.highlights)}</td>"
                if "Highlights" not in headers:
                    headers.append("Highlights")
            
            row = f"""
            <tr>
                <td>{ranking.rank}</td>
                <td><strong>{ranking.restaurant_name}</strong></td>
                {score_cell}
                <td>{ranking.explanation}</td>
                {highlights_cell}
            </tr>
            """
            rows.append(row)
        
        header_row = "".join(f"<th>{header}</th>" for header in headers)
        
        return f"""
        <div class="restaurant-recommendations">
            <div class="summary">
                <h2>Restaurant Recommendations</h2>
                <p>{response.summary}</p>
            </div>
            <table class="restaurant-table">
                <thead>
                    <tr>{header_row}</tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """.strip()
    
    def get_css_styles(self) -> str:
        """Get CSS styles for HTML rendering"""
        return """
        <style>
        .restaurant-recommendations {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .summary {
            margin-bottom: 30px;
            text-align: center;
        }
        
        .cards-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .restaurant-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .restaurant-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .rank {
            font-size: 24px;
            font-weight: bold;
            color: #6b7280;
            margin-bottom: 10px;
        }
        
        .restaurant-name h3 {
            margin: 0 0 10px 0;
            color: #1f2937;
        }
        
        .score {
            font-weight: bold;
            margin: 10px 0;
        }
        
        .explanation {
            color: #4b5563;
            line-height: 1.5;
            margin: 15px 0;
        }
        
        .highlights {
            margin-top: 15px;
        }
        
        .highlights ul {
            margin: 5px 0;
            padding-left: 20px;
        }
        
        .highlights li {
            margin: 3px 0;
            color: #059669;
        }
        
        .restaurant-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .restaurant-table th,
        .restaurant-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .restaurant-table th {
            background-color: #f9fafb;
            font-weight: bold;
            color: #374151;
        }
        
        .restaurant-table tr:hover {
            background-color: #f9fafb;
        }
        </style>
        """
