import axios, { AxiosInstance, AxiosError } from "axios";
import {
  Restaurant,
  SearchParams,
  SearchResult,
  AuthToken,
  LoginCredentials,
  RegisterData,
  User,
  SavedRestaurant,
  SearchHistoryItem,
  HealthStatus,
  RateLimitInfo,
  ApiError,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

/**
 * API Client for Phase 6 Backend
 */
class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 30000,
    });

    // Request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem("access_token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired, try to refresh
          const refreshToken = localStorage.getItem("refresh_token");
          if (refreshToken) {
            try {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem("access_token", response.access_token);
              
              // Retry original request
              const originalRequest = error.config;
              if (originalRequest) {
                originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
                return this.client.request(originalRequest);
              }
            } catch {
              // Refresh failed, logout
              localStorage.removeItem("access_token");
              localStorage.removeItem("refresh_token");
              window.location.href = "/auth/login";
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async getHealth(): Promise<HealthStatus> {
    const response = await this.client.get("/health");
    return response.data;
  }

  // Authentication
  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const response = await this.client.post("/auth/login", {
      ...credentials,
      ip_address: "127.0.0.1", // Will be set by server
    });
    return response.data;
  }

  async register(data: RegisterData): Promise<AuthToken> {
    const response = await this.client.post("/auth/register", data);
    return response.data;
  }

  async logout(): Promise<void> {
    const token = localStorage.getItem("access_token");
    if (token) {
      await this.client.post("/auth/logout", { access_token: token });
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  async refreshToken(refreshToken: string): Promise<AuthToken> {
    const response = await this.client.post("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get("/user/profile");
    return response.data;
  }

  async updateUserProfile(userId: string, updates: Partial<User>): Promise<User> {
    const response = await this.client.put(`/user/${userId}`, updates);
    return response.data;
  }

  // Restaurant Search
  async searchRestaurants(params: SearchParams): Promise<SearchResult> {
    const response = await this.client.post("/recommend", params);
    return response.data;
  }

  async searchRestaurantsBatch(params: SearchParams[]): Promise<SearchResult[]> {
    const response = await this.client.post("/recommend/batch", params);
    return response.data;
  }

  async getRestaurantById(id: string): Promise<Restaurant> {
    const response = await this.client.get(`/restaurants/${id}`);
    return response.data;
  }

  async getRestaurantsByLocation(
    location: string,
    limit: number = 20
  ): Promise<Restaurant[]> {
    const response = await this.client.get("/restaurants", {
      params: { location, limit },
    });
    return response.data;
  }

  // Saved Restaurants
  async getSavedRestaurants(): Promise<SavedRestaurant[]> {
    const response = await this.client.get("/user/saved-restaurants");
    return response.data;
  }

  async saveRestaurant(restaurantId: string, notes?: string): Promise<SavedRestaurant> {
    const response = await this.client.post("/user/saved-restaurants", {
      restaurant_id: restaurantId,
      notes,
    });
    return response.data;
  }

  async removeSavedRestaurant(savedId: string): Promise<void> {
    await this.client.delete(`/user/saved-restaurants/${savedId}`);
  }

  // Search History
  async getSearchHistory(): Promise<SearchHistoryItem[]> {
    const response = await this.client.get("/user/search-history");
    return response.data;
  }

  async clearSearchHistory(): Promise<void> {
    await this.client.delete("/user/search-history");
  }

  // Rate Limiting
  async getRateLimitStatus(): Promise<RateLimitInfo> {
    const response = await this.client.get("/rate-limit/status");
    return response.data;
  }

  // Cache Management (Admin only)
  async clearCache(pattern?: string): Promise<{ cleared: number }> {
    const response = await this.client.post("/cache/clear", { pattern });
    return response.data;
  }

  // Error handling helper
  handleError(error: AxiosError): ApiError {
    if (error.response) {
      return {
        status: error.response.status,
        message: (error.response.data as any)?.message || error.message,
        details: (error.response.data as any)?.details,
      };
    }
    return {
      status: 500,
      message: error.message || "An unexpected error occurred",
    };
  }
}

export const api = new ApiClient();
export default api;
