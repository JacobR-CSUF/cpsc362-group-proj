-- =====================================================
-- Row Level Security (RLS) Setup
-- =====================================================
-- Complete RLS implementation for all database tables
-- Run this in your Supabase SQL Editor
-- NOTE: Ensure base privileges for the "authenticated" role exist; Supabase usually
-- seeds these, but if you see "permission denied for schema public", run the GRANTs
-- below before (re)applying policies.
--
-- Base privileges (safe to re-run):
--   GRANT USAGE ON SCHEMA public TO authenticated;
--   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
--   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
--   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;
--   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO authenticated;

-- =====================================================
-- 1. ENABLE RLS ON ALL TABLES
-- =====================================================

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.follows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.media ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.friend_suggestions ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 2. USERS TABLE
-- =====================================================

-- Anyone can view profiles (public profiles)
CREATE POLICY "Public profiles viewable"
ON public.users FOR SELECT
USING (true);

-- Users manage their own profile
CREATE POLICY "Users manage own profile"
ON public.users FOR ALL
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- =====================================================
-- 3. POSTS TABLE
-- =====================================================

-- View posts based on visibility setting
CREATE POLICY "View posts by visibility"
ON public.posts FOR SELECT
USING (
  visibility = 'public' 
  OR user_id = auth.uid()
  OR (
    visibility = 'followers' 
    AND EXISTS (
      SELECT 1 FROM public.follows 
      WHERE followed_user_id = posts.user_id 
      AND following_user_id = auth.uid()
    )
  )
);

-- Users manage their own posts
CREATE POLICY "Users manage own posts"
ON public.posts FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- 4. COMMENTS TABLE
-- =====================================================

-- View comments on posts you can see
CREATE POLICY "View comments on visible posts"
ON public.comments FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.posts 
    WHERE posts.id = comments.post_id
    AND (
      posts.visibility = 'public'
      OR posts.user_id = auth.uid()
      OR (
        posts.visibility = 'followers'
        AND EXISTS (
          SELECT 1 FROM public.follows
          WHERE followed_user_id = posts.user_id
          AND following_user_id = auth.uid()
        )
      )
    )
  )
);

-- Comment on posts you can see
CREATE POLICY "Comment on visible posts"
ON public.comments FOR INSERT
WITH CHECK (
  auth.uid() = user_id
  AND EXISTS (
    SELECT 1 FROM public.posts 
    WHERE posts.id = comments.post_id
    AND (
      posts.visibility = 'public'
      OR posts.user_id = auth.uid()
      OR (
        posts.visibility = 'followers'
        AND EXISTS (
          SELECT 1 FROM public.follows
          WHERE followed_user_id = posts.user_id
          AND following_user_id = auth.uid()
        )
      )
    )
  )
);

-- Update your own comments
CREATE POLICY "Update own comments"
ON public.comments FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Delete your own comments OR comments on your posts
CREATE POLICY "Delete own or on own posts"
ON public.comments FOR DELETE
USING (
  auth.uid() = user_id
  OR EXISTS (
    SELECT 1 FROM public.posts
    WHERE posts.id = comments.post_id
    AND posts.user_id = auth.uid()
  )
);

-- =====================================================
-- 5. LIKES TABLE
-- =====================================================

-- View likes on posts you can see
CREATE POLICY "View likes on visible posts"
ON public.likes FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.posts
    WHERE posts.id = likes.post_id
    AND (
      posts.visibility = 'public'
      OR posts.user_id = auth.uid()
      OR (
        posts.visibility = 'followers'
        AND EXISTS (
          SELECT 1 FROM public.follows
          WHERE followed_user_id = posts.user_id
          AND following_user_id = auth.uid()
        )
      )
    )
  )
);

-- Like visible posts
CREATE POLICY "Like visible posts"
ON public.likes FOR INSERT
WITH CHECK (
  auth.uid() = user_id
  AND EXISTS (
    SELECT 1 FROM public.posts
    WHERE posts.id = likes.post_id
    AND (
      posts.visibility = 'public'
      OR posts.user_id = auth.uid()
      OR (
        posts.visibility = 'followers'
        AND EXISTS (
          SELECT 1 FROM public.follows
          WHERE followed_user_id = posts.user_id
          AND following_user_id = auth.uid()
        )
      )
    )
  )
);

-- Unlike your own likes
CREATE POLICY "Unlike own likes"
ON public.likes FOR DELETE
USING (auth.uid() = user_id);

-- =====================================================
-- 6. FOLLOWS TABLE
-- =====================================================

-- Anyone can view follow relationships
CREATE POLICY "Follows are public"
ON public.follows FOR SELECT
USING (true);

-- Users manage their following list
CREATE POLICY "Manage own following"
ON public.follows FOR ALL
USING (auth.uid() = following_user_id)
WITH CHECK (auth.uid() = following_user_id);

-- =====================================================
-- 7. MESSAGES TABLE
-- =====================================================

-- View your own messages (sent or received)
CREATE POLICY "View own messages"
ON public.messages FOR SELECT
USING (auth.uid() = sender_id OR auth.uid() = recipient_id);

-- Send messages as yourself
CREATE POLICY "Send own messages"
ON public.messages FOR INSERT
WITH CHECK (auth.uid() = sender_id);

-- Manage messages you sent
CREATE POLICY "Manage sent messages"
ON public.messages FOR ALL
USING (auth.uid() = sender_id)
WITH CHECK (auth.uid() = sender_id);

-- =====================================================
-- 8. MEDIA TABLE
-- =====================================================

-- Anyone can view media (posts control visibility)
CREATE POLICY "Media is public"
ON public.media FOR SELECT
USING (true);

-- Users manage their own media
CREATE POLICY "Manage own media"
ON public.media FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- 9. FRIEND SUGGESTIONS TABLE
-- =====================================================

-- View only your own suggestions
CREATE POLICY "View own suggestions"
ON public.friend_suggestions FOR SELECT
USING (auth.uid() = user_id);

-- Only system can create suggestions
CREATE POLICY "System creates suggestions"
ON public.friend_suggestions FOR INSERT
WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- Dismiss your own suggestions
CREATE POLICY "Dismiss own suggestions"
ON public.friend_suggestions FOR DELETE
USING (auth.uid() = user_id);

-- =====================================================
-- VERIFICATION
-- =====================================================
-- Run this to verify RLS is enabled:
/*
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'posts', 'comments', 'likes', 'follows', 'messages', 'media', 'friend_suggestions');
*/
