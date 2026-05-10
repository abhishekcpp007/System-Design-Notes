/**
 * Auto-generated TypeScript API Client
 * 
 * Generated from OpenAPI schema with full type safety.
 * Includes React Query hooks for data fetching with:
 * - Automatic caching and background refetching
 * - Optimistic updates
 * - Infinite scroll pagination
 * - Mutation hooks with cache invalidation
 * 
 * Usage:
 *   import { useProjects, useCreateProject } from '@/lib/api-client';
 *   
 *   function ProjectList() {
 *     const { data, isLoading } = useProjects({ featured: true });
 *     const createProject = useCreateProject();
 *     ...
 *   }
 */

import {
  useQuery,
  useMutation,
  useInfiniteQuery,
  useQueryClient,
  QueryClient,
  QueryKey,
  UseQueryOptions,
  UseMutationOptions,
  UseInfiniteQueryOptions,
} from '@tanstack/react-query';
import axios, { AxiosError, AxiosRequestConfig } from 'axios';

// ─── Base API Configuration ────────────────────────────────────────────────

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Request interceptor — attach auth token
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Response interceptor — handle 401 with token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const { data } = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {}, {
          withCredentials: true,
        });
        localStorage.setItem('access_token', data.access_token);
        originalRequest.headers = {
          ...originalRequest.headers,
          Authorization: `Bearer ${data.access_token}`,
        };
        return apiClient(originalRequest);
      } catch {
        localStorage.removeItem('access_token');
        if (typeof window !== 'undefined') {
          window.location.href = '/auth/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ─── Types (from OpenAPI schema) ───────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string;
  avatar_url: string | null;
  role: 'user' | 'admin';
  created_at: string;
}

export interface Project {
  id: number;
  title: string;
  slug: string;
  description: string;
  long_description: string | null;
  tech_stack: string[];
  github_url: string | null;
  live_url: string | null;
  thumbnail_url: string | null;
  category: string | null;
  featured: boolean;
  published: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface BlogPost {
  id: number;
  title: string;
  slug: string;
  content: string;
  excerpt: string | null;
  tags: string[];
  published: boolean;
  reading_time: number;
  views_count: number;
  created_at: string;
  updated_at: string;
}

export interface ContactMessage {
  id: number;
  name: string;
  email: string;
  subject: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface AnalyticsDashboard {
  total_views: number;
  unique_visitors: number;
  top_pages: { path: string; views: number }[];
  daily_stats: { date: string; views: number; visitors: number }[];
  referrers: { source: string; count: number }[];
  devices: { type: string; count: number }[];
  bounce_rate: number;
}

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
}

export interface FeatureFlag {
  name: string;
  description: string;
  enabled: boolean;
  percentage: number | null;
  target_users: number[];
  target_roles: string[];
  created_at: string;
}

// Pagination types
export interface CursorPage<T> {
  items: T[];
  next_cursor: string | null;
  prev_cursor: string | null;
  has_next: boolean;
  has_prev: boolean;
  total: number | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
}

// Request types
export interface ProjectCreateRequest {
  title: string;
  description: string;
  long_description?: string;
  tech_stack: string[];
  github_url?: string;
  live_url?: string;
  thumbnail_url?: string;
  category?: string;
  featured?: boolean;
  published?: boolean;
}

export interface BlogPostCreateRequest {
  title: string;
  content: string;
  excerpt?: string;
  tags?: string[];
  published?: boolean;
}

export interface ContactSubmitRequest {
  name: string;
  email: string;
  subject: string;
  message: string;
  website?: string; // Honeypot
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

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

// ─── Query Keys (centralized for cache management) ─────────────────────────

export const queryKeys = {
  projects: {
    all: ['projects'] as const,
    list: (params?: Record<string, unknown>) => ['projects', 'list', params] as const,
    detail: (slug: string) => ['projects', 'detail', slug] as const,
    infinite: (params?: Record<string, unknown>) => ['projects', 'infinite', params] as const,
  },
  blog: {
    all: ['blog'] as const,
    list: (params?: Record<string, unknown>) => ['blog', 'list', params] as const,
    detail: (slug: string) => ['blog', 'detail', slug] as const,
    tags: ['blog', 'tags'] as const,
    infinite: (params?: Record<string, unknown>) => ['blog', 'infinite', params] as const,
  },
  contact: {
    all: ['contact'] as const,
    list: (params?: Record<string, unknown>) => ['contact', 'list', params] as const,
  },
  analytics: {
    dashboard: ['analytics', 'dashboard'] as const,
  },
  github: {
    repos: ['github', 'repos'] as const,
    languages: ['github', 'languages'] as const,
    profile: ['github', 'profile'] as const,
  },
  user: {
    me: ['user', 'me'] as const,
  },
  featureFlags: {
    all: ['featureFlags'] as const,
    evaluate: ['featureFlags', 'evaluate'] as const,
  },
  search: {
    results: (query: string) => ['search', query] as const,
    autocomplete: (query: string) => ['search', 'autocomplete', query] as const,
  },
} as const;

// ─── API Functions ─────────────────────────────────────────────────────────

const api = {
  // Auth
  login: (data: LoginRequest) =>
    apiClient.post<AuthTokens>('/api/v1/auth/login', data),
  signup: (data: SignupRequest) =>
    apiClient.post<AuthTokens>('/api/v1/auth/signup', data),
  getMe: () =>
    apiClient.get<User>('/api/v1/auth/me'),
  updateMe: (data: Partial<User>) =>
    apiClient.patch<User>('/api/v1/auth/me', data),

  // Projects
  getProjects: (params?: { cursor?: string; limit?: number; category?: string; featured?: boolean }) =>
    apiClient.get<CursorPage<Project>>('/api/v1/projects', { params }),
  getProject: (slug: string) =>
    apiClient.get<Project>(`/api/v1/projects/${slug}`),
  createProject: (data: ProjectCreateRequest, idempotencyKey?: string) =>
    apiClient.post<Project>('/api/v1/projects', data, {
      headers: idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {},
    }),
  updateProject: (id: number, data: Partial<ProjectCreateRequest>) =>
    apiClient.put<Project>(`/api/v1/projects/${id}`, data),
  deleteProject: (id: number) =>
    apiClient.delete(`/api/v1/projects/${id}`),

  // Blog
  getBlogPosts: (params?: { cursor?: string; limit?: number; tag?: string; search?: string }) =>
    apiClient.get<CursorPage<BlogPost>>('/api/v1/blog', { params }),
  getBlogPost: (slug: string) =>
    apiClient.get<BlogPost>(`/api/v1/blog/${slug}`),
  createBlogPost: (data: BlogPostCreateRequest, idempotencyKey?: string) =>
    apiClient.post<BlogPost>('/api/v1/blog', data, {
      headers: idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {},
    }),
  updateBlogPost: (id: number, data: Partial<BlogPostCreateRequest>) =>
    apiClient.put<BlogPost>(`/api/v1/blog/${id}`, data),
  deleteBlogPost: (id: number) =>
    apiClient.delete(`/api/v1/blog/${id}`),
  getBlogTags: () =>
    apiClient.get<{ tags: string[] }>('/api/v1/blog/tags'),

  // Contact
  submitContact: (data: ContactSubmitRequest, idempotencyKey?: string) =>
    apiClient.post('/api/v1/contact', data, {
      headers: idempotencyKey ? { 'X-Idempotency-Key': idempotencyKey } : {},
    }),
  getContacts: (params?: { page?: number; limit?: number }) =>
    apiClient.get<PaginatedResponse<ContactMessage>>('/api/v1/contact', { params }),

  // Analytics
  getAnalyticsDashboard: () =>
    apiClient.get<AnalyticsDashboard>('/api/v1/analytics/dashboard'),
  recordPageView: (path: string) =>
    apiClient.post('/api/v1/analytics/pageview', { path }),

  // GitHub
  getGitHubRepos: () =>
    apiClient.get<GitHubRepo[]>('/api/v1/github/repos'),
  getGitHubLanguages: () =>
    apiClient.get<Record<string, number>>('/api/v1/github/languages'),
  getGitHubProfile: () =>
    apiClient.get('/api/v1/github/profile'),

  // Search
  search: (params: { q: string; type?: string; limit?: number }) =>
    apiClient.get('/api/v1/search', { params }),
  autocomplete: (q: string) =>
    apiClient.get('/api/v1/search/autocomplete', { params: { q } }),

  // Feature Flags
  getFeatureFlags: () =>
    apiClient.get<Record<string, boolean>>('/api/v1/feature-flags/evaluate'),
  getAdminFlags: () =>
    apiClient.get<FeatureFlag[]>('/api/v1/feature-flags'),
  createFlag: (data: Partial<FeatureFlag>) =>
    apiClient.post<FeatureFlag>('/api/v1/feature-flags', data),
  updateFlag: (name: string, data: Partial<FeatureFlag>) =>
    apiClient.patch<FeatureFlag>(`/api/v1/feature-flags/${name}`, data),
  deleteFlag: (name: string) =>
    apiClient.delete(`/api/v1/feature-flags/${name}`),
};

// ─── React Query Hooks ─────────────────────────────────────────────────────

// --- Projects ---

export function useProjects(params?: { category?: string; featured?: boolean; limit?: number }) {
  return useInfiniteQuery({
    queryKey: queryKeys.projects.infinite(params),
    queryFn: async ({ pageParam }) => {
      const { data } = await api.getProjects({ ...params, cursor: pageParam });
      return data;
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    getPreviousPageParam: (firstPage) => firstPage.prev_cursor ?? undefined,
  });
}

export function useProject(slug: string) {
  return useQuery({
    queryKey: queryKeys.projects.detail(slug),
    queryFn: async () => {
      const { data } = await api.getProject(slug);
      return data;
    },
    enabled: !!slug,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreateRequest) =>
      api.createProject(data, crypto.randomUUID()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ProjectCreateRequest> }) =>
      api.updateProject(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
}

// --- Blog ---

export function useBlogPosts(params?: { tag?: string; search?: string; limit?: number }) {
  return useInfiniteQuery({
    queryKey: queryKeys.blog.infinite(params),
    queryFn: async ({ pageParam }) => {
      const { data } = await api.getBlogPosts({ ...params, cursor: pageParam });
      return data;
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  });
}

export function useBlogPost(slug: string) {
  return useQuery({
    queryKey: queryKeys.blog.detail(slug),
    queryFn: async () => {
      const { data } = await api.getBlogPost(slug);
      return data;
    },
    enabled: !!slug,
  });
}

export function useCreateBlogPost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BlogPostCreateRequest) =>
      api.createBlogPost(data, crypto.randomUUID()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.blog.all });
    },
  });
}

export function useUpdateBlogPost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<BlogPostCreateRequest> }) =>
      api.updateBlogPost(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.blog.all });
    },
  });
}

export function useDeleteBlogPost() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteBlogPost(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.blog.all });
    },
  });
}

export function useBlogTags() {
  return useQuery({
    queryKey: queryKeys.blog.tags,
    queryFn: async () => {
      const { data } = await api.getBlogTags();
      return data.tags;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// --- Search ---

export function useSearch(query: string, type?: string) {
  return useQuery({
    queryKey: queryKeys.search.results(query),
    queryFn: async () => {
      const { data } = await api.search({ q: query, type });
      return data;
    },
    enabled: query.length >= 2,
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useAutocomplete(query: string) {
  return useQuery({
    queryKey: queryKeys.search.autocomplete(query),
    queryFn: async () => {
      const { data } = await api.autocomplete(query);
      return data;
    },
    enabled: query.length >= 1,
    staleTime: 60 * 1000, // 1 minute
  });
}

// --- Auth ---

export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.user.me,
    queryFn: async () => {
      const { data } = await api.getMe();
      return data;
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: LoginRequest) => api.login(data),
    onSuccess: ({ data }) => {
      localStorage.setItem('access_token', data.access_token);
      queryClient.invalidateQueries({ queryKey: queryKeys.user.me });
    },
  });
}

export function useSignup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SignupRequest) => api.signup(data),
    onSuccess: ({ data }) => {
      localStorage.setItem('access_token', data.access_token);
      queryClient.invalidateQueries({ queryKey: queryKeys.user.me });
    },
  });
}

// --- Contact ---

export function useSubmitContact() {
  return useMutation({
    mutationFn: (data: ContactSubmitRequest) =>
      api.submitContact(data, crypto.randomUUID()),
  });
}

// --- Analytics ---

export function useAnalyticsDashboard() {
  return useQuery({
    queryKey: queryKeys.analytics.dashboard,
    queryFn: async () => {
      const { data } = await api.getAnalyticsDashboard();
      return data;
    },
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });
}

// --- GitHub ---

export function useGitHubRepos() {
  return useQuery({
    queryKey: queryKeys.github.repos,
    queryFn: async () => {
      const { data } = await api.getGitHubRepos();
      return data;
    },
    staleTime: 30 * 60 * 1000, // 30 minutes (GitHub data changes infrequently)
  });
}

export function useGitHubLanguages() {
  return useQuery({
    queryKey: queryKeys.github.languages,
    queryFn: async () => {
      const { data } = await api.getGitHubLanguages();
      return data;
    },
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}

// --- Feature Flags ---

export function useFeatureFlags() {
  return useQuery({
    queryKey: queryKeys.featureFlags.evaluate,
    queryFn: async () => {
      const { data } = await api.getFeatureFlags();
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useFeatureFlag(flagName: string): boolean {
  const { data } = useFeatureFlags();
  return data?.[flagName] ?? false;
}

// ─── Query Client Configuration ────────────────────────────────────────────

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minute default
        gcTime: 5 * 60 * 1000, // 5 minutes garbage collection
        retry: (failureCount, error) => {
          // Don't retry on 4xx errors
          if (error instanceof AxiosError && error.response?.status) {
            if (error.response.status >= 400 && error.response.status < 500) {
              return false;
            }
          }
          return failureCount < 3;
        },
        refetchOnWindowFocus: true,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

export { api, apiClient };
