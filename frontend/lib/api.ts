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
  LocationsResponse,
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
      timeout: 120000,
    });

    // Request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        if (typeof window !== "undefined") {
          const token = localStorage.getItem("access_token");
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
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
          const refreshToken =
            typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
          if (refreshToken) {
            try {
              const response = await this.refreshToken(refreshToken);
              if (typeof window !== "undefined") {
                localStorage.setItem("access_token", response.access_token);
              }
              
              // Retry original request
              const originalRequest = error.config;
              if (originalRequest) {
                originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
                return this.client.request(originalRequest);
              }
            } catch {
              // Refresh failed, logout
              if (typeof window !== "undefined") {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                window.location.href = "/auth/login";
              }
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

  // Locations (from dataset city column)
  async getLocations(): Promise<LocationsResponse> {
    const response = await this.client.get("/locations");
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
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    if (token) {
      await this.client.post("/auth/logout", { access_token: token });
    }
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
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
    const payload = response.data as any;

    const data = payload?.data ?? {};
    const meta = payload?.meta ?? {};
    const rankings = Array.isArray(data.rankings) ? data.rankings : [];

    const restaurants: Restaurant[] = rankings.map((r: any, idx: number) => {
      const name = String(r?.name ?? r?.restaurant_name ?? `Restaurant ${idx + 1}`);
      const locality = r?.locality ? String(r.locality) : "";
      const idBase = `${name}-${locality || "unknown"}`.toLowerCase();
      const id = idBase.replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

      const cuisinesRaw = r?.cuisines;
      const cuisines =
        Array.isArray(cuisinesRaw)
          ? cuisinesRaw.map(String)
          : typeof cuisinesRaw === "string"
            ? cuisinesRaw.split(",").map((s: string) => s.trim()).filter(Boolean)
            : [];

      return {
        id,
        name,
        cuisines,
        rating: typeof r?.rating === "number" ? r.rating : Number(r?.rating ?? 0),
        votes: typeof r?.votes === "number" ? r.votes : Number(r?.votes ?? 0),
        cost_for_two:
          typeof r?.cost_for_two === "number" ? r.cost_for_two : Number(r?.cost_for_two ?? 0),
        location: locality,
        explanation: r?.explanation ? String(r.explanation) : undefined,
        ai_recommended: true,
      };
    });

    return {
      summary: String(data.summary ?? ""),
      total_results: typeof data.total_results === "number" ? data.total_results : restaurants.length,
      rankings: restaurants,
      suggestions: Array.isArray(data.suggestions) ? data.suggestions.map(String) : [],
      processing_time_ms:
        typeof meta.processing_time_ms === "number" ? meta.processing_time_ms : 0,
    };
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
