-- Add update_at and delted_at
-- Add updated_at column
ALTER TABLE comments 
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add deleted_at column for soft deletes
ALTER TABLE comments 
ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

-- Create trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_comments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_update_comments_updated_at 
BEFORE UPDATE ON comments 
FOR EACH ROW 
EXECUTE FUNCTION update_comments_updated_at();

-- Verify the changes
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'comments'
ORDER BY ordinal_position;
