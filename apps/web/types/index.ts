// User types
export interface User {
  id: string;
  email: string;
  username: string;
  created_at: string;
  profile_pic?: string | null;
}

// Auth types
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  username: string;
}

// Post Author (nested in Post)
export interface PostAuthor {
  user_id: string;
  username: string;
  profile_pic: string | null;
}

// Post Media (nested in Post)
export interface PostMedia {
  id: string;
  public_url: string;
  media_type: 'image' | 'video' | null;
  caption: string | null;
}

// Post types
export interface Post {
  id: string;
  user_id: string;
  caption: string;
  media_id: string | null;
  has_media: boolean;
  visibility: string;
  created_at: string;
  author: PostAuthor;
  media: PostMedia | null;
  likes_count?: number;
  comments_count?: number;
}

// Comment types
export interface Comment {
  id: string;
  post_id: string;
  user_id: string;
  content: string;
  created_at: string;
  user?: User;
}

// API Error types
export interface APIError {
  detail: string;
  status?: number;
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}