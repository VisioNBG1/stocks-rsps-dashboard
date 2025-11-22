-- Create checkpoints table for RSPS Stocks Dashboard
-- Copy and paste this entire file into Supabase SQL Editor

-- Create checkpoints table
CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    data JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    stage TEXT,
    is_partial BOOLEAN DEFAULT false
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_checkpoints_id ON checkpoints(id);

-- Grant access (if needed)
ALTER TABLE checkpoints ENABLE ROW LEVEL SECURITY;

-- Verify table was created
SELECT * FROM checkpoints LIMIT 1;

