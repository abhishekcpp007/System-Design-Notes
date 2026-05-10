/**
 * Optimistic UI Updates with Zustand
 * 
 * Implements the optimistic update pattern:
 * 1. Immediately update UI (assume success)
 * 2. Send request to server in background
 * 3. On failure → rollback to previous state + show error
 * 
 * This eliminates perceived latency for mutations, making the app
 * feel instant while maintaining data consistency.
 * 
 * Pattern used by: Twitter, Linear, Notion, Figma
 */

import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { api, Project, BlogPost, ContactMessage } from './api-client';
import toast from 'react-hot-toast';

// ─── Types ─────────────────────────────────────────────────────────────────

interface OptimisticOperation {
  id: string;
  type: 'create' | 'update' | 'delete';
  entity: string;
  timestamp: number;
  rollbackData: unknown;
  status: 'pending' | 'confirmed' | 'failed';
}

interface ProjectsState {
  items: Project[];
  isLoading: boolean;
  error: string | null;
}

interface BlogState {
  items: BlogPost[];
  isLoading: boolean;
  error: string | null;
}

interface AppState {
  projects: ProjectsState;
  blog: BlogState;
  operations: OptimisticOperation[];
  
  // Project actions
  setProjects: (projects: Project[]) => void;
  optimisticCreateProject: (data: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  optimisticUpdateProject: (id: number, data: Partial<Project>) => Promise<void>;
  optimisticDeleteProject: (id: number) => Promise<void>;
  optimisticReorderProjects: (orderedIds: number[]) => Promise<void>;
  
  // Blog actions
  setBlogPosts: (posts: BlogPost[]) => void;
  optimisticCreatePost: (data: Omit<BlogPost, 'id' | 'created_at' | 'updated_at' | 'views_count'>) => Promise<void>;
  optimisticUpdatePost: (id: number, data: Partial<BlogPost>) => Promise<void>;
  optimisticDeletePost: (id: number) => Promise<void>;
  
  // Operation tracking
  getPendingOperations: () => OptimisticOperation[];
  clearConfirmedOperations: () => void;
}

// ─── Helper: Generate temporary ID for optimistic creates ──────────────────

let tempIdCounter = -1;
function getTempId(): number {
  return tempIdCounter--;
}

function generateOperationId(): string {
  return `op_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

// ─── Store ─────────────────────────────────────────────────────────────────

export const useOptimisticStore = create<AppState>()(
  immer((set, get) => ({
    projects: { items: [], isLoading: false, error: null },
    blog: { items: [], isLoading: false, error: null },
    operations: [],

    // ─── Projects ────────────────────────────────────────────────────

    setProjects: (projects) => {
      set((state) => {
        state.projects.items = projects;
        state.projects.isLoading = false;
      });
    },

    optimisticCreateProject: async (data) => {
      const opId = generateOperationId();
      const tempId = getTempId();
      const now = new Date().toISOString();

      // Optimistic: add to state immediately
      const optimisticProject: Project = {
        ...data,
        id: tempId,
        created_at: now,
        updated_at: now,
      } as Project;

      set((state) => {
        state.projects.items.unshift(optimisticProject);
        state.operations.push({
          id: opId,
          type: 'create',
          entity: 'project',
          timestamp: Date.now(),
          rollbackData: null,
          status: 'pending',
        });
      });

      try {
        const { data: created } = await api.createProject(
          {
            title: data.title,
            description: data.description,
            long_description: data.long_description || undefined,
            tech_stack: data.tech_stack,
            github_url: data.github_url || undefined,
            live_url: data.live_url || undefined,
            thumbnail_url: data.thumbnail_url || undefined,
            category: data.category || undefined,
            featured: data.featured,
            published: data.published,
          },
          crypto.randomUUID()
        );

        // Replace temp item with real one
        set((state) => {
          const idx = state.projects.items.findIndex((p) => p.id === tempId);
          if (idx !== -1) {
            state.projects.items[idx] = created;
          }
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'confirmed';
        });

        toast.success('Project created');
      } catch (error) {
        // Rollback: remove the optimistic item
        set((state) => {
          state.projects.items = state.projects.items.filter((p) => p.id !== tempId);
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'failed';
        });

        toast.error('Failed to create project');
        throw error;
      }
    },

    optimisticUpdateProject: async (id, data) => {
      const opId = generateOperationId();
      const currentItems = get().projects.items;
      const originalProject = currentItems.find((p) => p.id === id);

      if (!originalProject) return;

      // Optimistic: update immediately
      set((state) => {
        const idx = state.projects.items.findIndex((p) => p.id === id);
        if (idx !== -1) {
          Object.assign(state.projects.items[idx], data, {
            updated_at: new Date().toISOString(),
          });
        }
        state.operations.push({
          id: opId,
          type: 'update',
          entity: 'project',
          timestamp: Date.now(),
          rollbackData: { ...originalProject },
          status: 'pending',
        });
      });

      try {
        const { data: updated } = await api.updateProject(id, data);

        set((state) => {
          const idx = state.projects.items.findIndex((p) => p.id === id);
          if (idx !== -1) {
            state.projects.items[idx] = updated;
          }
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'confirmed';
        });

        toast.success('Project updated');
      } catch (error) {
        // Rollback to original
        set((state) => {
          const idx = state.projects.items.findIndex((p) => p.id === id);
          if (idx !== -1 && originalProject) {
            state.projects.items[idx] = originalProject;
          }
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'failed';
        });

        toast.error('Failed to update project');
        throw error;
      }
    },

    optimisticDeleteProject: async (id) => {
      const opId = generateOperationId();
      const currentItems = get().projects.items;
      const deletedProject = currentItems.find((p) => p.id === id);
      const deletedIndex = currentItems.findIndex((p) => p.id === id);

      if (!deletedProject) return;

      // Optimistic: remove immediately
      set((state) => {
        state.projects.items = state.projects.items.filter((p) => p.id !== id);
        state.operations.push({
          id: opId,
          type: 'delete',
          entity: 'project',
          timestamp: Date.now(),
          rollbackData: { project: deletedProject, index: deletedIndex },
          status: 'pending',
        });
      });

      try {
        await api.deleteProject(id);

        set((state) => {
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'confirmed';
        });

        toast.success('Project deleted');
      } catch (error) {
        // Rollback: re-insert at original position
        set((state) => {
          state.projects.items.splice(deletedIndex, 0, deletedProject);
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'failed';
        });

        toast.error('Failed to delete project');
        throw error;
      }
    },

    optimisticReorderProjects: async (orderedIds) => {
      const opId = generateOperationId();
      const originalItems = [...get().projects.items];

      // Optimistic: reorder immediately
      set((state) => {
        const itemMap = new Map(state.projects.items.map((p) => [p.id, p]));
        state.projects.items = orderedIds
          .map((id) => itemMap.get(id))
          .filter(Boolean) as Project[];
        state.operations.push({
          id: opId,
          type: 'update',
          entity: 'project',
          timestamp: Date.now(),
          rollbackData: originalItems,
          status: 'pending',
        });
      });

      try {
        await api.updateProject(0, {}); // TODO: Use reorder endpoint
        set((state) => {
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'confirmed';
        });
      } catch (error) {
        // Rollback
        set((state) => {
          state.projects.items = originalItems;
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'failed';
        });
        toast.error('Failed to reorder');
        throw error;
      }
    },

    // ─── Blog ────────────────────────────────────────────────────────

    setBlogPosts: (posts) => {
      set((state) => {
        state.blog.items = posts;
        state.blog.isLoading = false;
      });
    },

    optimisticCreatePost: async (data) => {
      const opId = generateOperationId();
      const tempId = getTempId();
      const now = new Date().toISOString();

      const optimisticPost: BlogPost = {
        ...data,
        id: tempId,
        views_count: 0,
        created_at: now,
        updated_at: now,
      } as BlogPost;

      set((state) => {
        state.blog.items.unshift(optimisticPost);
        state.operations.push({
          id: opId,
          type: 'create',
          entity: 'blog',
          timestamp: Date.now(),
          rollbackData: null,
          status: 'pending',
        });
      });

      try {
        const { data: created } = await api.createBlogPost(
          {
            title: data.title,
            content: data.content,
            excerpt: data.excerpt || undefined,
            tags: data.tags,
            published: data.published,
          },
          crypto.randomUUID()
        );

        set((state) => {
          const idx = state.blog.items.findIndex((p) => p.id === tempId);
          if (idx !== -1) {
            state.blog.items[idx] = created;
          }
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'confirmed';
        });

        toast.success('Post created');
      } catch (error) {
        set((state) => {
          state.blog.items = state.blog.items.filter((p) => p.id !== tempId);
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'failed';
        });

        toast.error('Failed to create post');
        throw error;
      }
    },

    optimisticUpdatePost: async (id, data) => {
      const opId = generateOperationId();
      const currentItems = get().blog.items;
      const originalPost = currentItems.find((p) => p.id === id);

      if (!originalPost) return;

      set((state) => {
        const idx = state.blog.items.findIndex((p) => p.id === id);
        if (idx !== -1) {
          Object.assign(state.blog.items[idx], data, {
            updated_at: new Date().toISOString(),
          });
        }
        state.operations.push({
          id: opId,
          type: 'update',
          entity: 'blog',
          timestamp: Date.now(),
          rollbackData: { ...originalPost },
          status: 'pending',
        });
      });

      try {
        const { data: updated } = await api.updateBlogPost(id, data);
        set((state) => {
          const idx = state.blog.items.findIndex((p) => p.id === id);
          if (idx !== -1) {
            state.blog.items[idx] = updated;
          }
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'confirmed';
        });
        toast.success('Post updated');
      } catch (error) {
        set((state) => {
          const idx = state.blog.items.findIndex((p) => p.id === id);
          if (idx !== -1 && originalPost) {
            state.blog.items[idx] = originalPost;
          }
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'failed';
        });
        toast.error('Failed to update post');
        throw error;
      }
    },

    optimisticDeletePost: async (id) => {
      const opId = generateOperationId();
      const currentItems = get().blog.items;
      const deletedPost = currentItems.find((p) => p.id === id);
      const deletedIndex = currentItems.findIndex((p) => p.id === id);

      if (!deletedPost) return;

      set((state) => {
        state.blog.items = state.blog.items.filter((p) => p.id !== id);
        state.operations.push({
          id: opId,
          type: 'delete',
          entity: 'blog',
          timestamp: Date.now(),
          rollbackData: { post: deletedPost, index: deletedIndex },
          status: 'pending',
        });
      });

      try {
        await api.deleteBlogPost(id);
        set((state) => {
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'confirmed';
        });
        toast.success('Post deleted');
      } catch (error) {
        set((state) => {
          state.blog.items.splice(deletedIndex, 0, deletedPost);
          const op = state.operations.find((o) => o.id === opId);
          if (op) op.status = 'failed';
        });
        toast.error('Failed to delete post');
        throw error;
      }
    },

    // ─── Operations ──────────────────────────────────────────────────

    getPendingOperations: () => {
      return get().operations.filter((op) => op.status === 'pending');
    },

    clearConfirmedOperations: () => {
      set((state) => {
        state.operations = state.operations.filter((op) => op.status === 'pending');
      });
    },
  }))
);
