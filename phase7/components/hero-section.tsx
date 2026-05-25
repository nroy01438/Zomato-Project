"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Search, Sparkles, ChevronRight } from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-secondary/5" />
      
      {/* Decorative elements */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-primary/10 rounded-full blur-3xl" />
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/10 rounded-full blur-3xl" />

      <div className="container relative py-20 lg:py-32">
        <div className="flex flex-col items-center text-center space-y-8">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium">
              <Sparkles className="h-4 w-4" />
              <span>AI-Powered Recommendations</span>
            </div>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight max-w-4xl"
          >
            Discover Your Perfect{" "}
            <span className="text-primary">Dining Experience</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg text-muted-foreground max-w-2xl"
          >
            Let our AI find the best restaurants tailored to your preferences. 
            From local gems to fine dining, we&apos;ve got you covered.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4"
          >
            <Link href="/search">
              <Button size="lg" className="gap-2 text-lg px-8">
                <Search className="h-5 w-5" />
                Find Restaurants
              </Button>
            </Link>
            <Link href="#how-it-works">
              <Button variant="outline" size="lg" className="gap-2 text-lg px-8">
                How It Works
                <ChevronRight className="h-5 w-5" />
              </Button>
            </Link>
          </motion.div>

          {/* Trust indicators */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="flex items-center gap-8 pt-8 text-sm text-muted-foreground"
          >
            <div className="flex items-center gap-2">
              <div className="flex -space-x-2">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="w-8 h-8 rounded-full bg-muted border-2 border-background"
                  />
                ))}
              </div>
              <span>10,000+ happy diners</span>
            </div>
            <div className="hidden sm:block h-4 w-px bg-border" />
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-yellow-500">★★★★★</span>
              <span>4.9/5 rating</span>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
