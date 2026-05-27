"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { MapPin, DollarSign, Utensils, Star, Search, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { SearchParams } from "@/types";
import { api } from "@/lib/api";

interface SearchFormProps {
  onSearch: (params: SearchParams) => void;
  initialParams: SearchParams;
}

const budgets = [
  { value: 500, label: "Budget", icon: DollarSign, description: "Under ₹500" },
  { value: 1500, label: "Mid-range", icon: DollarSign, description: "₹500 - ₹1500" },
  { value: 3000, label: "Fine Dining", icon: DollarSign, description: "Above ₹1500" },
];

const cuisines = [
  "North Indian",
  "South Indian",
  "Biryani",
  "Chinese",
  "Italian",
  "Japanese",
  "Mexican",
  "Thai",
  "Cafe",
  "Desserts",
];

export function SearchForm({ onSearch, initialParams }: SearchFormProps) {
  const [params, setParams] = useState<SearchParams>(initialParams);
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>(
    initialParams.cuisine ? initialParams.cuisine.split(",").map((s) => s.trim()).filter(Boolean) : []
  );
  const [smartFilter, setSmartFilter] = useState(true);
  const [locations, setLocations] = useState<string[]>([]);
  const [locationsError, setLocationsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getLocations()
      .then((res) => {
        if (cancelled) return;
        setLocations(res.locations || []);
        setLocationsError(null);
      })
      .catch(() => {
        if (cancelled) return;
        setLocations([]);
        setLocationsError("Could not load locations from API.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      ...params,
      cuisine: selectedCuisines.join(","),
    });
  };

  const toggleCuisine = (cuisine: string) => {
    setSelectedCuisines((prev) =>
      prev.includes(cuisine)
        ? prev.filter((c) => c !== cuisine)
        : [...prev, cuisine]
    );
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      onSubmit={handleSubmit}
      className="bg-card rounded-2xl p-6 shadow-lg border"
    >
      {/* Location */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Location</label>
        <div className="relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          {locations.length > 0 ? (
            <select
              value={params.location}
              onChange={(e) => setParams({ ...params, location: e.target.value })}
              className="w-full pl-10 pr-4 py-3 rounded-lg border bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            >
              <option value="" disabled>
                Select a location
              </option>
              {locations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              placeholder={locationsError ? "Enter a location (API unavailable)" : "Enter city or area"}
              value={params.location}
              onChange={(e) => setParams({ ...params, location: e.target.value })}
              className="w-full pl-10 pr-4 py-3 rounded-lg border bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            />
          )}
        </div>
        {locationsError && (
          <p className="mt-2 text-xs text-muted-foreground">{locationsError}</p>
        )}
      </div>

      {/* Budget */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Budget</label>
        <div className="grid grid-cols-3 gap-3">
          {budgets.map((budget) => (
            <button
              key={budget.value}
              type="button"
              onClick={() => setParams({ ...params, budget: budget.value })}
              className={cn(
                "p-3 rounded-lg border text-center transition-all",
                params.budget === budget.value
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              )}
            >
              <budget.icon className="h-5 w-5 mx-auto mb-1 text-primary" />
              <div className="text-sm font-medium">{budget.label}</div>
              <div className="text-xs text-muted-foreground">{budget.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Cuisine */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Cuisine Type</label>
        <div className="flex flex-wrap gap-2">
          {cuisines.map((cuisine) => (
            <button
              key={cuisine}
              type="button"
              onClick={() => toggleCuisine(cuisine)}
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium transition-all",
                selectedCuisines.includes(cuisine)
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              )}
            >
              {cuisine}
            </button>
          ))}
        </div>
      </div>

      {/* Rating */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">
          Minimum Rating: {params.min_rating}★
        </label>
        <input
          type="range"
          min="1"
          max="5"
          step="0.5"
          value={params.min_rating}
          onChange={(e) => setParams({ ...params, min_rating: parseFloat(e.target.value) })}
          className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>1★</span>
          <span>5★</span>
        </div>
      </div>

      {/* Additional preferences */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Additional preferences (optional)</label>
        <textarea
          placeholder="e.g. family-friendly, outdoor seating, good for groups"
          value={params.additional_preferences || ""}
          onChange={(e) => setParams({ ...params, additional_preferences: e.target.value })}
          rows={3}
          className="w-full px-4 py-3 rounded-lg border bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none"
        />
      </div>

      {/* Smart Filter Toggle */}
      <div className="mb-6 flex items-center justify-between p-4 bg-muted/50 rounded-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Sparkles className="h-5 w-5 text-primary" />
          </div>
          <div>
            <div className="font-medium">Smart AI Filters</div>
            <div className="text-sm text-muted-foreground">Enhanced recommendations using AI</div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setSmartFilter(!smartFilter)}
          className={cn(
            "w-12 h-6 rounded-full transition-colors relative",
            smartFilter ? "bg-primary" : "bg-muted"
          )}
        >
          <span
            className={cn(
              "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
              smartFilter ? "left-7" : "left-1"
            )}
          />
        </button>
      </div>

      {/* Submit */}
      <Button
        type="submit"
        size="lg"
        className="w-full text-lg gap-2"
        disabled={!params.location}
      >
        <Search className="h-5 w-5" />
        Find Restaurants
      </Button>
    </motion.form>
  );
}
