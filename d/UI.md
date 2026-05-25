# Google Stitch Prompt for Frontend UI Generation

## Next.js Restaurant Recommendation App - UI Design Prompt

Use the following prompt with **Google Stitch** to generate frontend UI images for the Next.js application:

```
Create a modern, visually stunning restaurant recommendation web application UI using Next.js, React, and Tailwind CSS. The design should follow a premium food-tech aesthetic with warm colors (oranges, warm grays, subtle gradients) reminiscent of fine dining apps.

### Main Pages/Screens Required:

1. **Landing Page**
   - Hero section with search bar prominently displayed
   - "Discover Your Perfect Restaurant" headline with elegant typography
   - Background with subtle food/restaurant imagery or gradient
   - Featured restaurant categories (Italian, Japanese, Indian, etc.) as clickable cards
   - Statistics section showing "10,000+ Restaurants", "50+ Cities", "AI-Powered"
   - Call-to-action buttons: "Get Started", "How It Works"

2. **Search/Input Page**
   - Clean form with floating labels or modern input styling
   - Fields: Location (with location icon/autocomplete), Budget (dropdown: Low/Medium/High), Cuisine Type (multi-select chips), Minimum Rating (slider 1-5 stars)
   - "Smart Filters" toggle for AI-enhanced recommendations
   - Large prominent "Find Restaurants" button with gradient
   - Recent searches section below the form
   - Dark mode toggle in header

3. **Results/Loading Page**
   - Skeleton loading cards (3-5 restaurant cards with shimmer effect)
   - "AI is finding the best restaurants for you..." message with animated dots
   - Progress indicator showing retrieval → filtering → ranking steps
   - Cancel search option

4. **Results Display Page**
   - Grid layout (2-3 columns desktop, 1 column mobile)
   - Restaurant cards with:
     * High-quality food image (16:9 ratio) with overlay gradient
     * Restaurant name (bold, large text)
     * Cuisine tags (colored pills: Italian, Japanese, etc.)
     * Star rating with vote count
     * Price range indicator (₹, ₹₹, ₹₹₹)
     * AI-generated explanation badge ("AI Pick" with sparkle icon)
     * "View Details" and "Get Directions" action buttons
   - Sort dropdown: "AI Recommended", "Highest Rated", "Price: Low to High", "Distance"
   - Filter sidebar (collapsible on mobile): Cuisine types, Price range, Rating, Features (delivery, outdoor seating, etc.)
   - Pagination or infinite scroll indicator

5. **Restaurant Detail Page/Modal**
   - Large hero image carousel (3-5 images)
   - Restaurant name, rating, price range at top
   - Quick info row: Address, Phone, Hours, Website link
   - "About" section with AI-generated summary
   - "Why We Recommend This" section with bullet points from AI
   - Menu highlights section
   - Reviews section with sentiment analysis badge
   - Map integration placeholder
   - "Book Table" or "Order Online" CTA buttons
   - Similar restaurants section at bottom

6. **User Profile Page**
   - User avatar, name, member since date
   - Tabs: Saved Restaurants, Search History, Preferences, Settings
   - Saved restaurants as horizontal scroll cards or grid
   - Preference settings: Favorite cuisines, dietary restrictions, notification settings
   - Dark mode toggle, language selector

7. **Authentication Pages**
   - Clean login form: Email, Password, "Remember me" checkbox
   - Social login buttons: Google, Apple (OAuth)
   - "Sign Up" link with benefits: "Save favorites", "Get personalized recommendations"
   - Password reset flow

### Design System Specifications:

**Colors:**
- Primary: Warm orange (#FF6B35) or coral
- Secondary: Deep teal or emerald (#10B981)
- Background: Off-white (#FAFAFA) or dark mode (#1A1A1A)
- Surface: White (#FFFFFF) or dark mode card (#2D2D2D)
- Text: Dark charcoal (#1F2937) or light gray (#F3F4F6 in dark mode)
- Accent: Gold/amber for ratings (#F59E0B)

**Typography:**
- Headlines: Inter or Poppins, bold weights (600-700)
- Body: Inter or Roboto, regular (400-500)
- Font sizes: Hero (48-64px), H1 (32-40px), H2 (24-28px), Body (16-18px)

**Components:**
- Cards: Rounded corners (12-16px), subtle shadow (shadow-lg), hover lift effect
- Buttons: Rounded-full or rounded-xl, gradient backgrounds, hover scale
- Inputs: Rounded-lg, border-2 focus states, floating labels
- Badges: Pill-shaped, colored backgrounds for cuisine types
- Icons: Lucide React icons (Star, MapPin, Utensils, DollarSign, Clock)

**Animations:**
- Page transitions: Fade + slide (300ms ease-out)
- Card hover: Scale 1.02, shadow increase
- Button hover: Background lightens, subtle scale
- Loading: Skeleton shimmer, dots bounce
- Results: Staggered fade-in for cards (50ms delay each)

**Responsive Breakpoints:**
- Mobile: < 640px (single column, stacked layout)
- Tablet: 640px - 1024px (2 columns)
- Desktop: > 1024px (3 columns, sidebar visible)

### Technical Notes for Developers:
- Use Next.js 14+ with App Router
- Tailwind CSS for styling
- Framer Motion for animations
- React Query or SWR for data fetching
- Zustand or Redux for state management
- Shadcn/ui or Radix UI for accessible components
- Lucide React for icons
- Implement dark mode with next-themes

### Key Features to Highlight:
- AI-powered recommendations (show "AI-generated" badges)
- Real-time search with autocomplete
- Interactive maps integration
- Save/share restaurants
- User reviews with sentiment
- Mobile-first responsive design
- Accessibility (WCAG 2.1 AA compliant)
- Fast page loads (Next.js SSR/SSG)
- SEO optimized for restaurant searches
```

## Usage Instructions

1. **Copy the prompt above** and paste it into Google Stitch
2. **Iterate on specific pages** by asking for variations:
   - "Show me the dark mode version"
   - "Create a mobile layout for [page]"
   - "Generate a loading state animation"
   - "Design an empty state screen"
3. **Export designs** and use them as reference for Next.js implementation
4. **Extract color values, spacing, and typography** directly from generated images
5. **Use as mockups** for stakeholder presentations before development

## Phase 7 Integration

Once UI designs are generated, implement in `phase7/` directory with:
- Next.js 14+ App Router structure
- Tailwind CSS configuration matching the design system
- Component library (shadcn/ui recommended)
- API integration with Phase 6 backend endpoints
- Authentication integration with Phase 6 auth system

### Suggested Folder Structure:

```
phase7/
├── app/
│   ├── page.tsx              # Landing page
│   ├── search/
│   │   └── page.tsx          # Search form
│   ├── results/
│   │   └── page.tsx          # Results grid
│   ├── restaurant/
│   │   └── [id]/
│   │       └── page.tsx      # Detail page
│   ├── profile/
│   │   └── page.tsx          # User profile
│   ├── auth/
│   │   ├── login/
│   │   │   └── page.tsx      # Login page
│   │   └── signup/
│   │       └── page.tsx      # Signup page
│   └── layout.tsx            # Root layout
├── components/
│   ├── ui/                   # shadcn/ui components
│   ├── restaurant-card.tsx   # Restaurant card component
│   ├── search-form.tsx       # Search form component
│   └── loading-skeleton.tsx  # Loading states
├── lib/
│   ├── api.ts                # API client
│   ├── auth.ts               # Auth utilities
│   └── utils.ts              # Helper functions
├── hooks/
│   ├── use-restaurants.ts    # Data fetching hook
│   └── use-auth.ts           # Auth state hook
├── public/
│   └── images/               # Static images
├── styles/
│   └── globals.css           # Global styles + Tailwind
├── tailwind.config.ts        # Tailwind configuration
├── next.config.js            # Next.js configuration
└── package.json
```

## Additional Resources

### Color Palette Reference

| Token | Light Mode | Dark Mode | Usage |
|-------|-----------|-----------|-------|
| `--primary` | `#FF6B35` | `#FF8F5A` | Buttons, links, accents |
| `--secondary` | `#10B981` | `#34D399` | Success states, badges |
| `--background` | `#FAFAFA` | `#1A1A1A` | Page background |
| `--surface` | `#FFFFFF` | `#2D2D2D` | Cards, modals |
| `--text-primary` | `#1F2937` | `#F3F4F6` | Headlines, body |
| `--text-secondary` | `#6B7280` | `#9CA3AF` | Captions, meta |
| `--accent` | `#F59E0B` | `#FBBF24` | Ratings, stars |

### Typography Scale

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Hero | 48-64px | 700 | 1.1 | Landing headlines |
| H1 | 32-40px | 700 | 1.2 | Page titles |
| H2 | 24-28px | 600 | 1.3 | Section headers |
| H3 | 20-24px | 600 | 1.4 | Card titles |
| Body | 16-18px | 400-500 | 1.5 | Paragraphs |
| Caption | 14px | 400 | 1.4 | Labels, meta |
| Small | 12px | 400 | 1.4 | Badges, tags |

---

*Copy this prompt into Google Stitch to generate your UI designs for the Restaurant Recommendation App.*
