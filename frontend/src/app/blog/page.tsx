"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import api from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { BlogPost } from "@/types";

export default function BlogPage() {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function fetchPosts() {
      try {
        const params: Record<string, string> = { published: "true" };
        if (searchQuery) params.search = searchQuery;

        const response = await api.get("/blog", { params });
        setPosts(response.data.items || response.data);
      } catch (error) {
        console.error("Failed to fetch posts:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchPosts();
  }, [searchQuery]);

  return (
    <>
      <Navbar />
      <main className="pt-20 min-h-screen">
        <section className="section-padding">
          <div className="container-custom max-w-4xl">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-12"
            >
              <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white">
                The <span className="gradient-text">Blog</span>
              </h1>
              <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
                Thoughts on development, architecture, and building better software.
              </p>
            </motion.div>

            {/* Search */}
            <div className="mb-10">
              <input
                type="text"
                placeholder="Search articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all"
              />
            </div>

            {/* Posts */}
            {loading ? (
              <div className="space-y-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-40 rounded-xl bg-gray-100 dark:bg-dark-surface animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="space-y-8">
                {posts.map((post, index) => (
                  <motion.article
                    key={post.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="group"
                  >
                    <Link href={`/blog/${post.slug}`}>
                      <div className="p-6 rounded-xl border border-gray-200 dark:border-dark-border hover:border-primary-500/50 dark:hover:border-primary-500/50 bg-white dark:bg-dark-surface transition-all hover-lift">
                        {/* Meta */}
                        <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400 mb-3">
                          <time>{formatDate(post.created_at)}</time>
                          <span>&bull;</span>
                          <span>{post.reading_time} min read</span>
                          <span>&bull;</span>
                          <span>{post.views} views</span>
                        </div>

                        {/* Title */}
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white group-hover:text-primary-500 transition-colors">
                          {post.title}
                        </h2>

                        {/* Excerpt */}
                        <p className="mt-2 text-gray-600 dark:text-gray-400 line-clamp-2">
                          {post.excerpt}
                        </p>

                        {/* Tags */}
                        <div className="mt-4 flex flex-wrap gap-2">
                          {post.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2.5 py-0.5 text-xs font-medium bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </Link>
                  </motion.article>
                ))}
              </div>
            )}

            {!loading && posts.length === 0 && (
              <div className="text-center py-16">
                <p className="text-gray-500 dark:text-gray-400">
                  {searchQuery ? "No articles found matching your search." : "No blog posts yet. Stay tuned!"}
                </p>
              </div>
            )}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
