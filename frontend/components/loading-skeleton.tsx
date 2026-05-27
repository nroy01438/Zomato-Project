"use client";

import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  count?: number;
  className?: string;
}

export function LoadingSkeleton({ count = 6, className }: LoadingSkeletonProps) {
  return (
    <div className={cn("grid md:grid-cols-2 gap-6", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-card rounded-xl overflow-hidden shadow-sm border animate-pulse"
        >
          {/* Image skeleton */}
          <div className="aspect-video bg-muted" />
          
          {/* Content skeleton */}
          <div className="p-4 space-y-3">
            <div className="flex justify-between">
              <div className="h-5 bg-muted rounded w-2/3" />
              <div className="h-5 bg-muted rounded w-16" />
            </div>
            <div className="flex gap-2">
              <div className="h-4 bg-muted rounded w-16" />
              <div className="h-4 bg-muted rounded w-16" />
              <div className="h-4 bg-muted rounded w-16" />
            </div>
            <div className="h-4 bg-muted rounded w-full" />
            <div className="h-4 bg-muted rounded w-3/4" />
            <div className="flex gap-2 pt-2">
              <div className="h-10 bg-muted rounded flex-1" />
              <div className="h-10 bg-muted rounded flex-1" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
