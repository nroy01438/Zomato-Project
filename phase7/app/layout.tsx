import type { Metadata } from "next";
import { Inter, Poppins } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { QueryProvider } from "@/components/query-provider";
import { Toaster } from "@/components/ui/toaster";
import { AppChrome } from "@/components/app-chrome";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-poppins",
});

export const metadata: Metadata = {
  title: "RestaurantFinder AI - Discover Your Perfect Dining Experience",
  description:
    "AI-powered restaurant recommendations tailored to your preferences. Find the best restaurants based on location, budget, cuisine, and more.",
  keywords: [
    "restaurant recommendations",
    "AI dining",
    "food discovery",
    "restaurant finder",
    "dining suggestions",
  ],
  authors: [{ name: "RestaurantFinder AI" }],
  openGraph: {
    title: "RestaurantFinder AI",
    description: "Discover your perfect restaurant with AI-powered recommendations",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${poppins.variable} font-sans antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <AppChrome>{children}</AppChrome>
            <Toaster />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
