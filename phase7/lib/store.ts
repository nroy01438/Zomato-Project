import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  User,
  Restaurant,
  SearchParams,
  SearchResult,
  Notification,
} from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setIsAuthenticated: (value: boolean) => void;
  setIsLoading: (value: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setIsAuthenticated: (value) => set({ isAuthenticated: value }),
      setIsLoading: (value) => set({ isLoading: value }),
      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

interface SearchState {
  params: SearchParams;
  results: SearchResult | null;
  isLoading: boolean;
  error: string | null;
  recentSearches: SearchParams[];
  setParams: (params: Partial<SearchParams>) => void;
  setResults: (results: SearchResult | null) => void;
  setIsLoading: (value: boolean) => void;
  setError: (error: string | null) => void;
  addRecentSearch: (params: SearchParams) => void;
  clearResults: () => void;
}

export const useSearchStore = create<SearchState>()(
  persist(
    (set) => ({
      params: {
        location: "",
        budget: "Medium",
        cuisine: "",
        min_rating: 4.0,
      },
      results: null,
      isLoading: false,
      error: null,
      recentSearches: [],
      setParams: (params) =>
        set((state) => ({ params: { ...state.params, ...params } })),
      setResults: (results) => set({ results }),
      setIsLoading: (value) => set({ isLoading: value }),
      setError: (error) => set({ error }),
      addRecentSearch: (params) =>
        set((state) => ({
          recentSearches: [params, ...state.recentSearches.slice(0, 9)],
        })),
      clearResults: () => set({ results: null, error: null }),
    }),
    {
      name: "search-storage",
      partialize: (state) => ({ recentSearches: state.recentSearches }),
    }
  )
);

interface SavedRestaurantsState {
  saved: Restaurant[];
  isLoading: boolean;
  addRestaurant: (restaurant: Restaurant) => void;
  removeRestaurant: (id: string) => void;
  setSaved: (restaurants: Restaurant[]) => void;
  setIsLoading: (value: boolean) => void;
  isSaved: (id: string) => boolean;
}

export const useSavedRestaurantsStore = create<SavedRestaurantsState>()(
  persist(
    (set, get) => ({
      saved: [],
      isLoading: false,
      addRestaurant: (restaurant) =>
        set((state) => ({
          saved: state.saved.some((r) => r.id === restaurant.id)
            ? state.saved
            : [...state.saved, restaurant],
        })),
      removeRestaurant: (id) =>
        set((state) => ({
          saved: state.saved.filter((r) => r.id !== id),
        })),
      setSaved: (restaurants) => set({ saved: restaurants }),
      setIsLoading: (value) => set({ isLoading: value }),
      isSaved: (id) => get().saved.some((r) => r.id === id),
    }),
    {
      name: "saved-restaurants-storage",
      partialize: (state) => ({ saved: state.saved }),
    }
  )
);

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, "id" | "read" | "created_at">) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationState>()(
  persist(
    (set, get) => ({
      notifications: [],
      unreadCount: 0,
      addNotification: (notification) =>
        set((state) => {
          const newNotification: Notification = {
            ...notification,
            id: Math.random().toString(36).substring(2, 9),
            read: false,
            created_at: new Date().toISOString(),
          };
          return {
            notifications: [newNotification, ...state.notifications.slice(0, 49)],
            unreadCount: state.unreadCount + 1,
          };
        }),
      markAsRead: (id) =>
        set((state) => {
          const notification = state.notifications.find((n) => n.id === id);
          if (notification && !notification.read) {
            return {
              notifications: state.notifications.map((n) =>
                n.id === id ? { ...n, read: true } : n
              ),
              unreadCount: Math.max(0, state.unreadCount - 1),
            };
          }
          return state;
        }),
      markAllAsRead: () =>
        set((state) => ({
          notifications: state.notifications.map((n) => ({ ...n, read: true })),
          unreadCount: 0,
        })),
      removeNotification: (id) =>
        set((state) => {
          const notification = state.notifications.find((n) => n.id === id);
          return {
            notifications: state.notifications.filter((n) => n.id !== id),
            unreadCount: notification && !notification.read
              ? Math.max(0, state.unreadCount - 1)
              : state.unreadCount,
          };
        }),
      clearAll: () => set({ notifications: [], unreadCount: 0 }),
    }),
    {
      name: "notification-storage",
      partialize: (state) => ({ notifications: state.notifications, unreadCount: state.unreadCount }),
    }
  )
);

interface UIState {
  sidebarOpen: boolean;
  searchOpen: boolean;
  activeModal: string | null;
  setSidebarOpen: (value: boolean) => void;
  setSearchOpen: (value: boolean) => void;
  setActiveModal: (modal: string | null) => void;
  closeAllModals: () => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: false,
  searchOpen: false,
  activeModal: null,
  setSidebarOpen: (value) => set({ sidebarOpen: value }),
  setSearchOpen: (value) => set({ searchOpen: value }),
  setActiveModal: (modal) => set({ activeModal: modal }),
  closeAllModals: () => set({ activeModal: null, searchOpen: false }),
}));
