"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { motion } from "framer-motion";
import { Star } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { useSearchStore } from "@/lib/store";
import { SearchParams } from "@/types";
import { RestaurantCard } from "@/components/restaurant-card";
import { LoadingSkeleton } from "@/components/loading-skeleton";

const ZOMATO_RED = "#E23744";

const quickTags = ["Italian", "Spicy", "Dessert", "North Indian", "Biryani", "Chinese"];

const ratingOptions = [
  { label: "3.5+", value: 3.5 },
  { label: "4.0+", value: 4.0 },
  { label: "4.5+", value: 4.5 },
] as const;

function FieldLabel({ children, required }: { children: React.ReactNode; required?: boolean }) {
  return (
    <label className="mb-1.5 block text-sm font-medium text-neutral-800">
      {children}
      {required && <span className="text-[#E23744]"> *</span>}
    </label>
  );
}

function inputClass(error?: boolean) {
  return cn(
    "w-full rounded-lg border bg-white px-3 py-2.5 text-sm text-neutral-900 placeholder:text-neutral-400 outline-none transition-colors focus:border-[#E23744] focus:ring-2 focus:ring-[#E23744]/20",
    error ? "border-red-400" : "border-neutral-200"
  );
}

export function ZomatoRecommendationScreen() {
  const { params: storedParams, results, setResults, setIsLoading, isLoading } = useSearchStore();
  const [params, setParams] = useState<SearchParams>(storedParams);
  const [locations, setLocations] = useState<string[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof SearchParams, string>>>({});
  const [apiStatus, setApiStatus] = useState<string>("Checking API…");

  useEffect(() => {
    api
      .getLocations()
      .then((res) => setLocations(res.locations || []))
      .catch(() => setLocations([]));

    api
      .getHealth()
      .then((h) => {
        const ok = h.status === "healthy";
        setApiStatus(ok ? "API: ok — ready for recommendations" : `API: ${h.status}`);
      })
      .catch(() => setApiStatus("API: unreachable — check NEXT_PUBLIC_API_URL"));
  }, []);

  const validate = (): boolean => {
    const next: Partial<Record<keyof SearchParams, string>> = {};
    if (!params.location.trim()) next.location = "Location is required";
    if (!params.cuisine.trim()) next.cuisine = "Cuisine is required";
    if (!params.budget || params.budget <= 0) next.budget = "Budget is required (max ₹ for two)";
    if (!params.min_rating || params.min_rating < 1) next.min_rating = "Rating is required";
    if (!params.additional_preferences?.trim()) {
      next.additional_preferences = "Additional preferences are required";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleQuickTag = (tag: string) => {
    setParams((p) => {
      const parts = p.cuisine
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      if (parts.includes(tag)) return p;
      return { ...p, cuisine: [...parts, tag].join(", ") };
    });
    setErrors((e) => ({ ...e, cuisine: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) {
      toast.error("Please fill all required fields.");
      return;
    }

    setIsLoading(true);
    setHasSearched(true);

    try {
      const payload: SearchParams = {
        location: params.location.trim(),
        cuisine: params.cuisine.trim(),
        min_rating: params.min_rating,
        budget: Number(params.budget),
        additional_preferences: params.additional_preferences?.trim(),
      };
      const response = await api.searchRestaurants(payload);
      setResults(response);
      if (response.rankings.length === 0) {
        toast.info("No restaurants found. Try adjusting your filters.");
      }
    } catch {
      toast.error("Failed to get recommendations. Is the backend running?");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-dvh flex flex-col">
      {/* Background from reference image */}
      <div className="pointer-events-none absolute inset-0 z-0">
        <Image
          src="/zomato-ui-reference.png"
          alt=""
          fill
          className="object-cover"
          priority
          aria-hidden
        />
        <div className="absolute inset-0 bg-black/45 backdrop-blur-[2px]" />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center gap-2 border-b border-white/20 bg-white/90 px-4 py-3 shadow-sm backdrop-blur-md">
        <span className="text-2xl font-bold tracking-tight" style={{ color: ZOMATO_RED }}>
          zomato
        </span>
        <span className="text-sm font-medium text-neutral-600">Zomato AI Recommendation</span>
      </header>

      {/* Main */}
      <main className="relative z-10 flex flex-1 flex-col items-center px-4 py-8 pb-4">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-2xl rounded-2xl bg-white/95 p-6 shadow-2xl ring-1 ring-black/5 backdrop-blur-sm sm:p-8"
        >
          <h1 className="mb-4 text-center text-xl font-bold text-neutral-900 sm:text-2xl">
            Find Your Perfect Meal with Zomato AI
          </h1>

          {/* Quick tags */}
          <div className="mb-5 flex flex-wrap justify-center gap-2">
            {quickTags.map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => handleQuickTag(tag)}
                className="rounded-full border border-neutral-200 bg-neutral-50 px-3 py-1 text-xs font-medium text-neutral-700 transition-colors hover:border-[#E23744] hover:text-[#E23744]"
              >
                {tag}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              {/* Location */}
              <div>
                <FieldLabel required>Location</FieldLabel>
                {locations.length > 0 ? (
                  <select
                    required
                    value={params.location}
                    onChange={(e) => {
                      setParams({ ...params, location: e.target.value });
                      setErrors((er) => ({ ...er, location: undefined }));
                    }}
                    className={inputClass(!!errors.location)}
                  >
                    <option value="" disabled>
                      Select area (e.g. Basavanagudi)
                    </option>
                    {locations.map((loc) => (
                      <option key={loc} value={loc}>
                        {loc}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    required
                    type="text"
                    placeholder="Basavanagudi"
                    value={params.location}
                    onChange={(e) => {
                      setParams({ ...params, location: e.target.value });
                      setErrors((er) => ({ ...er, location: undefined }));
                    }}
                    className={inputClass(!!errors.location)}
                  />
                )}
                {errors.location && (
                  <p className="mt-1 text-xs text-red-600">{errors.location}</p>
                )}
              </div>

              {/* Cuisine */}
              <div>
                <FieldLabel required>Cuisine</FieldLabel>
                <input
                  required
                  type="text"
                  placeholder="e.g. North Indian, Biryani"
                  value={params.cuisine}
                  onChange={(e) => {
                    setParams({ ...params, cuisine: e.target.value });
                    setErrors((er) => ({ ...er, cuisine: undefined }));
                  }}
                  className={inputClass(!!errors.cuisine)}
                />
                {errors.cuisine && (
                  <p className="mt-1 text-xs text-red-600">{errors.cuisine}</p>
                )}
              </div>

              {/* Budget */}
              <div>
                <FieldLabel required>Budget</FieldLabel>
                <input
                  required
                  type="number"
                  min={100}
                  step={100}
                  placeholder="e.g. 1000 (max ₹ for two)"
                  value={params.budget || ""}
                  onChange={(e) => {
                    setParams({ ...params, budget: Number(e.target.value) });
                    setErrors((er) => ({ ...er, budget: undefined }));
                  }}
                  className={inputClass(!!errors.budget)}
                />
                {errors.budget && (
                  <p className="mt-1 text-xs text-red-600">{errors.budget}</p>
                )}
              </div>

              {/* Ratings */}
              <div>
                <FieldLabel required>Minimum rating</FieldLabel>
                <div className="flex gap-2">
                  {ratingOptions.map((opt) => {
                    const active = params.min_rating === opt.value;
                    return (
                      <button
                        key={opt.label}
                        type="button"
                        onClick={() => {
                          setParams({ ...params, min_rating: opt.value });
                          setErrors((er) => ({ ...er, min_rating: undefined }));
                        }}
                        className={cn(
                          "flex flex-1 items-center justify-center gap-1 rounded-lg border py-2.5 text-sm font-medium transition-colors",
                          active
                            ? "border-2 border-[#E23744] bg-white text-[#E23744] shadow-sm"
                            : "border-neutral-200 bg-neutral-50 text-neutral-600 hover:bg-neutral-100"
                        )}
                      >
                        {active && <Star className="h-3.5 w-3.5 fill-current" />}
                        {opt.label}
                      </button>
                    );
                  })}
                </div>
                {errors.min_rating && (
                  <p className="mt-1 text-xs text-red-600">{errors.min_rating}</p>
                )}
              </div>
            </div>

            {/* Additional preferences — full width */}
            <div>
              <FieldLabel required>Additional preferences</FieldLabel>
              <textarea
                required
                rows={2}
                placeholder="e.g. family-friendly, outdoor seating, Butter Chicken"
                value={params.additional_preferences || ""}
                onChange={(e) => {
                  setParams({ ...params, additional_preferences: e.target.value });
                  setErrors((er) => ({ ...er, additional_preferences: undefined }));
                }}
                className={cn(inputClass(!!errors.additional_preferences), "resize-none")}
              />
              {errors.additional_preferences && (
                <p className="mt-1 text-xs text-red-600">{errors.additional_preferences}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-lg py-3.5 text-base font-semibold text-white shadow-md transition-opacity hover:opacity-95 disabled:opacity-60"
              style={{ backgroundColor: ZOMATO_RED }}
            >
              {isLoading ? "Finding recommendations…" : "Get Recommendations"}
            </button>
          </form>
        </motion.div>

        {/* Results */}
        {hasSearched && (
          <div className="relative z-10 mt-8 w-full max-w-4xl">
            {isLoading ? (
              <LoadingSkeleton count={4} />
            ) : results ? (
              <div className="rounded-2xl bg-white/95 p-6 shadow-xl ring-1 ring-black/5">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-lg font-semibold text-neutral-900">
                    Top {results.total_results} recommendations
                  </h2>
                  <span className="text-xs text-neutral-500">
                    {results.processing_time_ms}ms
                  </span>
                </div>
                {results.summary && (
                  <p className="mb-4 text-sm text-neutral-600">{results.summary}</p>
                )}
                {results.rankings.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    {results.rankings.map((r, i) => (
                      <RestaurantCard key={r.id} restaurant={r} />
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-sm text-neutral-600">
                    <p>No restaurants match your criteria.</p>
                    {results.suggestions?.length > 0 && (
                      <ul className="mt-3 space-y-1 text-left">
                        {results.suggestions.map((s) => (
                          <li key={s}>• {s}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative z-10 mt-auto border-t border-white/20 bg-white/90 px-4 py-4 text-center backdrop-blur-md">
        <p className="text-lg font-bold" style={{ color: ZOMATO_RED }}>
          zomato
        </p>
        <p className="mt-1 text-xs text-neutral-500">
          © {new Date().getFullYear()} Zomato AI · Restaurant recommendations powered by Groq
        </p>
        <p className="mt-2 text-xs text-neutral-400">{apiStatus}</p>
      </footer>
    </div>
  );
}
