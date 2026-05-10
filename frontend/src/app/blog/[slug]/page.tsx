import { Metadata } from "next";
import { notFound } from "next/navigation";
import { getBlogPostBySlug, getBlogSlugs } from "@/lib/server-api";

/**
 * Static generation for all blog post slugs.
 */
export async function generateStaticParams() {
  const slugs = await getBlogSlugs();
  return slugs.map((slug) => ({ slug }));
}

/**
 * Dynamic SEO metadata.
 */
export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const post = await getBlogPostBySlug(params.slug);
  if (!post) return { title: "Post Not Found" };

  return {
    title: `${post.title} | Blog`,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      type: "article",
      publishedTime: post.created_at,
      images: post.cover_image_url ? [post.cover_image_url] : [],
      tags: post.tags,
    },
    twitter: {
      card: "summary_large_image",
      title: post.title,
      description: post.excerpt,
    },
  };
}

/**
 * ISR: Revalidate every 3 minutes.
 */
export const revalidate = 180;

export default async function BlogPostPage({
  params,
}: {
  params: { slug: string };
}) {
  const post = await getBlogPostBySlug(params.slug);

  if (!post) {
    notFound();
  }

  const formattedDate = new Date(post.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <main className="min-h-screen pt-20 pb-16" role="main" id="main-content">
      <article className="container-custom max-w-4xl" aria-labelledby="post-title">
        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="mb-8">
          <ol className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400" role="list">
            <li>
              <a href="/" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                Home
              </a>
            </li>
            <li aria-hidden="true">/</li>
            <li>
              <a href="/blog" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                Blog
              </a>
            </li>
            <li aria-hidden="true">/</li>
            <li aria-current="page" className="text-gray-900 dark:text-white font-medium truncate max-w-[200px]">
              {post.title}
            </li>
          </ol>
        </nav>

        {/* Post Header */}
        <header className="mb-10">
          {post.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4" role="list" aria-label="Post tags">
              {post.tags.map((tag) => (
                <a
                  key={tag}
                  href={`/blog?tag=${tag}`}
                  className="px-3 py-1 text-xs font-medium rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 hover:bg-primary-200 dark:hover:bg-primary-900/50 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
                  role="listitem"
                >
                  {tag}
                </a>
              ))}
            </div>
          )}

          <h1
            id="post-title"
            className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4 leading-tight"
          >
            {post.title}
          </h1>

          <p className="text-lg text-gray-600 dark:text-gray-300 mb-6">
            {post.excerpt}
          </p>

          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400 pb-6 border-b border-gray-200 dark:border-dark-border">
            <time dateTime={post.created_at} aria-label={`Published on ${formattedDate}`}>
              {formattedDate}
            </time>
            <span aria-hidden="true">&middot;</span>
            <span aria-label={`${post.reading_time} minute read`}>
              {post.reading_time} min read
            </span>
            <span aria-hidden="true">&middot;</span>
            <span aria-label={`${post.views} views`}>
              {post.views.toLocaleString()} views
            </span>
          </div>
        </header>

        {/* Cover Image */}
        {post.cover_image_url && (
          <figure className="mb-10 rounded-xl overflow-hidden border border-gray-200 dark:border-dark-border">
            <img
              src={post.cover_image_url}
              alt={`Cover image for ${post.title}`}
              className="w-full h-auto object-cover"
              loading="eager"
            />
          </figure>
        )}

        {/* Content */}
        <div
          className="prose prose-lg dark:prose-invert max-w-none
            prose-headings:scroll-mt-20
            prose-a:text-primary-600 dark:prose-a:text-primary-400
            prose-a:no-underline hover:prose-a:underline
            prose-code:before:content-none prose-code:after:content-none
            prose-code:bg-gray-100 dark:prose-code:bg-dark-surface
            prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
            prose-pre:bg-gray-900 dark:prose-pre:bg-dark-surface
            prose-pre:border prose-pre:border-gray-200 dark:prose-pre:border-dark-border
            prose-img:rounded-xl prose-img:border prose-img:border-gray-200 dark:prose-img:border-dark-border"
          dangerouslySetInnerHTML={{ __html: post.content }}
          role="article"
        />

        {/* Post Footer */}
        <footer className="mt-16 pt-8 border-t border-gray-200 dark:border-dark-border">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <a
              href="/blog"
              className="inline-flex items-center text-primary-600 dark:text-primary-400 hover:underline font-medium focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Blog
            </a>

            <div className="flex items-center gap-3" role="group" aria-label="Share this post">
              <span className="text-sm text-gray-500 dark:text-gray-400">Share:</span>
              <a
                href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(post.title)}&url=${encodeURIComponent(`${process.env.NEXT_PUBLIC_SITE_URL || ""}/blog/${post.slug}`)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-surface transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
                aria-label="Share on Twitter"
              >
                <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
              <a
                href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(`${process.env.NEXT_PUBLIC_SITE_URL || ""}/blog/${post.slug}`)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-surface transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
                aria-label="Share on LinkedIn"
              >
                <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              </a>
            </div>
          </div>
        </footer>
      </article>
    </main>
  );
}
