"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { SearchForm } from "@/components/search-form";
import { RestaurantCard } from "@/components/restaurant-card";
import { LoadingSkeleton } from "@/components/loading-skeleton";
import { useSearchStore } from "@/lib/store";
import { api } from "@/lib/api";
import { toast } from "sonner";

export default function SearchPage() {
  const { params, results, setResults, setIsLoading, isLoading } = useSearchStore();
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (searchParams: typeof params) => {
    setIsLoading(true);
    setHasSearched(true);

    try {
      const response = await api.searchRestaurants(searchParams);
      setResults(response);
      
      if (response.rankings.length === 0) {
        toast.info("No restaurants found. Try adjusting your filters.");
      }
    } catch (error) {
      toast.error("Failed to search restaurants. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto"
      >
        <h1 className="font-display text-3xl font-bold mb-8 text-center">
          Find Your Perfect Restaurant
        </h1>

        {/* Search Form */}
        <div className="mb-12">
          <SearchForm onSearch={handleSearch} initialParams={params} />
        </div>

        {/* Results */}
        {isLoading ? (
          <LoadingSkeleton count={6} />
        ) : hasSearched && results ? (
          <div>
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-semibold">
                {results.total_results} restaurants found
              </h2>
              <p className="text-sm text-muted-foreground">
                Processing time: {results.processing_time_ms}ms
              </p>
            </div>

            {results.summary && (
              <div className="mb-6 rounded-xl border bg-card p-4">
                <p className="text-sm text-muted-foreground">{results.summary}</p>
              </div>
            )}

            {results.rankings.length > 0 ? (
              <div className="grid md:grid-cols-2 gap-6">
                {results.rankings.map((restaurant, index) => (
                  <motion.div
                    key={restaurant.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <RestaurantCard restaurant={restaurant} />
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <p className="text-muted-foreground">
                  No restaurants match your criteria. Try adjusting your filters.
                </p>
                {results.suggestions?.length > 0 && (
                  <ul className="mt-4 text-sm text-muted-foreground space-y-1">
                    {results.suggestions.map((s) => (
                      <li key={s}>- {s}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-16 text-muted-foreground">
            <p>Enter your preferences above to get AI-powered restaurant recommendations.</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
