/** Shared TypeScript types for the frontend */

// ─── Auth ─────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  bio?: string;
  is_admin: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  full_name: string;
}

// ─── Projects ─────────────────────────────────────────────────
export interface Project {
  id: string;
  title: string;
  slug: string;
  description: string;
  long_description?: string;
  tech_stack: string[];
  image_url?: string;
  live_url?: string;
  github_url?: string;
  featured: boolean;
  status: "completed" | "in_progress" | "planned";
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  title: string;
  description: string;
  long_description?: string;
  tech_stack: string[];
  image_url?: string;
  live_url?: string;
  github_url?: string;
  featured?: boolean;
  status?: "completed" | "in_progress" | "planned";
}

// ─── Blog ─────────────────────────────────────────────────────
export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  cover_image?: string;
  tags: string[];
  published: boolean;
  reading_time: number;
  views: number;
  created_at: string;
  updated_at: string;
  author: {
    full_name: string;
    avatar_url?: string;
  };
}

export interface BlogPostCreate {
  title: string;
  excerpt: string;
  content: string;
  cover_image?: string;
  tags: string[];
  published?: boolean;
}

// ─── Contact ──────────────────────────────────────────────────
export interface ContactMessage {
  id: string;
  name: string;
  email: string;
  subject: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface ContactSubmit {
  name: string;
  email: string;
  subject: string;
  message: string;
  honeypot?: string; // Bot detection field
}

// ─── Analytics ────────────────────────────────────────────────
export interface AnalyticsDashboard {
  period_days: number;
  total_views: number;
  unique_visitors: number;
  avg_views_per_day: number;
  daily_views: { date: string; views: number; visitors: number }[];
  top_pages: { path: string; views: number; unique_views: number }[];
  top_referrers: { referrer: string; count: number }[];
  devices: Record<string, number>;
  bounce_rate: number;
}

// ─── GitHub ───────────────────────────────────────────────────
export interface GitHubRepo {
  name: string;
  description: string;
  url: string;
  homepage: string;
  language: string;
  stars: number;
  forks: number;
  topics: string[];
  updated_at: string;
  created_at: string;
}

export interface GitHubProfile {
  username: string;
  name: string;
  bio: string;
  avatar_url: string;
  public_repos: number;
  followers: number;
  following: number;
}

// ─── Pagination ───────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// ─── Navigation ───────────────────────────────────────────────
export interface NavItem {
  label: string;
  href: string;
  icon?: string;
}
