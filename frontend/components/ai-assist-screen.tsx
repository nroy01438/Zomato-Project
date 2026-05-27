"use client";

import Link from "next/link";
import { useState, type ReactNode } from "react";
import {
  MapPin,
  Navigation,
  UtensilsCrossed,
  Star,
  Bike,
  Bot,
  Wallet,
  User,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

const brand = "#B21E2C";
const brandMuted = "#8B1520";

const ratingOptions = ["3.5+", "4.0+", "4.5+"] as const;
const budgetOptions = ["₹", "₹₹", "₹₹₹", "₹₹₹₹"] as const;

export function AiAssistScreen() {
  const [minRating, setMinRating] = useState<(typeof ratingOptions)[number]>("4.0+");
  const [budget, setBudget] = useState<(typeof budgetOptions)[number]>("₹₹₹");

  return (
    <div className="min-h-dvh flex flex-col bg-[#FAFAFA] text-neutral-900 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-4 pt-5 pb-2">
        <div className="flex items-center gap-1.5">
          <MapPin className="h-4 w-4 shrink-0" style={{ color: brand }} aria-hidden />
          <span className="text-[15px] font-semibold" style={{ color: brand }}>
            New Delhi, India
          </span>
        </div>
        <button
          type="button"
          className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-neutral-500 to-neutral-700 ring-2 ring-white shadow-md"
          aria-label="Profile"
        >
          <User className="h-5 w-5 text-white" aria-hidden />
        </button>
      </header>

      {/* Hero */}
      <div className="px-4 pt-2 pb-4">
        <h1 className="font-display text-[26px] leading-tight font-bold tracking-tight text-neutral-900 sm:text-[28px]">
          Find your next favorite meal
        </h1>
        <p className="mt-2 text-sm text-neutral-500 leading-relaxed max-w-md">
          AI-powered recommendations tailored to your taste buds.
        </p>
      </div>

      {/* Search card */}
      <div className="mx-4 rounded-2xl bg-white p-4 shadow-[0_8px_30px_rgb(0,0,0,0.08)] ring-1 ring-black/[0.04]">
        <div className="space-y-5">
          <FieldBlock label="LOCATION">
            <div className="flex items-center gap-3 rounded-xl border border-neutral-200 bg-neutral-50/80 px-3.5 py-3">
              <Navigation className="h-4 w-4 shrink-0 text-neutral-400" aria-hidden />
              <span className="text-[15px] text-neutral-700">New Delhi, India</span>
            </div>
          </FieldBlock>

          <FieldBlock label="CUISINE">
            <div className="flex items-center gap-3 rounded-xl border border-neutral-200 bg-neutral-50/80 px-3.5 py-3">
              <UtensilsCrossed className="h-4 w-4 shrink-0 text-neutral-400" aria-hidden />
              <span className="text-[15px] text-neutral-700">North Indian, Biryani</span>
            </div>
          </FieldBlock>

          <FieldBlock label="MINIMUM RATING">
            <div className="flex gap-2">
              {ratingOptions.map((opt) => {
                const active = minRating === opt;
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setMinRating(opt)}
                    className={cn(
                      "flex flex-1 items-center justify-center gap-1 rounded-xl border py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "border-2 bg-white shadow-sm"
                        : "border border-neutral-200 bg-neutral-50/50 text-neutral-600 hover:bg-neutral-100"
                    )}
                    style={
                      active
                        ? { borderColor: brand, color: brandMuted }
                        : undefined
                    }
                  >
                    {active && <Star className="h-3.5 w-3.5 fill-current" style={{ color: brand }} />}
                    {opt}
                  </button>
                );
              })}
            </div>
          </FieldBlock>

          <FieldBlock label="BUDGET (PER PERSON)">
            <div className="flex gap-2">
              {budgetOptions.map((opt) => {
                const active = budget === opt;
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setBudget(opt)}
                    className={cn(
                      "flex-1 rounded-xl border py-2.5 text-center text-sm font-semibold transition-colors",
                      active
                        ? "border-2 bg-white shadow-sm"
                        : "border border-neutral-200 bg-neutral-50/50 text-neutral-600 hover:bg-neutral-100"
                    )}
                    style={
                      active
                        ? { borderColor: brand, color: brand }
                        : undefined
                    }
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
          </FieldBlock>

          <Link
            href="/search"
            className="mt-1 flex w-full items-center justify-center rounded-xl py-3.5 text-[15px] font-bold text-white shadow-md transition-opacity hover:opacity-95 active:opacity-90"
            style={{ backgroundColor: brand }}
          >
            Get Recommendations
          </Link>
        </div>
      </div>

      {/* Content preview strip (food imagery placeholder) */}
      <div
        className="relative mx-4 mt-4 h-28 overflow-hidden rounded-xl bg-neutral-800 bg-cover bg-center shadow-inner"
        style={{
          backgroundImage:
            "linear-gradient(180deg, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.55) 100%), url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 120'%3E%3Crect fill='%23222' width='400' height='120'/%3E%3Ccircle cx='120' cy='40' r='50' fill='%23333'/%3E%3Ccircle cx='280' cy='80' r='40' fill='%232a2a2a'/%3E%3C/svg%3E\")",
        }}
        aria-hidden
      />

      <div className="flex-1 min-h-4" aria-hidden />

      {/* Bottom navigation */}
      <nav
        className="sticky bottom-0 mt-auto border-t border-neutral-100 bg-white px-2 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2"
        aria-label="Primary"
      >
        <div className="mx-auto flex max-w-md items-stretch justify-between gap-1">
          <BottomTab icon={Bike} label="Delivery" active={false} />
          <BottomTab icon={UtensilsCrossed} label="Dining" active={false} />
          <BottomTab icon={Bot} label="AI Assist" active />
          <BottomTab icon={Wallet} label="Money" active={false} />
        </div>
      </nav>
    </div>
  );
}

function FieldBlock({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-neutral-400">
        {label}
      </p>
      {children}
    </div>
  );
}

function BottomTab({
  icon: Icon,
  label,
  active,
}: {
  icon: LucideIcon;
  label: string;
  active: boolean;
}) {
  return (
    <button
      type="button"
      className={cn(
        "flex flex-1 flex-col items-center gap-1 py-2 text-[11px] font-medium transition-colors",
        active ? "" : "text-neutral-400 hover:text-neutral-600"
      )}
      style={active ? { color: brand } : undefined}
      aria-current={active ? "page" : undefined}
    >
      <Icon className="h-5 w-5" style={active ? { color: brand } : undefined} />
      {label}
    </button>
  );
}
