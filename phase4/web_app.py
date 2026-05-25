"""
Web Application for Restaurant Recommendation System

Main web application that serves the frontend UI and integrates with the API.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from typing import Optional
import os
from .api_endpoints import APIEndpoints, APIConfig


def create_app(config: Optional[APIConfig] = None) -> Flask:
    """Create and configure the Flask web application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['DEBUG'] = config.debug if config else False
    
    # Enable CORS
    CORS(app)
    
    # Initialize API endpoints
    api_config = config or APIConfig()
    api = APIEndpoints(api_config)
    
    # Serve the main web UI
    @app.route('/')
    def index():
        """Serve the main web UI"""
        from flask import render_template_string
        return render_template_string(_get_web_ui_template(), 
                                    llm_provider=api_config.llm_provider)
    
    # Include all API endpoints
    app.register_blueprint(api.app, url_prefix='/api/v1')
    
    return app


def _get_web_ui_template() -> str:
    """Get the main web UI template"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍽️ AI Restaurant Recommendations</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .card-hover {
            transition: all 0.3s ease;
        }
        .card-hover:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .loading-spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="gradient-bg text-white shadow-lg">
        <div class="container mx-auto px-4 py-6">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-utensils text-3xl"></i>
                    <h1 class="text-2xl font-bold">AI Restaurant Recommendations</h1>
                </div>
                <div class="text-sm">
                    <span class="bg-white/20 px-3 py-1 rounded-full">
                        Powered by {{ llm_provider|title }}
                    </span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="container mx-auto px-4 py-8">
        <!-- Search Form -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 class="text-xl font-semibold mb-6 text-gray-800">
                <i class="fas fa-search mr-2"></i>Find Your Perfect Restaurant
            </h2>
            
            <form id="searchForm" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Location -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-map-marker-alt mr-1"></i>Location
                        </label>
                        <input type="text" 
                               id="location" 
                               name="location" 
                               required
                               class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                               placeholder="e.g., New York, San Francisco">
                    </div>
                    
                    <!-- Budget -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-dollar-sign mr-1"></i>Budget Range
                        </label>
                        <select id="budget" 
                                name="budget" 
                                required
                                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                            <option value="">Select budget</option>
                            <option value="Low">Low (< $30 for two)</option>
                            <option value="Medium">Medium ($30-80 for two)</option>
                            <option value="High">High (> $80 for two)</option>
                        </select>
                    </div>
                    
                    <!-- Cuisine -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-utensils mr-1"></i>Preferred Cuisine
                        </label>
                        <input type="text" 
                               id="cuisine" 
                               name="cuisine" 
                               required
                               class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                               placeholder="e.g., Italian, Japanese, Indian">
                    </div>
                    
                    <!-- Rating -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-star mr-1"></i>Minimum Rating
                        </label>
                        <select id="rating" 
                                name="rating" 
                                required
                                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                            <option value="">Select minimum rating</option>
                            <option value="0">Any rating</option>
                            <option value="3.0">3.0+ stars</option>
                            <option value="4.0">4.0+ stars</option>
                            <option value="4.5">4.5+ stars</option>
                        </select>
                    </div>
                </div>
                
                <!-- Submit Button -->
                <div class="flex justify-center">
                    <button type="submit" 
                            class="bg-purple-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-purple-700 transition duration-200 flex items-center space-x-2">
                        <i class="fas fa-search"></i>
                        <span>Get Recommendations</span>
                    </button>
                </div>
            </form>
        </div>

        <!-- Loading State -->
        <div id="loadingState" class="hidden text-center py-12">
            <div class="loading-spinner mx-auto mb-4"></div>
            <p class="text-gray-600">AI is analyzing your preferences...</p>
        </div>

        <!-- Results Section -->
        <div id="resultsSection" class="hidden">
            <!-- Results will be dynamically inserted here -->
        </div>

        <!-- Error Section -->
        <div id="errorSection" class="hidden bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <i class="fas fa-exclamation-triangle text-red-500 text-3xl mb-3"></i>
            <h3 class="text-lg font-semibold text-red-800 mb-2">Something went wrong</h3>
            <p id="errorMessage" class="text-red-600"></p>
        </div>
    </main>

    <!-- Footer -->
    <footer class="bg-gray-800 text-white py-6 mt-12">
        <div class="container mx-auto px-4 text-center">
            <p class="text-sm">
                <i class="fas fa-robot mr-1"></i>
                Powered by AI Technology | LLM Provider: {{ llm_provider|title }}
            </p>
        </div>
    </footer>

    <script>
        // Form handling
        document.getElementById('searchForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = {
                location: document.getElementById('location').value,
                budget: document.getElementById('budget').value,
                cuisine: document.getElementById('cuisine').value,
                min_rating: parseFloat(document.getElementById('rating').value)
            };
            
            // Show loading
            showLoading();
            
            try {
                // Call API
                const response = await fetch('/recommend', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showResults(data.data);
                } else {
                    showError(data.error || 'Failed to get recommendations');
                }
            } catch (error) {
                showError('Network error. Please try again.');
            } finally {
                hideLoading();
            }
        });
        
        function showLoading() {
            document.getElementById('loadingState').classList.remove('hidden');
            document.getElementById('resultsSection').classList.add('hidden');
            document.getElementById('errorSection').classList.add('hidden');
        }
        
        function hideLoading() {
            document.getElementById('loadingState').classList.add('hidden');
        }
        
        function showResults(data) {
            const resultsSection = document.getElementById('resultsSection');
            
            let html = `
                <div class="bg-white rounded-xl shadow-lg p-6 mb-8 fade-in">
                    <h2 class="text-xl font-semibold mb-4 text-gray-800">
                        <i class="fas fa-star mr-2"></i>Restaurant Recommendations
                    </h2>
                    <p class="text-gray-600 mb-6">${data.summary}</p>
            `;
            
            if (data.rankings && data.rankings.length > 0) {
                html += '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">';
                
                data.rankings.forEach((restaurant, index) => {
                    const scoreColor = getScoreColor(restaurant.relevance_score);
                    const scoreCategory = getScoreCategory(restaurant.relevance_score);
                    
                    html += `
                        <div class="bg-white border border-gray-200 rounded-lg p-6 card-hover fade-in" style="animation-delay: ${index * 0.1}s">
                            <div class="flex items-center justify-between mb-4">
                                <span class="text-2xl font-bold text-purple-600">#${restaurant.rank}</span>
                                <div class="text-right">
                                    <div class="text-sm font-semibold" style="color: ${scoreColor}">
                                        ${restaurant.relevance_score}/100
                                    </div>
                                    <div class="text-xs text-gray-500">${scoreCategory}</div>
                                </div>
                            </div>
                            
                            <h3 class="text-lg font-semibold text-gray-800 mb-3">
                                ${restaurant.restaurant_name}
                            </h3>
                            
                            <div class="mb-4">
                                <p class="text-gray-600 text-sm leading-relaxed">
                                    ${restaurant.explanation}
                                </p>
                            </div>
                            
                            ${restaurant.highlights && restaurant.highlights.length > 0 ? `
                                <div class="border-t pt-3">
                                    <div class="text-xs font-semibold text-gray-500 mb-2">Highlights</div>
                                    <div class="flex flex-wrap gap-1">
                                        ${restaurant.highlights.map(highlight => 
                                            `<span class="bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full">${highlight}</span>`
                                        ).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    `;
                });
                
                html += '</div>';
            } else {
                html += `
                    <div class="text-center py-8">
                        <i class="fas fa-search text-gray-400 text-4xl mb-4"></i>
                        <p class="text-gray-600">No restaurants found matching your criteria.</p>
                    </div>
                `;
            }
            
            // Add suggestions if available
            if (data.suggestions && data.suggestions.length > 0) {
                html += `
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
                        <h4 class="font-semibold text-blue-800 mb-2">
                            <i class="fas fa-lightbulb mr-1"></i>Suggestions
                        </h4>
                        <ul class="text-blue-700 space-y-1">
                            ${data.suggestions.map(suggestion => 
                                `<li><i class="fas fa-chevron-right mr-1 text-xs"></i>${suggestion}</li>`
                            ).join('')}
                        </ul>
                    </div>
                `;
            }
            
            html += '</div>';
            
            resultsSection.innerHTML = html;
            resultsSection.classList.remove('hidden');
        }
        
        function showError(message) {
            document.getElementById('errorMessage').textContent = message;
            document.getElementById('errorSection').classList.remove('hidden');
        }
        
        function getScoreColor(score) {
            if (score >= 90) return '#10b981';  // green
            if (score >= 75) return '#3b82f6';  // blue
            if (score >= 60) return '#f59e0b';  // amber
            return '#6b7280';  // gray
        }
        
        function getScoreCategory(score) {
            if (score >= 90) return 'Excellent Match';
            if (score >= 75) return 'Great Match';
            if (score >= 60) return 'Good Match';
            return 'Fair Match';
        }
    </script>
</body>
</html>
    """
