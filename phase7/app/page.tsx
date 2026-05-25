import { HeroSection } from "@/components/hero-section";
import { FeaturedCategories } from "@/components/featured-categories";
import { HowItWorks } from "@/components/how-it-works";
import { StatsSection } from "@/components/stats-section";

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero Section with Search */}
      <HeroSection />

      {/* Featured Cuisine Categories */}
      <FeaturedCategories />

      {/* How It Works */}
      <HowItWorks />

      {/* Stats Section */}
      <StatsSection />
    </div>
  );
}
