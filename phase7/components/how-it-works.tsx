"use client";

import { motion } from "framer-motion";
import { Search, Filter, Sparkles, Utensils } from "lucide-react";

const steps = [
  {
    icon: Search,
    title: "Tell Us Your Preferences",
    description: "Enter your location, budget, cuisine type, and rating preferences. Our smart form makes it quick and easy.",
    color: "bg-blue-500",
  },
  {
    icon: Filter,
    title: "AI Filters & Ranks",
    description: "Our AI scans thousands of restaurants, applies your filters, and ranks them based on quality, relevance, and reviews.",
    color: "bg-purple-500",
  },
  {
    icon: Sparkles,
    title: "Get Personalized Recommendations",
    description: "Receive a curated list with AI-generated explanations for why each restaurant matches your taste.",
    color: "bg-primary",
  },
  {
    icon: Utensils,
    title: "Enjoy Your Perfect Meal",
    description: "View details, check menus, read reviews, and book your table. Save favorites for future visits.",
    color: "bg-secondary",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20">
      <div className="container">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold mb-4">
            How It Works
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Finding your perfect restaurant is simple with our AI-powered recommendation system
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="relative"
            >
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-8 left-full w-full h-0.5 bg-border -translate-y-1/2" />
              )}
              
              <div className="flex flex-col items-center text-center">
                <div className={`${step.color} w-16 h-16 rounded-full flex items-center justify-center mb-6 shadow-lg`}>
                  <step.icon className="h-7 w-7 text-white" />
                </div>
                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center mb-4 font-bold text-sm">
                  {index + 1}
                </div>
                <h3 className="font-semibold text-lg mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
