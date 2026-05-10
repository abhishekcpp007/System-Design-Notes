"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import api from "@/lib/api";
import type { Project } from "@/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    async function fetchProjects() {
      try {
        const params: Record<string, string> = {};
        if (filter !== "all") params.status = filter;

        const response = await api.get("/projects", { params });
        setProjects(response.data.items || response.data);
      } catch (error) {
        console.error("Failed to fetch projects:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchProjects();
  }, [filter]);

  const filters = [
    { label: "All", value: "all" },
    { label: "Completed", value: "completed" },
    { label: "In Progress", value: "in_progress" },
  ];

  return (
    <>
      <Navbar />
      <main className="pt-20 min-h-screen">
        <section className="section-padding">
          <div className="container-custom">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-12"
            >
              <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white">
                My <span className="gradient-text">Projects</span>
              </h1>
              <p className="mt-4 text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                A collection of projects I&apos;ve built, from full-stack applications
                to open-source tools.
              </p>
            </motion.div>

            {/* Filters */}
            <div className="flex items-center justify-center gap-3 mb-12">
              {filters.map((f) => (
                <button
                  key={f.value}
                  onClick={() => setFilter(f.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    filter === f.value
                      ? "bg-primary-600 text-white shadow-lg shadow-primary-500/25"
                      : "bg-gray-100 dark:bg-dark-surface text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-border"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {/* Projects Grid */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div
                    key={i}
                    className="h-80 rounded-xl bg-gray-100 dark:bg-dark-surface animate-pulse"
                  />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects.map((project, index) => (
                  <motion.article
                    key={project.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="group rounded-xl border border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface overflow-hidden hover-lift"
                  >
                    {/* Project image */}
                    <div className="h-48 bg-gradient-to-br from-primary-500/20 to-purple-500/20 flex items-center justify-center">
                      <span className="text-4xl font-bold text-primary-500/50">
                        {project.title[0]}
                      </span>
                    </div>

                    {/* Content */}
                    <div className="p-6">
                      <div className="flex items-center gap-2 mb-2">
                        {project.featured && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-full">
                            Featured
                          </span>
                        )}
                        <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 dark:bg-dark-bg text-gray-600 dark:text-gray-400 rounded-full capitalize">
                          {project.status.replace("_", " ")}
                        </span>
                      </div>

                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-primary-500 transition-colors">
                        {project.title}
                      </h3>
                      <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                        {project.description}
                      </p>

                      {/* Tech stack */}
                      <div className="mt-4 flex flex-wrap gap-1.5">
                        {project.tech_stack.slice(0, 4).map((tech) => (
                          <span
                            key={tech}
                            className="px-2 py-0.5 text-xs bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 rounded"
                          >
                            {tech}
                          </span>
                        ))}
                        {project.tech_stack.length > 4 && (
                          <span className="px-2 py-0.5 text-xs text-gray-500">
                            +{project.tech_stack.length - 4}
                          </span>
                        )}
                      </div>

                      {/* Links */}
                      <div className="mt-4 flex items-center gap-3">
                        {project.live_url && (
                          <a
                            href={project.live_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                          >
                            Live Demo &rarr;
                          </a>
                        )}
                        {project.github_url && (
                          <a
                            href={project.github_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                          >
                            Source Code
                          </a>
                        )}
                      </div>
                    </div>
                  </motion.article>
                ))}
              </div>
            )}

            {!loading && projects.length === 0 && (
              <div className="text-center py-16">
                <p className="text-gray-500 dark:text-gray-400">
                  No projects found. Check back soon!
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
