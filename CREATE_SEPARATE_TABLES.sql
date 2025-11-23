-- Create separate tables for z_scores, ratio_analysis, and back_test
-- Run this in Supabase SQL Editor

-- 1. Create z_scores table
CREATE TABLE IF NOT EXISTS public.z_scores (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    date_str TEXT NOT NULL,
    z_avg NUMERIC,
    avg_score NUMERIC,
    sector TEXT,
    analysis_result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, date_str)
);

-- Create index on z_scores
CREATE INDEX IF NOT EXISTS idx_z_scores_ticker_date ON public.z_scores(ticker, date_str);
CREATE INDEX IF NOT EXISTS idx_z_scores_date ON public.z_scores(date_str);

-- 2. Create ratio_analysis table
CREATE TABLE IF NOT EXISTS public.ratio_analysis (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    date_str TEXT NOT NULL,
    ratio_score NUMERIC,
    num_comparisons INTEGER,
    ratio_z_scores JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, date_str)
);

-- Create index on ratio_analysis
CREATE INDEX IF NOT EXISTS idx_ratio_analysis_ticker_date ON public.ratio_analysis(ticker, date_str);
CREATE INDEX IF NOT EXISTS idx_ratio_analysis_date ON public.ratio_analysis(date_str);

-- 3. Create back_test table
CREATE TABLE IF NOT EXISTS public.back_test (
    id BIGSERIAL PRIMARY KEY,
    date_str TEXT NOT NULL,
    backtest_results JSONB,
    ratio_analysis JSONB,
    timestamp TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date_str)
);

-- Create index on back_test
CREATE INDEX IF NOT EXISTS idx_back_test_date ON public.back_test(date_str);

-- 4. Create ratio_analysis_summary table (for the summary data)
CREATE TABLE IF NOT EXISTS public.ratio_analysis_summary (
    id BIGSERIAL PRIMARY KEY,
    date_str TEXT NOT NULL,
    ratio_analysis JSONB,
    timestamp TEXT,
    total_stocks INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date_str)
);

-- Create index on ratio_analysis_summary
CREATE INDEX IF NOT EXISTS idx_ratio_analysis_summary_date ON public.ratio_analysis_summary(date_str);

-- 5. Enable Row Level Security (RLS) - Allow all operations for now
ALTER TABLE public.z_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ratio_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.back_test ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ratio_analysis_summary ENABLE ROW LEVEL SECURITY;

-- 6. Create policies to allow all operations (adjust as needed for security)
CREATE POLICY "Allow all operations on z_scores" ON public.z_scores
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on ratio_analysis" ON public.ratio_analysis
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on back_test" ON public.back_test
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on ratio_analysis_summary" ON public.ratio_analysis_summary
    FOR ALL USING (true) WITH CHECK (true);

-- 7. Create updated_at trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 8. Create triggers for updated_at
DROP TRIGGER IF EXISTS update_z_scores_updated_at ON public.z_scores;
CREATE TRIGGER update_z_scores_updated_at
    BEFORE UPDATE ON public.z_scores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ratio_analysis_updated_at ON public.ratio_analysis;
CREATE TRIGGER update_ratio_analysis_updated_at
    BEFORE UPDATE ON public.ratio_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_back_test_updated_at ON public.back_test;
CREATE TRIGGER update_back_test_updated_at
    BEFORE UPDATE ON public.back_test
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ratio_analysis_summary_updated_at ON public.ratio_analysis_summary;
CREATE TRIGGER update_ratio_analysis_summary_updated_at
    BEFORE UPDATE ON public.ratio_analysis_summary
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verify tables were created
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public' 
    AND table_name IN ('z_scores', 'ratio_analysis', 'back_test', 'ratio_analysis_summary')
ORDER BY table_name, ordinal_position;

