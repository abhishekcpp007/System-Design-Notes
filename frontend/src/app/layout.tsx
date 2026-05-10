import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "@/styles/globals.css";
import { SkipToContent } from "@/components/ui/accessibility";
import { WebVitalsReporter } from "@/lib/web-vitals";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Abhishek Verma | Full-Stack Developer & Data Engineer",
    template: "%s | Abhishek Verma",
  },
  description:
    "Full-Stack Developer & Data Engineer with experience building scalable web applications, designing efficient data pipelines, and integrating secure RESTful APIs. Proficient in Python, React, Node.js, and modern web frameworks.",
  keywords: [
    "abhishek verma",
    "full-stack developer",
    "data engineer",
    "react",
    "python",
    "nextjs",
    "fastapi",
    "node.js",
    "postgresql",
    "docker",
    "aws",
  ],
  authors: [{ name: "Abhishek Verma" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "Abhishek Verma Portfolio",
  },
  twitter: {
    card: "summary_large_image",
  },
  robots: {
    index: true,
    follow: true,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}
      >
        {/* WCAG 2.1: Skip to main content link for keyboard users */}
        <SkipToContent />

        {/* Web Vitals measurement */}
        <WebVitalsReporter />

        <div id="main-content">
          {children}
        </div>
      </body>
    </html>
  );
}
