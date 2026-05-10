"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { useAuthStore } from "@/lib/store";
import api from "@/lib/api";
import type { AnalyticsDashboard } from "@/types";

export default function AdminDashboard() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchUser } = useAuthStore();
  const [analytics, setAnalytics] = useState<AnalyticsDashboard | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/auth/login");
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated && user?.is_admin) {
      async function loadStats() {
        try {
          const response = await api.get("/analytics/dashboard");
          setAnalytics(response.data);
        } catch {
          console.error("Failed to load analytics");
        } finally {
          setStatsLoading(false);
        }
      }
      loadStats();
    }
  }, [isAuthenticated, user]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg">
        <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!user?.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Access Denied</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Admin access required.</p>
          <Link href="/" className="mt-4 inline-block text-primary-500 hover:text-primary-600">
            Go home
          </Link>
        </div>
      </div>
    );
  }

  const statCards = [
    { label: "Total Views", value: analytics?.total_views || 0 },
    { label: "Unique Visitors", value: analytics?.unique_visitors || 0 },
    { label: "Avg/Day", value: analytics?.avg_views_per_day || 0 },
    { label: "Bounce Rate", value: `${analytics?.bounce_rate || 0}%` },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      {/* Admin Header */}
      <header className="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border">
        <div className="container-custom flex items-center justify-between h-16">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-xl font-bold gradient-text">
              &lt;Dev /&gt;
            </Link>
            <span className="px-2 py-0.5 text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded">
              Admin
            </span>
          </div>
          <nav className="flex items-center gap-6">
            <Link href="/admin/projects" className="text-sm text-gray-600 dark:text-gray-300 hover:text-primary-500">
              Projects
            </Link>
            <Link href="/admin/blog" className="text-sm text-gray-600 dark:text-gray-300 hover:text-primary-500">
              Blog
            </Link>
            <Link href="/admin/messages" className="text-sm text-gray-600 dark:text-gray-300 hover:text-primary-500">
              Messages
            </Link>
            <span className="text-sm text-gray-500 dark:text-gray-400">{user.full_name}</span>
          </nav>
        </div>
      </header>

      {/* Dashboard Content */}
      <main className="container-custom py-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">Dashboard</h1>

        {/* Stats Grid */}
        {statsLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 rounded-xl bg-gray-100 dark:bg-dark-surface animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {statCards.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-6 rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface"
              >
                <p className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</p>
                <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
              </motion.div>
            ))}
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/admin/projects/new"
            className="p-6 rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface hover:border-primary-500 transition-colors"
          >
            <h3 className="font-semibold text-gray-900 dark:text-white">New Project</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Add a new project to your portfolio</p>
          </Link>
          <Link
            href="/admin/blog/new"
            className="p-6 rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface hover:border-primary-500 transition-colors"
          >
            <h3 className="font-semibold text-gray-900 dark:text-white">New Blog Post</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Write and publish a new article</p>
          </Link>
          <Link
            href="/admin/messages"
            className="p-6 rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface hover:border-primary-500 transition-colors"
          >
            <h3 className="font-semibold text-gray-900 dark:text-white">Messages</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">View contact form submissions</p>
          </Link>
        </div>

        {/* Top Pages */}
        {analytics && analytics.top_pages.length > 0 && (
          <div className="mt-8 p-6 rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Pages</h2>
            <div className="space-y-3">
              {analytics.top_pages.slice(0, 5).map((page) => (
                <div key={page.path} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700 dark:text-gray-300 font-mono">{page.path}</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">{page.views} views</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
