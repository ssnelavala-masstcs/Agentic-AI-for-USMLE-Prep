-- Supabase Database Schema for Agentic USMLE Prep System
-- MULTIMODAL RAG EDITION
-- Supports text, images, PDFs, video, and audio resource storage

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for embeddings

-- Students table
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    target_exam_date DATE,
    study_hours_per_day DECIMAL(3,1) DEFAULT 6.0,
    baseline_nbme_score INTEGER,
    baseline_uworld_percentile DECIMAL(5,2),
    learning_style VARCHAR(50),  -- 'visual', 'auditory', 'reading', 'mixed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Knowledge areas (USMLE subjects/topics)
CREATE TABLE knowledge_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    subtopics TEXT[],
    weight_in_exam DECIMAL(5,2)
);

-- Student knowledge graph
CREATE TABLE student_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    knowledge_area_id UUID REFERENCES knowledge_areas(id),
    proficiency_score DECIMAL(5,2) DEFAULT 0.0,
    last_assessed TIMESTAMP WITH TIME ZONE,
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    avg_confidence DECIMAL(3,1),
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(student_id, knowledge_area_id)
);

-- Performance logs
CREATE TABLE performance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    session_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    knowledge_area_id UUID REFERENCES knowledge_areas(id),
    topic VARCHAR(200),
    questions_attempted INTEGER,
    questions_correct INTEGER,
    avg_time_per_question_sec INTEGER,
    avg_confidence_score DECIMAL(3,1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Study plans
CREATE TABLE study_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    plan_start_date DATE NOT NULL,
    plan_end_date DATE NOT NULL,
    plan_json JSONB NOT NULL,
    generation_model VARCHAR(100),
    multimodal_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Study blocks
CREATE TABLE study_blocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    study_plan_id UUID REFERENCES study_plans(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,
    date DATE NOT NULL,
    knowledge_area_id UUID REFERENCES knowledge_areas(id),
    topic VARCHAR(200),
    recommended_duration_hours DECIMAL(3,1),
    practice_questions INTEGER,
    review_materials TEXT[],
    resource_modalities TEXT[],  -- ['text', 'image', 'video']
    completed BOOLEAN DEFAULT FALSE,
    actual_score DECIMAL(5,2),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent execution logs
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id),
    agent_name VARCHAR(100) NOT NULL,
    execution_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT
);

-- ============================================================================
-- MULTIMODAL RESOURCE DATABASE (NEW)
-- ============================================================================

-- Resource types (modalities)
CREATE TYPE resource_modality AS ENUM ('text', 'pdf', 'image', 'video', 'audio');
CREATE TYPE resource_tier AS ENUM ('essential', 'high-yield', 'supplementary', 'reference');

-- Multimodal resource catalog
CREATE TABLE multimodal_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., "fa-txt-cardio"
    name VARCHAR(255) NOT NULL,
    source VARCHAR(100) NOT NULL,  -- "First Aid", "UWorld", "Pathoma", etc.
    modality resource_modality NOT NULL,
    area VARCHAR(100) NOT NULL,
    topic VARCHAR(200) NOT NULL,
    description TEXT,
    tier resource_tier DEFAULT 'high-yield',
    
    -- Content storage (varies by modality)
    content_text TEXT,  -- Text content / transcript
    content_url TEXT,  -- URL or file path for PDFs/images/audio
    page_range VARCHAR(50),  -- e.g., "pp. 265-280"
    timestamp_range VARCHAR(50),  -- e.g., "12:30-18:45"
    
    -- Embeddings for vector similarity search
    text_embedding vector(1536),  -- OpenAI ada-002 for text
    image_embedding vector(768),  -- CLIP ViT-L/14 for images
    
    -- Image-specific metadata
    image_type VARCHAR(50),  -- 'pathology_slide', 'ECG', 'radiograph', 'diagram', 'table'
    image_description TEXT,  -- Clinical description of image
    
    -- Video-specific metadata
    video_url TEXT,
    duration_minutes DECIMAL(5,1),
    key_frames TEXT[],  -- Important timestamps with labels
    
    -- Engagement metrics
    estimated_hours DECIMAL(3,1) DEFAULT 2.0,
    student_rating DECIMAL(2,1),  -- 1-5 from prior users
    usage_count INTEGER DEFAULT 0,
    
    -- Tags
    tags TEXT[],
    img_specific BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Student resource interactions (tracking what they actually used)
CREATE TABLE student_resource_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    resource_id UUID REFERENCES multimodal_resources(id),
    interaction_type VARCHAR(50) NOT NULL,  -- 'viewed', 'completed', 'skipped', 'rated'
    duration_minutes INTEGER,  -- How long they spent
    rating DECIMAL(2,1),  -- Student's rating (1-5)
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Uploaded student documents (multimodal inputs)
CREATE TABLE student_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL,  -- 'pdf', 'image', 'text'
    file_url TEXT NOT NULL,  -- Supabase Storage URL
    file_name VARCHAR(255),
    extracted_text TEXT,  -- OCR/extracted text content
    text_embedding vector(1536),  -- Embedding for retrieval
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_student_knowledge_student ON student_knowledge(student_id);
CREATE INDEX idx_performance_logs_student ON performance_logs(student_id, session_timestamp);
CREATE INDEX idx_study_plans_student ON study_plans(student_id, plan_start_date);
CREATE INDEX idx_study_blocks_plan ON study_blocks(study_plan_id, day_number);
CREATE INDEX idx_agent_executions_student ON agent_executions(student_id, execution_timestamp);

-- Multimodal resource indexes
CREATE INDEX idx_resources_modality ON multimodal_resources(modality);
CREATE INDEX idx_resources_area ON multimodal_resources(area);
CREATE INDEX idx_resources_tier ON multimodal_resources(tier);
CREATE INDEX idx_resources_img_specific ON multimodal_resources(img_specific);
CREATE INDEX idx_resources_text_embedding ON multimodal_resources USING ivfflat (text_embedding vector_cosine_ops);
CREATE INDEX idx_resources_image_embedding ON multimodal_resources USING ivfflat (image_embedding vector_cosine_ops);

-- Student interaction tracking
CREATE INDEX idx_interactions_student ON student_resource_interactions(student_id, resource_id);
CREATE INDEX idx_uploads_student ON student_uploads(student_id, created_at);

-- Enable Row Level Security
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE multimodal_resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_resource_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_uploads ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Students can view own data" ON students
    FOR SELECT USING (auth.uid()::text = external_id);

CREATE POLICY "Students can view own knowledge" ON student_knowledge
    FOR SELECT USING (student_id IN (
        SELECT id FROM students WHERE external_id = auth.uid()::text
    ));

CREATE POLICY "Students can view own performance" ON performance_logs
    FOR SELECT USING (student_id IN (
        SELECT id FROM students WHERE external_id = auth.uid()::text
    ));

CREATE POLICY "Students can view own plans" ON study_plans
    FOR SELECT USING (student_id IN (
        SELECT id FROM students WHERE external_id = auth.uid()::text
    ));

CREATE POLICY "Anyone can view resources" ON multimodal_resources
    FOR SELECT USING (true);

CREATE POLICY "Students can view own interactions" ON student_resource_interactions
    FOR SELECT USING (student_id IN (
        SELECT id FROM students WHERE external_id = auth.uid()::text
    ));

CREATE POLICY "Students can insert own interactions" ON student_resource_interactions
    FOR INSERT WITH CHECK (student_id IN (
        SELECT id FROM students WHERE external_id = auth.uid()::text
    ));

CREATE POLICY "Students can view own uploads" ON student_uploads
    FOR ALL USING (student_id IN (
        SELECT id FROM students WHERE external_id = auth.uid()::text
    ));

-- Insert seed data for USMLE knowledge areas
INSERT INTO knowledge_areas (name, category, weight_in_exam, subtopics) VALUES
('Cardiology', 'Clinical Medicine', 8.5, ARRAY['Heart Failure', 'Arrhythmias', 'Valvular Disease', 'Coronary Artery Disease']),
('Biochemistry', 'Basic Sciences', 6.0, ARRAY['Enzyme Kinetics', 'Metabolic Pathways', 'Molecular Biology', 'Nutrition']),
('Anatomy', 'Basic Sciences', 5.5, ARRAY['Thorax', 'Abdomen', 'Neuroanatomy', 'Musculoskeletal']),
('Physiology', 'Basic Sciences', 6.5, ARRAY['Respiratory', 'Cardiovascular', 'Renal', 'Endocrine']),
('Pathology', 'Basic Sciences', 8.0, ARRAY['Inflammation', 'Neoplasia', 'Hemodynamic Disorders', 'Genetic Disorders']),
('Pharmacology', 'Basic Sciences', 7.0, ARRAY['Autonomic Drugs', 'Cardiovascular Drugs', 'Antimicrobials', 'CNS Drugs']),
('Neurology', 'Clinical Medicine', 5.5, ARRAY['Stroke Syndromes', 'Seizures', 'Neurodegenerative Diseases', 'Peripheral Neuropathy']),
('Microbiology', 'Basic Sciences', 6.0, ARRAY['Bacteriology', 'Virology', 'Mycology', 'Parasitology']),
('Ethics', 'Professional Competence', 3.5, ARRAY['Informed Consent', 'End-of-Life Care', 'Confidentiality', 'Resource Allocation']),
('Preventive Medicine', 'Public Health', 3.0, ARRAY['Epidemiology', 'Biostatistics', 'Screening Guidelines', 'Vaccination']);

-- Insert sample multimodal resources
-- (Full insertion script would include all 30+ resources from resource_optimizer.py)
INSERT INTO multimodal_resources (resource_id, name, source, modality, area, topic, description, tier, page_range, estimated_hours, img_specific) VALUES
('fa-txt-cardio', 'First Aid - Cardiovascular System', 'First Aid for USMLE Step 1', 'text', 'Cardiology', 'Complete cardiovascular chapter', 'Comprehensive cardiovascular physiology, pathology, pharmacology', 'essential', 'pp. 265-288', 4.0, false),
('fa-txt-biochem', 'First Aid - Biochemistry', 'First Aid for USMLE Step 1', 'text', 'Biochemistry', 'Complete biochemistry chapter', 'Metabolic pathways, enzyme kinetics, molecular biology, nutrition', 'essential', 'pp. 95-128', 3.5, false),
('fa-img-metabolic', 'First Aid Metabolic Pathway Maps', 'First Aid for USMLE Step 1', 'image', 'Biochemistry', 'Metabolic pathway diagrams', 'Visual maps of glycolysis, gluconeogenesis, TCA cycle, ETC, HMP shunt', 'essential', NULL, 2.0, false),
('ecg-img-arrhythm', 'ECG Arrhythmia Collection', 'UWorld / First Aid', 'image', 'Cardiology', 'Arrhythmia ECG strips', 'ECG strips showing AFib, AFlutter, VTach, VFib, heart blocks, WPW, torsades', 'essential', NULL, 2.5, false),
('path-img-cardio', 'Pathoma Cardiovascular Pathology Images', 'Pathoma', 'image', 'Cardiology', 'Cardiovascular pathology slides', 'Histopathology images of atherosclerosis, MI, valvular lesions', 'high-yield', NULL, 2.0, false),
('nbme-pdf-score-report', 'NBME Score Report Interpretation Guide', 'NBME', 'pdf', 'Assessment', 'How to read NBME reports', 'Official guide to interpreting NBME score reports', 'reference', NULL, 0.5, true),
('guide-pdf-img-prep', 'IMG Guide to USMLE Step 1', 'ECFMG', 'pdf', 'General', 'IMG-specific preparation guide', 'Comprehensive guide for IMGs: registration, requirements, strategies', 'high-yield', NULL, 2.0, true),
('path-vid-general', 'Pathoma General Pathology Lectures', 'Pathoma (Dr. Sattar)', 'video', 'Pathology', 'Chapters 1-3: General pathology', 'General pathology: inflammation, neoplasia, genetics', 'essential', NULL, 3.0, false),
('bb-vid-biochem', 'Boards & Beyond Biochemistry Series', 'Boards & Beyond (Dr. Ryan)', 'video', 'Biochemistry', 'Complete biochemistry lecture series', 'Metabolism, molecular biology, genetics, nutrition', 'essential', NULL, 5.0, false),
('audio-podcast-highyield', 'High Yield USMLE Podcast - Cardiology', 'High Yield USMLE Podcast', 'audio', 'Cardiology', 'Cardiology review podcast episodes', 'Audio review of cardiology high-yield concepts', 'supplementary', NULL, 2.0, false),
('img-txt-us-system', 'US Healthcare System for IMGs', 'Custom (Blessie''s Guide)', 'text', 'Ethics', 'US healthcare system overview', 'Insurance types, referral systems, prior authorization', 'high-yield', NULL, 1.5, true),
('img-txt-lab-values', 'US Reference Lab Values for IMGs', 'Custom (Blessie''s Guide)', 'text', 'General', 'US laboratory reference ranges', 'Normal lab values used in USMLE', 'high-yield', NULL, 1.0, true),
('free-120', 'USMLE Free 120 Questions', 'USMLE/FSMB', 'pdf', 'Assessment', 'Official free practice questions', '120 official USMLE practice questions - most representative', 'essential', NULL, 4.0, true);
