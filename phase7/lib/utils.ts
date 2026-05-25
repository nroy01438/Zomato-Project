import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge tailwind classes with clsx
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format currency value
 */
export function formatCurrency(amount: number, currency: string = "₹"): string {
  return `${currency}${amount.toLocaleString()}`;
}

/**
 * Format rating with stars
 */
export function formatRating(rating: number): string {
  const stars = "★".repeat(Math.floor(rating)) + "☆".repeat(5 - Math.floor(rating));
  return `${stars} ${rating.toFixed(1)}`;
}

/**
 * Get price range indicator
 */
export function getPriceRange(price: number): string {
  if (price < 500) return "₹";
  if (price < 1000) return "₹₹";
  if (price < 2000) return "₹₹₹";
  return "₹₹₹₹";
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "...";
}

/**
 * Generate unique ID
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Format date relative
 */
export function formatRelativeDate(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diffInSeconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (diffInSeconds < 60) return "just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
  return then.toLocaleDateString();
}
