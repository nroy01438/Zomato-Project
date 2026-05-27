"use client";

import { motion } from "framer-motion";
import { UtensilsCrossed, Users, MapPin, Sparkles } from "lucide-react";

const stats = [
  { icon: UtensilsCrossed, value: "10,000+", label: "Restaurants", suffix: "" },
  { icon: MapPin, value: "50+", label: "Cities Covered", suffix: "" },
  { icon: Users, value: "100K+", label: "Happy Diners", suffix: "" },
  { icon: Sparkles, value: "98", label: "AI Accuracy", suffix: "%" },
];

export function StatsSection() {
  return (
    <section className="py-20 bg-primary/5">
      <div className="container">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="text-center"
            >
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10 mb-4">
                <stat.icon className="h-6 w-6 text-primary" />
              </div>
              <div className="font-display text-3xl lg:text-4xl font-bold mb-1">
                {stat.value}{stat.suffix}
              </div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
