"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Utensils, Pizza, Soup, Fish, Beef, Salad, Coffee, Cake } from "lucide-react";

const categories = [
  { id: "italian", name: "Italian", icon: Pizza, count: 2340, color: "bg-orange-500" },
  { id: "japanese", name: "Japanese", icon: Fish, count: 1850, color: "bg-red-500" },
  { id: "indian", name: "Indian", icon: Soup, count: 1650, color: "bg-yellow-500" },
  { id: "american", name: "American", icon: Beef, count: 2100, color: "bg-blue-500" },
  { id: "chinese", name: "Chinese", icon: Utensils, count: 1920, color: "bg-red-600" },
  { id: "mediterranean", name: "Mediterranean", icon: Salad, count: 1280, color: "bg-green-500" },
  { id: "cafe", name: "Café", icon: Coffee, count: 3150, color: "bg-amber-600" },
  { id: "dessert", name: "Dessert", icon: Cake, count: 1420, color: "bg-pink-500" },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export function FeaturedCategories() {
  return (
    <section className="py-20 bg-muted/50">
      <div className="container">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl font-bold mb-4">
            Explore by Cuisine
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            From local favorites to international delights, find restaurants that match your taste
          </p>
        </div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4"
        >
          {categories.map((category) => (
            <motion.div key={category.id} variants={itemVariants}>
              <Link href={`/search?cuisine=${category.id}`}>
                <div className="group relative overflow-hidden rounded-xl bg-card p-6 shadow-sm transition-all hover:shadow-md hover:-translate-y-1">
                  <div className={`${category.color} w-12 h-12 rounded-lg flex items-center justify-center mb-4`}>
                    <category.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="font-semibold text-lg mb-1">{category.name}</h3>
                  <p className="text-sm text-muted-foreground">{category.count.toLocaleString()} restaurants</p>
                </div>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
