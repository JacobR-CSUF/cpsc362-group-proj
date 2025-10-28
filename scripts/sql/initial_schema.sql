CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

Table users {
  id uuid [primary key, default: `uuid_generate_v4()`]
  username varchar [unique, not null]
  email varchar [unique, not null]
  profile_pic varchar
  created_at timestamp [default: `now()`]
}

Table follows {
  following_user_id uuid [not null]
  followed_user_id uuid [not null]
  created_at timestamp [default: `now()`]
  
  indexes {
    (following_user_id, followed_user_id) [pk]
  }
}

Table media {
  id uuid [primary key, default: `uuid_generate_v4()`]
  user_id uuid [not null]
  url varchar [not null, note: 'Path to image or video file']
  type varchar [note: 'photo | video']
  description text
  created_at timestamp [default: `now()`]
}

Table posts {
  id uuid [primary key, default: `uuid_generate_v4()`]
  user_id uuid [not null]
  media_id uuid [note: 'Optional associated media']
  caption text
  visibility varchar [note: 'public | private | followers']
  created_at timestamp [default: `now()`]
}

Table friend_suggestions {
  id uuid [primary key, default: `uuid_generate_v4()`]
  user_id uuid [not null, note: 'The user receiving the suggestion']
  suggested_user_id uuid [not null, note: 'The potential friend']
  match_score float [note: '0-1 confidence of friendship likelihood']
  reason varchar [note: 'e.g., Nearby, mutual follows, shared interests']
  created_at timestamp [default: `now()`]
}

Table comments {
  id uuid [primary key, default: `uuid_generate_v4()`]
  post_id uuid [not null]
  user_id uuid [not null]
  content text
  created_at timestamp [default: `now()`]
}

Table likes {
  id uuid [primary key, default: `uuid_generate_v4()`, note: 'Optional but included']
  post_id uuid [not null]
  user_id uuid [not null]
  created_at timestamp [default: `now()`]
  
  indexes {
    (post_id, user_id) [unique]
  }
}

Table messages {
  id uuid [primary key, default: `uuid_generate_v4()`]
  sender_id uuid [not null]
  recipient_id uuid [not null]
  content text
  created_at timestamp [default: `now()`]
}

// Relationships
Ref: likes.post_id > posts.id [delete: cascade]
Ref: likes.user_id > users.id [delete: cascade]
Ref: comments.post_id > posts.id [delete: cascade]
Ref: comments.user_id > users.id [delete: cascade]
Ref: follows.following_user_id > users.id [delete: cascade]
Ref: follows.followed_user_id > users.id [delete: cascade]
Ref: media.user_id > users.id [delete: cascade]
Ref: posts.user_id > users.id [delete: cascade]
Ref: posts.media_id > media.id [delete: set null]
Ref: friend_suggestions.user_id > users.id [delete: cascade]
Ref: friend_suggestions.suggested_user_id > users.id [delete: cascade]
Ref: messages.sender_id > users.id [delete: cascade]
Ref: messages.recipient_id > users.id [delete: cascade]