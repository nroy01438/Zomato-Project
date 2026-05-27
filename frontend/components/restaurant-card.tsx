"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Star, MapPin, DollarSign, Heart, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Restaurant } from "@/types";
import { cn, formatCurrency, getPriceRange } from "@/lib/utils";
import { useSavedRestaurantsStore } from "@/lib/store";

interface RestaurantCardProps {
  restaurant: Restaurant;
  className?: string;
}

export function RestaurantCard({ restaurant, className }: RestaurantCardProps) {
  const { saved, addRestaurant, removeRestaurant } = useSavedRestaurantsStore();
  const isSaved = saved.some((r) => r.id === restaurant.id);

  const toggleSave = () => {
    if (isSaved) {
      removeRestaurant(restaurant.id);
    } else {
      addRestaurant(restaurant);
    }
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className={cn(
        "group bg-card rounded-xl overflow-hidden shadow-sm border transition-shadow hover:shadow-md",
        className
      )}
    >
      {/* Image */}
      <div className="relative aspect-video bg-muted">
        {restaurant.image_url ? (
          <img
            src={restaurant.image_url}
            alt={restaurant.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-muted to-muted/50">
            <span className="text-4xl">🍽️</span>
          </div>
        )}
        
        {/* AI Badge */}
        {restaurant.ai_recommended && (
          <div className="absolute top-3 left-3 px-2 py-1 bg-primary text-primary-foreground text-xs font-medium rounded-full flex items-center gap-1">
            <Sparkles className="h-3 w-3" />
            AI Pick
          </div>
        )}

        {/* Save Button */}
        <button
          onClick={toggleSave}
          className="absolute top-3 right-3 p-2 rounded-full bg-white/90 backdrop-blur-sm shadow-sm transition-colors hover:bg-white"
        >
          <Heart
            className={cn(
              "h-4 w-4 transition-colors",
              isSaved ? "fill-red-500 text-red-500" : "text-muted-foreground"
            )}
          />
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="font-semibold text-lg line-clamp-1">{restaurant.name}</h3>
          <div className="flex items-center gap-1 text-sm">
            <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
            <span className="font-medium">{restaurant.rating}</span>
            <span className="text-muted-foreground">({restaurant.votes})</span>
          </div>
        </div>

        {/* Cuisines */}
        <div className="flex flex-wrap gap-1 mb-3">
          {restaurant.cuisines.slice(0, 3).map((cuisine) => (
            <span
              key={cuisine}
              className="px-2 py-0.5 bg-muted text-xs rounded-full text-muted-foreground"
            >
              {cuisine}
            </span>
          ))}
        </div>

        {/* Info */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
          <div className="flex items-center gap-1">
            <MapPin className="h-4 w-4" />
            <span className="line-clamp-1">{restaurant.location}</span>
          </div>
          <div className="flex items-center gap-1">
            <DollarSign className="h-4 w-4" />
            <span>{getPriceRange(restaurant.cost_for_two)}</span>
          </div>
        </div>

        {/* Explanation */}
        {restaurant.explanation && (
          <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
            {restaurant.explanation}
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <Link href={`/restaurant/${restaurant.id}`} className="flex-1">
            <Button variant="outline" className="w-full">
              View Details
            </Button>
          </Link>
          <Button className="flex-1">Get Directions</Button>
        </div>
      </div>
    </motion.div>
  );
}
