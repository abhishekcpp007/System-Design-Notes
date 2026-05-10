/**
 * Server-side API client for Next.js Server Components.
 *
 * Uses fetch() directly (not axios) for:
 * - Next.js cache integration (ISR/revalidation)
 * - Static generation support
 * - Edge runtime compatibility
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions {
  revalidate?: number; // ISR revalidation interval in seconds
  tags?: string[]; // Cache tags for on-demand revalidation
  cache?: RequestCache;
}

async function serverFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T | null> {
  const { revalidate = 60, tags, cache } = options;

  try {
    const fetchOptions: RequestInit & { next?: { revalidate?: number; tags?: string[] } } = {
      headers: { "Content-Type": "application/json" },
      next: {},
    };

    if (cache) {
      fetchOptions.cache = cache;
    } else if (revalidate !== undefined) {
      fetchOptions.next!.revalidate = revalidate;
    }

    if (tags) {
      fetchOptions.next!.tags = tags;
    }

    const res = await fetch(`${API_URL}${endpoint}`, fetchOptions);

    if (!res.ok) return null;
    return res.json() as Promise<T>;
  } catch {
    return null;
  }
}

// ============================================================
// Typed API Functions for Server Components
// ============================================================

export interface ProjectResponse {
  id: number;
  title: string;
  slug: string;
  description: string;
  long_description?: string;
  tech_stack: string[];
  live_url?: string;
  github_url?: string;
  thumbnail_url?: string;
  category: string;
  status: string;
  featured: boolean;
  display_order: number;
  created_at: string;
}

export interface BlogResponse {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  tags: string[];
  cover_image_url?: string;
  reading_time: number;
  published: boolean;
  views: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
}

/**
 * Get all published projects with ISR (revalidates every 5 minutes).
 */
export async function getProjects(params?: {
  status?: string;
  featured?: boolean;
}): Promise<PaginatedResponse<ProjectResponse> | null> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set("status", params.status);
  if (params?.featured) searchParams.set("featured", "true");
  searchParams.set("per_page", "50");

  const query = searchParams.toString();
  return serverFetch<PaginatedResponse<ProjectResponse>>(
    `/api/v1/projects${query ? `?${query}` : ""}`,
    { revalidate: 300, tags: ["projects"] }
  );
}

/**
 * Get a single project by slug (revalidates every 5 minutes).
 */
export async function getProjectBySlug(slug: string): Promise<ProjectResponse | null> {
  return serverFetch<ProjectResponse>(`/api/v1/projects/${slug}`, {
    revalidate: 300,
    tags: ["projects", `project:${slug}`],
  });
}

/**
 * Get all project slugs for static generation.
 */
export async function getProjectSlugs(): Promise<string[]> {
  const data = await serverFetch<PaginatedResponse<ProjectResponse>>(
    "/api/v1/projects?per_page=100",
    { revalidate: 600, tags: ["projects"] }
  );
  return data?.items?.map((p) => p.slug) ?? [];
}

/**
 * Get all published blog posts with ISR (revalidates every 3 minutes).
 */
export async function getBlogPosts(params?: {
  tag?: string;
  search?: string;
  page?: number;
}): Promise<PaginatedResponse<BlogResponse> | null> {
  const searchParams = new URLSearchParams();
  if (params?.tag) searchParams.set("tag", params.tag);
  if (params?.search) searchParams.set("search", params.search);
  if (params?.page) searchParams.set("page", String(params.page));
  searchParams.set("per_page", "12");

  const query = searchParams.toString();
  return serverFetch<PaginatedResponse<BlogResponse>>(
    `/api/v1/blog${query ? `?${query}` : ""}`,
    { revalidate: 180, tags: ["blog"] }
  );
}

/**
 * Get a single blog post by slug (revalidates every 3 minutes).
 */
export async function getBlogPostBySlug(slug: string): Promise<BlogResponse | null> {
  return serverFetch<BlogResponse>(`/api/v1/blog/${slug}`, {
    revalidate: 180,
    tags: ["blog", `blog:${slug}`],
  });
}

/**
 * Get all blog post slugs for static generation.
 */
export async function getBlogSlugs(): Promise<string[]> {
  const data = await serverFetch<PaginatedResponse<BlogResponse>>(
    "/api/v1/blog?per_page=200",
    { revalidate: 600, tags: ["blog"] }
  );
  return data?.items?.map((p) => p.slug) ?? [];
}

/**
 * Get featured projects for homepage (revalidates every 10 minutes).
 */
export async function getFeaturedProjects(): Promise<ProjectResponse[]> {
  const data = await serverFetch<PaginatedResponse<ProjectResponse>>(
    "/api/v1/projects?featured=true&per_page=6",
    { revalidate: 600, tags: ["projects", "featured"] }
  );
  return data?.items ?? [];
}

/**
 * Get recent blog posts for homepage (revalidates every 5 minutes).
 */
export async function getRecentPosts(): Promise<BlogResponse[]> {
  const data = await serverFetch<PaginatedResponse<BlogResponse>>(
    "/api/v1/blog?per_page=3",
    { revalidate: 300, tags: ["blog"] }
  );
  return data?.items ?? [];
}
