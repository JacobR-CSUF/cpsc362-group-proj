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

// Post types
export interface Post {
  id: string;
  user_id: string;
  content: string;
  media_url?: string;
  created_at: string;
  updated_at: string;
  likes_count: number;
  comments_count: number;
  user?: User;
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
