/**
 * Type definitions for Restaurant Recommendation Frontend
 */

export interface Restaurant {
  id: string;
  name: string;
  cuisines: string[];
  rating: number;
  votes: number;
  cost_for_two: number;
  location: string;
  address?: string;
  phone?: string;
  website?: string;
  hours?: string;
  image_url?: string;
  menu_highlights?: string[];
  explanation?: string;
  ai_recommended?: boolean;
  features?: string[];
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: "guest" | "user" | "premium" | "admin" | "super_admin";
  avatar_url?: string;
  preferences: UserPreferences;
  created_at: string;
  last_login?: string;
}

export interface UserPreferences {
  favorite_cuisines: string[];
  dietary_restrictions: string[];
  max_budget?: number;
  min_rating?: number;
  notifications_enabled: boolean;
  dark_mode: boolean;
  language: string;
}

export interface SearchParams {
  location: string;
  budget: number;
  cuisine: string;
  min_rating: number;
  additional_preferences?: string;
}

export interface SearchResult {
  summary: string;
  rankings: Restaurant[];
  total_results: number;
  suggestions: string[];
  processing_time_ms: number;
}

export interface LocationsResponse {
  locations: string[];
}

export interface AuthToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface ApiError {
  status: number;
  message: string;
  details?: Record<string, string[]>;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  read: boolean;
  created_at: string;
}

export interface SavedRestaurant {
  id: string;
  restaurant: Restaurant;
  saved_at: string;
  notes?: string;
  tags?: string[];
}

export interface Review {
  id: string;
  user_id: string;
  restaurant_id: string;
  rating: number;
  text: string;
  sentiment: "positive" | "neutral" | "negative";
  created_at: string;
  user?: User;
}

export interface SearchHistoryItem {
  id: string;
  params: SearchParams;
  results_count: number;
  timestamp: string;
}

export interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

export interface CuisineCategory {
  id: string;
  name: string;
  icon: string;
  image_url: string;
  restaurant_count: number;
}

export interface HealthStatus {
  status: "healthy" | "degraded" | "unhealthy" | "critical";
  message: string;
  components: Record<string, {
    status: string;
    message?: string;
    stats?: Record<string, any>;
  }>;
}

export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset_time: string;
  retry_after?: number;
}
