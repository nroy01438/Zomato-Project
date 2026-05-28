"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { MapPin, UtensilsCrossed, Star, IndianRupee } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { useSearchStore } from "@/lib/store";
import { SearchParams } from "@/types";
import { RestaurantCard } from "@/components/restaurant-card";
import { LoadingSkeleton } from "@/components/loading-skeleton";

const ZOMATO_RED = "#E23744";

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

function iconWrap() {
  return "absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400";
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
    <div className="relative min-h-dvh bg-neutral-950 text-white">
      {/* Hero background (photo-like) */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1528605248644-14dd04022da1?auto=format&fit=crop&w=2400&q=70')",
        }}
        aria-hidden
      />
      <div className="absolute inset-0 bg-black/55" aria-hidden />

      {/* Top bar */}
      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-5">
        <div className="flex items-center gap-2">
          <span className="text-2xl font-extrabold tracking-tight" style={{ color: ZOMATO_RED }}>
            zomato
          </span>
        </div>
        <nav className="hidden items-center gap-6 text-sm text-white/80 md:flex">
          <a className="hover:text-white" href="#">
            Get the App
          </a>
          <a className="hover:text-white" href="#">
            Investor Relations
          </a>
          <a className="hover:text-white" href="#">
            Add restaurant
          </a>
          <a className="hover:text-white" href="#">
            Log in
          </a>
          <a className="hover:text-white" href="#">
            Sign up
          </a>
        </nav>
      </header>

      {/* Content */}
      <main className="relative z-10 mx-auto flex w-full max-w-6xl flex-col items-center px-4 pb-16 pt-4">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-4xl"
        >
          <div className="text-center">
            <div className="text-6xl font-black tracking-tight sm:text-7xl">
              <span className="drop-shadow-sm">zomato</span>
            </div>
            <p className="mt-3 text-xl text-white/90 sm:text-2xl">
              Discover the perfect dining experience
              <br className="hidden sm:block" /> using AI
            </p>
          </div>

          {/* Form card */}
          <div className="mt-10 rounded-2xl bg-white p-6 text-neutral-900 shadow-2xl ring-1 ring-black/10 sm:p-8">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                {/* Location */}
                <div>
                  <FieldLabel required>YOUR LOCATION</FieldLabel>
                  <div className="relative">
                    <MapPin className={iconWrap()} aria-hidden />
                    {locations.length > 0 ? (
                      <select
                        required
                        value={params.location}
                        onChange={(e) => {
                          setParams({ ...params, location: e.target.value });
                          setErrors((er) => ({ ...er, location: undefined }));
                        }}
                        className={cn(inputClass(!!errors.location), "pl-10")}
                      >
                        <option value="" disabled>
                          e.g. Indra Nagar, City Centre
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
                        placeholder="e.g. Indra Nagar, City Centre"
                        value={params.location}
                        onChange={(e) => {
                          setParams({ ...params, location: e.target.value });
                          setErrors((er) => ({ ...er, location: undefined }));
                        }}
                        className={cn(inputClass(!!errors.location), "pl-10")}
                      />
                    )}
                  </div>
                  {errors.location && (
                    <p className="mt-1 text-xs text-red-600">{errors.location}</p>
                  )}
                </div>

                {/* Cuisine */}
                <div>
                  <FieldLabel required>CUISINES</FieldLabel>
                  <div className="relative">
                    <UtensilsCrossed className={iconWrap()} aria-hidden />
                    <input
                      required
                      type="text"
                      placeholder="e.g. North Indian, Italian"
                      value={params.cuisine}
                      onChange={(e) => {
                        setParams({ ...params, cuisine: e.target.value });
                        setErrors((er) => ({ ...er, cuisine: undefined }));
                      }}
                      className={cn(inputClass(!!errors.cuisine), "pl-10")}
                    />
                  </div>
                  {errors.cuisine && (
                    <p className="mt-1 text-xs text-red-600">{errors.cuisine}</p>
                  )}
                </div>

                {/* Rating */}
                <div>
                  <FieldLabel required>MINIMUM RATING</FieldLabel>
                  <div className="relative">
                    <Star className={iconWrap()} aria-hidden />
                    <select
                      required
                      value={String(params.min_rating)}
                      onChange={(e) => {
                        setParams({ ...params, min_rating: Number(e.target.value) });
                        setErrors((er) => ({ ...er, min_rating: undefined }));
                      }}
                      className={cn(inputClass(!!errors.min_rating), "pl-10")}
                    >
                      {ratingOptions.map((o) => (
                        <option key={o.label} value={o.value}>
                          {o.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  {errors.min_rating && (
                    <p className="mt-1 text-xs text-red-600">{errors.min_rating}</p>
                  )}
                </div>

                {/* Budget */}
                <div>
                  <FieldLabel required>BUDGET</FieldLabel>
                  <div className="relative">
                    <IndianRupee className={iconWrap()} aria-hidden />
                    <input
                      required
                      type="number"
                      min={100}
                      step={100}
                      placeholder="e.g. 500-1000 (max ₹ for two)"
                      value={params.budget || ""}
                      onChange={(e) => {
                        setParams({ ...params, budget: Number(e.target.value) });
                        setErrors((er) => ({ ...er, budget: undefined }));
                      }}
                      className={cn(inputClass(!!errors.budget), "pl-10")}
                    />
                  </div>
                  {errors.budget && (
                    <p className="mt-1 text-xs text-red-600">{errors.budget}</p>
                  )}
                </div>
              </div>

              {/* Additional preferences */}
              <div>
                <FieldLabel required>ADDITIONAL PREFERENCES</FieldLabel>
                <textarea
                  required
                  rows={2}
                  placeholder="e.g. Quiet romantic, Rooftop, Vegan friendly"
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
                className="w-full rounded-xl py-3.5 text-base font-semibold text-white shadow-md transition-opacity hover:opacity-95 disabled:opacity-60"
                style={{ backgroundColor: ZOMATO_RED }}
              >
                {isLoading ? "Generating…" : "Generate Recommendations"}
              </button>
            </form>
          </div>
        </motion.div>

        {/* Results */}
        {hasSearched && (
          <div className="mt-10 w-full max-w-6xl">
            {isLoading ? (
              <LoadingSkeleton count={4} />
            ) : results ? (
              <div className="rounded-2xl bg-white/95 p-6 text-neutral-900 shadow-xl ring-1 ring-black/10 backdrop-blur">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-lg font-semibold">
                    Top {results.total_results} recommendations
                  </h2>
                  <span className="text-xs text-neutral-500">
                    {results.processing_time_ms}ms
                  </span>
                </div>
                {results.summary && (
                  <p className="mb-4 text-sm text-neutral-700">{results.summary}</p>
                )}
                {results.rankings.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    {results.rankings.map((r) => (
                      <RestaurantCard key={r.id} restaurant={r} />
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-sm text-neutral-700">
                    <p>No restaurants match your criteria.</p>
                    {results.suggestions?.length > 0 && (
                      <ul className="mx-auto mt-3 max-w-xl space-y-1 text-left">
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

        <p className="mt-10 text-center text-xs text-white/70">
          {apiStatus}
        </p>
      </main>
    </div>
  );
}
