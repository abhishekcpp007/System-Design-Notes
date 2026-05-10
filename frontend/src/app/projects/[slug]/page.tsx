import { Metadata } from "next";
import { notFound } from "next/navigation";
import { getProjectBySlug, getProjectSlugs } from "@/lib/server-api";

/**
 * Generate static params for all project slugs at build time.
 * Enables Static Site Generation (SSG) for project detail pages.
 */
export async function generateStaticParams() {
  const slugs = await getProjectSlugs();
  return slugs.map((slug) => ({ slug }));
}

/**
 * Dynamic metadata for SEO.
 */
export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const project = await getProjectBySlug(params.slug);
  if (!project) return { title: "Project Not Found" };

  return {
    title: `${project.title} | Projects`,
    description: project.description,
    openGraph: {
      title: project.title,
      description: project.description,
      images: project.thumbnail_url ? [project.thumbnail_url] : [],
      type: "article",
    },
    twitter: {
      card: "summary_large_image",
      title: project.title,
      description: project.description,
    },
  };
}

/**
 * ISR revalidation: regenerate page every 5 minutes.
 */
export const revalidate = 300;

export default async function ProjectDetailPage({
  params,
}: {
  params: { slug: string };
}) {
  const project = await getProjectBySlug(params.slug);

  if (!project) {
    notFound();
  }

  return (
    <main className="min-h-screen pt-20 pb-16" role="main">
      <article className="container-custom" aria-labelledby="project-title">
        {/* Back navigation */}
        <nav aria-label="Breadcrumb" className="mb-8">
          <a
            href="/projects"
            className="inline-flex items-center text-sm text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
            aria-label="Back to all projects"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            All Projects
          </a>
        </nav>

        {/* Hero Section */}
        <header className="mb-12">
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <span
              className="px-3 py-1 text-xs font-medium rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
              aria-label={`Category: ${project.category}`}
            >
              {project.category}
            </span>
            <span
              className={`px-3 py-1 text-xs font-medium rounded-full ${
                project.status === "completed"
                  ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
                  : "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300"
              }`}
              aria-label={`Status: ${project.status}`}
            >
              {project.status === "completed" ? "Completed" : "In Progress"}
            </span>
          </div>

          <h1
            id="project-title"
            className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4"
          >
            {project.title}
          </h1>

          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-3xl">
            {project.description}
          </p>
        </header>

        {/* Project Image */}
        {project.thumbnail_url && (
          <figure className="mb-12 rounded-xl overflow-hidden border border-gray-200 dark:border-dark-border">
            <img
              src={project.thumbnail_url}
              alt={`Screenshot of ${project.title}`}
              className="w-full h-auto object-cover"
              loading="eager"
            />
          </figure>
        )}

        {/* Links */}
        <div className="flex flex-wrap gap-4 mb-12" role="group" aria-label="Project links">
          {project.live_url && (
            <a
              href={project.live_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-dark-bg"
              aria-label={`Visit live demo of ${project.title} (opens in new tab)`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              Live Demo
            </a>
          )}
          {project.github_url && (
            <a
              href={project.github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-gray-300 dark:border-dark-border text-gray-700 dark:text-gray-200 font-medium hover:bg-gray-50 dark:hover:bg-dark-surface transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-dark-bg"
              aria-label={`View source code on GitHub (opens in new tab)`}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              Source Code
            </a>
          )}
        </div>

        {/* Tech Stack */}
        <section aria-labelledby="tech-stack-heading" className="mb-12">
          <h2 id="tech-stack-heading" className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Tech Stack
          </h2>
          <ul className="flex flex-wrap gap-2" role="list" aria-label="Technologies used">
            {project.tech_stack.map((tech) => (
              <li
                key={tech}
                className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-dark-surface text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                {tech}
              </li>
            ))}
          </ul>
        </section>

        {/* Long Description */}
        {project.long_description && (
          <section aria-labelledby="about-heading" className="mb-12">
            <h2 id="about-heading" className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              About This Project
            </h2>
            <div className="prose prose-lg dark:prose-invert max-w-none">
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                {project.long_description}
              </p>
            </div>
          </section>
        )}
      </article>
    </main>
  );
}
