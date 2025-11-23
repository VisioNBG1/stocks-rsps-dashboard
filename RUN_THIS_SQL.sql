-- Copy and paste this entire file into Supabase SQL Editor
-- URL: https://fzuxkphassgtvfiupixv.supabase.co
-- Then click "SQL Editor" → Paste → Click "Run"

-- Create stock_data table
CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    date_str VARCHAR(10) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ticker, stage, date_str)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_stock_data_lookup ON stock_data(ticker, stage, date_str);
CREATE INDEX IF NOT EXISTS idx_stock_data_date ON stock_data(date_str);

-- Enable Row Level Security
ALTER TABLE stock_data ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations
DROP POLICY IF EXISTS "Allow all operations on stock_data" ON stock_data;
CREATE POLICY "Allow all operations on stock_data" ON stock_data
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Create function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger
DROP TRIGGER IF EXISTS update_stock_data_updated_at ON stock_data;
CREATE TRIGGER update_stock_data_updated_at
    BEFORE UPDATE ON stock_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Clear old checkpoints to start fresh
-- DELETE FROM checkpoints;

