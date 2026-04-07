-- Migration 001: Initial schema with MULTIMODAL RAG support
-- Run this on your Supabase project SQL editor

-- Run the complete schema
\i schema.sql

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_knowledge_updated_at BEFORE UPDATE ON student_knowledge
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_multimodal_resources_updated_at BEFORE UPDATE ON multimodal_resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
