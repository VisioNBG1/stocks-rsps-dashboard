-- New Supabase table structure for storing stock data per stage
-- Run this in your Supabase SQL Editor

-- 1. Create stock_data table to store actual stock data per stage
CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    stage VARCHAR(50) NOT NULL, -- 'downloaded', 'z_scored', 'ratio_analyzed', 'backtested'
    date_str VARCHAR(10) NOT NULL, -- 'YYYY-MM-DD' format
    data JSONB NOT NULL, -- The actual stock data (DataFrame serialized as JSON)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ticker, stage, date_str)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_stock_data_lookup ON stock_data(ticker, stage, date_str);
CREATE INDEX IF NOT EXISTS idx_stock_data_date ON stock_data(date_str);

-- 2. Clear existing checkpoints table (optional - uncomment if you want to start fresh)
-- DELETE FROM checkpoints;

-- 3. Enable Row Level Security (RLS) - allow all operations for now
ALTER TABLE stock_data ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust as needed for security)
CREATE POLICY "Allow all operations on stock_data" ON stock_data
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- 4. Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_stock_data_updated_at ON stock_data;
CREATE TRIGGER update_stock_data_updated_at
    BEFORE UPDATE ON stock_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

