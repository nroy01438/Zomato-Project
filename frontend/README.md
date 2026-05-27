# Phase 7 - Production Frontend Architecture

A modern, responsive Next.js frontend for the AI-Powered Restaurant Recommendation System.

## Overview

Phase 7 provides a production-ready web application with:
- **Next.js 14+** with App Router
- **React 18** with Server Components
- **Tailwind CSS** for styling
- **TypeScript** for type safety
- **Zustand** for state management
- **TanStack Query** for data fetching
- **Framer Motion** for animations

## Features

### 🎨 **Modern UI/UX**
- Responsive design (mobile-first)
- Dark/Light mode support
- Smooth animations and transitions
- Accessible components (WCAG 2.1 AA)

### 🔍 **Search & Discovery**
- Smart search with autocomplete
- Advanced filters (location, budget, cuisine, rating)
- AI-powered recommendations display
- Real-time results loading

### 👤 **User Experience**
- User authentication (JWT)
- Saved restaurants
- Search history
- User preferences
- Profile management

### ⚡ **Performance**
- Server-side rendering (SSR)
- Static site generation (SSG)
- Image optimization
- Code splitting
- Lazy loading

## Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

Create a `.env.local` file:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:5000

# WebSocket URL (for real-time updates)
NEXT_PUBLIC_WS_URL=ws://localhost:5000

# Optional: Analytics
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

## Project Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── page.tsx             # Landing page
│   ├── search/
│   │   └── page.tsx         # Search results
│   ├── restaurant/
│   │   └── [id]/
│   │       └── page.tsx     # Restaurant detail
│   ├── profile/
│   │   └── page.tsx         # User profile
│   ├── auth/
│   │   ├── login/
│   │   │   └── page.tsx     # Login page
│   │   └── register/
│   │       └── page.tsx     # Register page
│   ├── layout.tsx           # Root layout
│   └── globals.css          # Global styles
├── components/               # React components
│   ├── ui/                  # shadcn/ui components
│   ├── navbar.tsx           # Navigation bar
│   ├── hero-section.tsx     # Landing hero
│   ├── search-form.tsx      # Search form
│   ├── restaurant-card.tsx  # Restaurant card
│   └── loading-skeleton.tsx # Loading states
├── hooks/                    # Custom React hooks
│   ├── use-auth.ts
│   ├── use-search.ts
│   └── use-restaurants.ts
├── lib/                      # Utilities
│   ├── api.ts               # API client
│   ├── store.ts             # Zustand stores
│   └── utils.ts             # Helper functions
├── types/                    # TypeScript types
│   └── index.ts
├── public/                   # Static assets
├── next.config.js           # Next.js config
├── tailwind.config.ts       # Tailwind config
├── tsconfig.json            # TypeScript config
└── package.json             # Dependencies
```

## Key Components

### Search Form
- Location input with autocomplete
- Budget selector (Low/Medium/High)
- Cuisine multi-select
- Rating slider
- Smart filters toggle

### Restaurant Cards
- High-quality images
- Cuisine tags
- Star ratings
- Price indicators
- AI recommendation badges
- Quick actions (save, share)

### Results Display
- Grid/List view toggle
- Sort options
- Pagination/Infinite scroll
- Filter sidebar
- Loading skeletons

### Authentication
- JWT-based auth
- Login/Register forms
- Social login (Google, Apple)
- Password reset
- Protected routes

## API Integration

The frontend integrates with Phase 6 backend:

```typescript
// Example: Search restaurants
const searchRestaurants = async (params: SearchParams) => {
  const response = await api.searchRestaurants({
    location: "New York",
    budget: "Medium",
    cuisine: "Italian",
    min_rating: 4.0,
  });
  return response.restaurants;
};

// Example: User authentication
const login = async (credentials: LoginCredentials) => {
  const token = await api.login(credentials);
  localStorage.setItem("access_token", token.access_token);
};
```

## State Management

Using Zustand for global state:

```typescript
// Auth store
const { user, isAuthenticated, logout } = useAuthStore();

// Search store
const { params, results, setParams } = useSearchStore();

// Saved restaurants store
const { saved, addRestaurant, removeRestaurant } = useSavedRestaurantsStore();
```

## Styling

### Tailwind Configuration
- Custom color palette (primary: orange, secondary: teal)
- Custom font stack (Inter + Poppins)
- Responsive breakpoints
- Animation utilities

### Dark Mode
```typescript
// Toggle dark mode
const { theme, setTheme } = useTheme();
setTheme(theme === "dark" ? "light" : "dark");
```

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Start production server
npm start
```

## Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Integration with Phase 6

The frontend connects to Phase 6 backend services:
- **API Gateway**: Routes all requests
- **Authentication**: JWT token management
- **Rate Limiting**: Respects API limits
- **Caching**: Benefits from backend caching
- **Health Monitoring**: Shows system status

## Next Steps

1. Run `npm install` to install dependencies
2. Set up environment variables in `.env.local`
3. Start the Phase 6 backend (port 5000)
4. Run `npm run dev` to start the frontend
5. Open http://localhost:3000

## Deliverables

✅ **Next.js 14+ App** with App Router
✅ **TypeScript** for type safety
✅ **Tailwind CSS** with custom design system
✅ **Authentication** with JWT
✅ **State Management** with Zustand
✅ **Data Fetching** with TanStack Query
✅ **Animations** with Framer Motion
✅ **Dark Mode** support
✅ **Responsive Design** (mobile-first)
✅ **Accessibility** (WCAG 2.1 AA)

## Phase 7 Integration

This frontend works seamlessly with:
- **Phase 6 Backend**: API, auth, caching, rate limiting
- **Phase 3 LLM**: AI-powered recommendations
- **Phase 5 Monitoring**: Error tracking, analytics

Ready for deployment to Vercel, AWS, or any Next.js-compatible hosting platform!
