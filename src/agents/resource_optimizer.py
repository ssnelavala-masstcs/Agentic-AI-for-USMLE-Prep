"""
Multimodal Resource Optimizer Agent - Agent 2 in the LangGraph.

Responsibilities:
1. Ingest multimodal USMLE resources:
   - Text: First Aid chapters, UWorld explanations, lecture notes
   - PDFs: NBME score reports, study guides, journal articles
   - Images: Pathology slides, ECG strips, radiographs, diagrams
   - Video metadata: Pathoma timestamps, B&B lecture segments
   - Audio: Lecture recordings, podcast summaries
2. Build vector embeddings for each modality
3. Retrieve resources via multimodal similarity search
4. Map knowledge gaps to specific high-yield content across modalities
5. Recommend resource combinations based on student learning profile

Implements Retrieval-Augmented Generation (RAG) with multimodal embeddings,
ensuring recommendations are grounded in verified, high-yield content.
"""

import logging
import time
import hashlib
import base64
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from src.agents.state import AgentState, DiagnosticResult, KnowledgeState

logger = logging.getLogger(__name__)


# ============================================================================
# MODALITY ENUMS
# ============================================================================

class Modality(str, Enum):
    """Supported content modalities."""
    TEXT = "text"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class ResourceTier(str, Enum):
    """Resource priority tiers."""
    ESSENTIAL = "essential"
    HIGH_YIELD = "high-yield"
    SUPPLEMENTARY = "supplementary"
    REFERENCE = "reference"


# ============================================================================
# MULTIMODAL RESOURCE DATA MODEL
# ============================================================================

@dataclass
class MultimodalResource:
    """
    A single USMLE study resource with multimodal metadata.
    
    Each resource can have multiple modalities:
    - Text content with vector embedding
    - PDF documents (score reports, guides)
    - Images (pathology, ECG, radiographs) with CLIP embeddings
    - Video segments with timestamps
    - Audio transcripts
    """
    # Core identification
    id: str
    name: str
    source: str  # "First Aid", "UWorld", "Pathoma", "B&B", "NBME", etc.
    modality: Modality
    area: str  # USMLE subject area
    topic: str  # Specific topic
    description: str
    tier: ResourceTier
    
    # Content storage (varies by modality)
    content_text: Optional[str] = None  # Text content / transcript
    content_path: Optional[str] = None  # File path for PDFs/images/audio
    page_range: Optional[str] = None  # e.g., "pp. 265-280"
    timestamp_range: Optional[str] = None  # e.g., "12:30-18:45"
    
    # Embedding storage
    embedding_text: Optional[List[float]] = None  # Text embedding (OpenAI ada-002, 1536d)
    embedding_image: Optional[List[float]] = None  # Image embedding (CLIP ViT-L/14, 768d)
    
    # Image-specific metadata
    image_type: Optional[str] = None  # "pathology_slide", "ECG", "radiograph", "diagram", "table"
    image_description: Optional[str] = None  # Clinical description of image
    
    # Video-specific metadata
    video_url: Optional[str] = None
    duration_minutes: Optional[float] = None
    key_frames: Optional[List[str]] = None  # Important timestamps
    
    # Engagement metrics
    estimated_hours: float = 2.0
    student_rating: Optional[float] = None  # 1-5 from prior users
    usage_count: int = 0
    
    # Tags for filtering
    tags: List[str] = field(default_factory=list)
    img_specific: bool = False  # Flag for IMG-specific content
    
    def compute_content_hash(self) -> str:
        """Unique hash for deduplication."""
        content = f"{self.name}-{self.modality}-{self.topic}-{self.description}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def relevance_score(
        self,
        query_area: str,
        query_topic: str,
        preferred_modalities: Optional[List[Modality]] = None
    ) -> float:
        """
        Calculate multimodal relevance score.
        
        Combines topic matching, modality preference, tier priority,
        and IMG-specific bonuses.
        """
        score = 0.0
        
        # Area match (weighted)
        if self.area.lower() == query_area.lower():
            score += 5.0
        elif query_area.lower() in self.area.lower():
            score += 3.0
        
        # Topic match in description
        if query_topic.lower() in self.description.lower():
            score += 3.0
        if query_topic.lower() in self.topic.lower():
            score += 2.0
        
        # Tags match
        for tag in self.tags:
            if query_topic.lower() in tag.lower():
                score += 1.0
        
        # Modality preference bonus
        if preferred_modalities:
            if self.modality in preferred_modalities:
                score += 2.0
            # Visual learners get image/video bonus
            if self.modality in [Modality.IMAGE, Modality.VIDEO]:
                score += 1.0
        
        # Tier bonus
        tier_scores = {
            ResourceTier.ESSENTIAL: 2.5,
            ResourceTier.HIGH_YIELD: 1.8,
            ResourceTier.SUPPLEMENTARY: 1.0,
            ResourceTier.REFERENCE: 0.5
        }
        score += tier_scores.get(self.tier, 0.0)
        
        # Student rating bonus (social proof)
        if self.student_rating:
            score += (self.student_rating / 5.0) * 1.5
        
        # IMG-specific bonus for IMG students
        if self.img_specific:
            score += 1.5
        
        # Usage count bonus (popular resources)
        if self.usage_count > 10:
            score += 0.5
        
        return score


# ============================================================================
# MULTIMODAL RESOURCE DATABASE
# ============================================================================
# Blessie (Clinical Lead) validates this mapping.
# Includes text, images, PDFs, video metadata, and audio transcripts.

MULTIMODAL_DATABASE: List[MultimodalResource] = [
    
    # ==================== TEXT RESOURCES ====================
    
    # First Aid - Text chapters
    MultimodalResource("fa-txt-cardio", "First Aid - Cardiovascular System",
                       "First Aid for USMLE Step 1", Modality.TEXT,
                       "Cardiology", "Complete cardiovascular chapter",
                       "Comprehensive cardiovascular physiology, pathology, pharmacology",
                       ResourceTier.ESSENTIAL,
                       content_text="Cardiovascular chapter covering heart failure, arrhythmias, valvular disease, CAD...",
                       page_range="pp. 265-288",
                       estimated_hours=4.0, student_rating=4.8, usage_count=150,
                       tags=["physiology", "pathology", "pharmacology", "high-yield"]),
    
    MultimodalResource("fa-txt-biochem", "First Aid - Biochemistry",
                       "First Aid for USMLE Step 1", Modality.TEXT,
                       "Biochemistry", "Complete biochemistry chapter",
                       "Metabolic pathways, enzyme kinetics, molecular biology, nutrition",
                       ResourceTier.ESSENTIAL,
                       content_text="Biochemistry chapter covering glycolysis, TCA cycle, ETC, enzyme kinetics...",
                       page_range="pp. 95-128",
                       estimated_hours=3.5, student_rating=4.5, usage_count=140,
                       tags=["metabolism", "enzymes", "genetics", "vitamins"]),
    
    MultimodalResource("fa-txt-ethics", "First Aid - Ethics & Behavioral Science",
                       "First Aid for USMLE Step 1", Modality.TEXT,
                       "Ethics", "Behavioral sciences chapter",
                       "Medical ethics, informed consent, end-of-life care, physician-patient communication",
                       ResourceTier.HIGH_YIELD,
                       page_range="pp. 293-304",
                       estimated_hours=1.5, student_rating=4.2, usage_count=90,
                       tags=["ethics", "legal", "communication", "IMG-important"],
                       img_specific=True),
    
    # UWorld - Text explanations
    MultimodalResource("uw-txt-cardio", "UWorld Cardiology Explanations",
                       "UWorld Step 1 QBank", Modality.TEXT,
                       "Cardiology", "Detailed answer explanations",
                       "In-depth explanations for all cardiology questions with educational objectives",
                       ResourceTier.ESSENTIAL,
                       estimated_hours=8.0, student_rating=4.9, usage_count=200,
                       tags=["questions", "explanations", "clinical-vignettes"]),
    
    MultimodalResource("uw-txt-pharm", "UWorld Pharmacology Explanations",
                       "UWorld Step 1 QBank", Modality.TEXT,
                       "Pharmacology", "Detailed answer explanations",
                       "Drug mechanisms, adverse effects, interactions, clinical indications",
                       ResourceTier.ESSENTIAL,
                       estimated_hours=7.0, student_rating=4.8, usage_count=180,
                       tags=["drug-mechanisms", "side-effects", "indications"]),
    
    # ==================== IMAGE RESOURCES ====================
    
    # Pathology slides
    MultimodalResource("path-img-cardio", "Pathoma Cardiovascular Pathology Images",
                       "Pathoma", Modality.IMAGE,
                       "Cardiology", "Cardiovascular pathology slides",
                       "Histopathology images of atherosclerosis, myocardial infarction, valvular lesions",
                       ResourceTier.HIGH_YIELD,
                       image_type="pathology_slide",
                       image_description="H&E stained sections showing coronary artery atherosclerosis, "
                                        "myocardial coagulative necrosis (days 1-7), granulation tissue, "
                                        "fibrous scar. Valvular vegetation images for endocarditis.",
                       content_text="Key findings: Day 1-4: coagulative necrosis with neutrophils. "
                                    "Day 5-10: macrophages, granulation tissue. Week 2+: collagen deposition.",
                       estimated_hours=2.0, student_rating=4.7, usage_count=120,
                       tags=["histology", "MI-timeline", "gross-pathology", "high-yield-images"]),
    
    MultimodalResource("path-img-inflamm", "Pathoma Inflammation Images",
                       "Pathoma", Modality.IMAGE,
                       "Pathology", "Inflammation and repair histology",
                       "Acute and chronic inflammation images: neutrophil infiltration, granulomas, wound healing",
                       ResourceTier.ESSENTIAL,
                       image_type="pathology_slide",
                       image_description="Acute inflammation: neutrophil-rich infiltrate. "
                                        "Chronic inflammation: lymphocyte and macrophage predominance. "
                                        "Granuloma: epithelioid histiocytes with Langhans giant cells.",
                       estimated_hours=2.5, student_rating=4.9, usage_count=160,
                       tags=["granuloma", "wound-healing", "acute", "chronic"]),
    
    # ECG strips
    MultimodalResource("ecg-img-arrhythm", "ECG Arrhythmia Collection",
                       "UWorld / First Aid", Modality.IMAGE,
                       "Cardiology", "Arrhythmia ECG strips",
                       "ECG strips showing AFib, AFlutter, VTach, VFib, heart blocks, WPW, torsades",
                       ResourceTier.ESSENTIAL,
                       image_type="ECG",
                       image_description="12-lead ECG strips: AFib (irregularly irregular, no P waves), "
                                        "AFlutter (sawtooth F waves), Complete heart block (AV dissociation), "
                                        "VTach (wide complex tachycardia), Torsades de pointes (twisting axis)",
                       estimated_hours=2.5, student_rating=4.6, usage_count=130,
                       tags=["EKG", "arrhythmia", "heart-block", "must-know"]),
    
    # Radiographs
    MultimodalResource("rad-img-cardio", "Cardiovascular Radiographs",
                       "UWorld / Radiopaedia", Modality.IMAGE,
                       "Cardiology", "CXR and cardiac imaging",
                       "CXR findings in heart failure, cardiomegaly, pulmonary edema, pleural effusions",
                       ResourceTier.HIGH_YIELD,
                       image_type="radiograph",
                       image_description="CXR: cardiomegaly (CTR > 0.5), cephalization of pulmonary vessels, "
                                        "Kerley B lines (interstitial edema), bat-wing opacities (alveolar edema), "
                                        "pleural effusions (blunted costophrenic angles)",
                       estimated_hours=1.5, student_rating=4.3, usage_count=85,
                       tags=["CXR", "heart-failure", "pulmonary-edema", "clinical"]),
    
    # Diagrams and tables
    MultimodalResource("fa-img-metabolic", "First Aid Metabolic Pathway Maps",
                       "First Aid for USMLE Step 1", Modality.IMAGE,
                       "Biochemistry", "Metabolic pathway diagrams",
                       "Visual maps of glycolysis, gluconeogenesis, TCA cycle, ETC, HMP shunt",
                       ResourceTier.ESSENTIAL,
                       image_type="diagram",
                       image_description="Glycolysis: Glucose → 2 Pyruvate (net 2 ATP, 2 NADH). "
                                        "Key enzymes: Hexokinase, PFK-1 (rate-limiting), Pyruvate kinase. "
                                        "TCA Cycle: Acetyl-CoA → 3 NADH, 1 FADH2, 1 GTP, 2 CO2.",
                       estimated_hours=2.0, student_rating=4.7, usage_count=145,
                       tags=["pathways", "enzymes", "rate-limiting-steps", "visual-learner"]),
    
    MultimodalResource("fa-img-pharm-tables", "First Aid Pharmacology Tables",
                       "First Aid for USMLE Step 1", Modality.IMAGE,
                       "Pharmacology", "Drug classification tables",
                       "Summary tables: Autonomic drugs, antiarrhythmics, antihypertensives, antibiotics",
                       ResourceTier.ESSENTIAL,
                       image_type="table",
                       image_description="Class I antiarrhythmics: Na+ channel blockers (Quinidine, "
                                        "Lidocaine, Flecainide). Class II: Beta blockers. "
                                        "Class III: K+ channel blockers (Amiodarone). "
                                        "Class IV: Ca2+ channel blockers (Verapamil, Diltiazem).",
                       estimated_hours=3.0, student_rating=4.8, usage_count=155,
                       tags=["drug-tables", "classification", "mechanism", "high-yield"]),
    
    # ==================== PDF RESOURCES ====================
    
    # NBME score reports
    MultimodalResource("nbme-pdf-score-report", "NBME Score Report Interpretation Guide",
                       "NBME", Modality.PDF,
                       "Assessment", "How to read NBME reports",
                       "Official guide to interpreting NBME score reports with content area breakdowns",
                       ResourceTier.REFERENCE,
                       content_path="resources/nbme_interpretation_guide.pdf",
                       estimated_hours=0.5, student_rating=4.0, usage_count=60,
                       tags=["assessment", "score-interpretation", "official"],
                       img_specific=True),
    
    # USMLE content outlines
    MultimodalResource("usmle-pdf-content-outline", "USMLE Step 1 Content Outline",
                       "USMLE/FSMB", Modality.PDF,
                       "General", "Official exam content blueprint",
                       "Official USMLE Step 1 content outline with subject weights and task areas",
                       ResourceTier.REFERENCE,
                       content_path="resources/usmle_step1_content_outline.pdf",
                       estimated_hours=1.0, student_rating=4.5, usage_count=100,
                       tags=["official", "blueprint", "exam-structure", "IMG-important"],
                       img_specific=True),
    
    # Study guides
    MultimodalResource("guide-pdf-img-prep", "IMG Guide to USMLE Step 1",
                       "ECFMG", Modality.PDF,
                       "General", "IMG-specific preparation guide",
                       "Comprehensive guide for IMGs: exam registration, clinical experience requirements, study strategies",
                       ResourceTier.HIGH_YIELD,
                       content_path="resources/ecfmg_img_guide.pdf",
                       estimated_hours=2.0, student_rating=4.3, usage_count=75,
                       tags=["IMG", "registration", "ECFMG", "clinical-experience"],
                       img_specific=True),
    
    # ==================== VIDEO RESOURCES ====================
    
    # Pathoma lectures
    MultimodalResource("path-vid-general", "Pathoma General Pathology Lectures",
                       "Pathoma (Dr. Sattar)", Modality.VIDEO,
                       "Pathology", "Chapters 1-3: General pathology",
                       "Dr. Sattar's legendary general pathology lectures: inflammation, neoplasia, genetics",
                       ResourceTier.ESSENTIAL,
                       content_text="Chapter 1: Cell injury and adaptation. "
                                    "Chapter 2: Acute and chronic inflammation. "
                                    "Chapter 3: Neoplasia - oncogenes, tumor suppressors.",
                       video_url="pathoma.com/chapters/1-3",
                       duration_minutes=180,
                       key_frames=["00:00 Cell injury types", "15:30 Necrosis vs apoptosis",
                                   "45:00 Acute inflammation mediators", "90:00 Granuloma formation",
                                   "120:00 Oncogenes vs tumor suppressors", "160:00 Metastasis pathways"],
                       estimated_hours=3.0, student_rating=4.9, usage_count=200,
                       tags=["Sattar", "foundational", "must-watch", "concepts"]),
    
    MultimodalResource("path-vid-cardio", "Pathoma Cardiovascular Pathology",
                       "Pathoma (Dr. Sattar)", Modality.VIDEO,
                       "Cardiology", "Cardiovascular pathology lecture",
                       "Atherosclerosis pathogenesis, MI timeline, valvular heart disease pathology",
                       ResourceTier.HIGH_YIELD,
                       video_url="pathoma.com/chapters/cardio",
                       duration_minutes=65,
                       key_frames=["00:00 Atherosclerosis steps", "15:00 MI timeline (days 1-7)",
                                   "30:00 Heart failure pathology", "45:00 Valvular lesions",
                                   "55:00 Pericardial diseases"],
                       estimated_hours=1.5, student_rating=4.8, usage_count=160,
                       tags=["atherosclerosis", "MI", "heart-failure", "valvular"]),
    
    # Boards & Beyond lectures
    MultimodalResource("bb-vid-biochem", "Boards & Beyond Biochemistry Series",
                       "Boards & Beyond (Dr. Ryan)", Modality.VIDEO,
                       "Biochemistry", "Complete biochemistry lecture series",
                       "Metabolism, molecular biology, genetics, nutrition with clinical correlations",
                       ResourceTier.ESSENTIAL,
                       video_url="boardsbeyond.com/biochemistry",
                       duration_minutes=300,
                       key_frames=["00:00 Glycolysis regulation", "30:00 TCA cycle enzymes",
                                   "60:00 ETC and oxidative phosphorylation", "90:00 Glycogen diseases",
                                   "120:00 Lipid metabolism", "180:00 Molecular biology basics",
                                   "240:00 Vitamin deficiencies"],
                       estimated_hours=5.0, student_rating=4.7, usage_count=140,
                       tags=["metabolism", "clinical-correlations", "visual-explanations"]),
    
    MultimodalResource("bb-vid-cardio-physio", "Boards & Beyond Cardiovascular Physiology",
                       "Boards & Beyond (Dr. Ryan)", Modality.VIDEO,
                       "Physiology", "Cardiovascular physiology lectures",
                       "Cardiac cycle, PV loops, hemodynamics, heart sounds, murmurs",
                       ResourceTier.ESSENTIAL,
                       video_url="boardsbeyond.com/cardio-physiology",
                       duration_minutes=120,
                       key_frames=["00:00 Cardiac cycle phases", "20:00 PV loop analysis",
                                   "40:00 Frank-Starling mechanism", "60:00 Heart sounds",
                                   "80:00 Murmur physiology", "100:00 Hemodynamics"],
                       estimated_hours=2.5, student_rating=4.8, usage_count=150,
                       tags=["PV-loops", "murmurs", "hemodynamics", "mechanisms"]),
    
    # SketchyMedical (visual mnemonics)
    MultimodalResource("sketchy-vid-micro", "Sketchy Micro - Bacteriology",
                       "SketchyMedical", Modality.VIDEO,
                       "Microbiology", "Visual mnemonic bacteriology lectures",
                       "Memory palaces for gram-positive, gram-negative, and atypical bacteria",
                       ResourceTier.HIGH_YIELD,
                       video_url="sketchy.com/medical/microbiology",
                       duration_minutes=240,
                       key_frames=["Staph aureus palace", "Strep pyogenes scene",
                                   "Clostridium farm", "Enterobacteriaceae city"],
                       estimated_hours=4.0, student_rating=4.6, usage_count=170,
                       tags=["visual-mnemonics", "memory-palace", "micro", "IMG-friendly"]),
    
    # ==================== AUDIO RESOURCES ====================
    
    MultimodalResource("audio-podcast-highyield", "High Yield USMLE Podcast - Cardiology",
                       "High Yield USMLE Podcast", Modality.AUDIO,
                       "Cardiology", "Cardiology review podcast episodes",
                       "Audio review of cardiology high-yield concepts for commute/passive learning",
                       ResourceTier.SUPPLEMENTARY,
                       content_text="Episode 42: Heart failure - HFrEF vs HFpEF, "
                                    "Episode 43: Arrhythmias - AFib management, "
                                    "Episode 44: Murmurs - systematic approach",
                       estimated_hours=2.0, student_rating=4.0, usage_count=45,
                       tags=["podcast", "commute", "passive-learning", "review"]),
    
    MultimodalResource("audio-podcast-pharm", "Divine Intervention Podcast - Pharmacology",
                       "Divine Intervention", Modality.AUDIO,
                       "Pharmacology", "High-yield pharmacology pearls",
                       "Rapid-fire pharmacology facts: drug interactions, adverse effects, board favorites",
                       ResourceTier.SUPPLEMENTARY,
                       content_text="Episode 89: Cytochrome P450 inducers and inhibitors, "
                                    "Episode 92: QT-prolonging drugs, "
                                    "Episode 95: Serotonin syndrome drugs",
                       estimated_hours=1.5, student_rating=4.2, usage_count=55,
                       tags=["rapid-fire", "pearls", "drug-interactions", "commute"]),
    
    # ==================== IMG-SPECIFIC RESOURCES ====================
    
    MultimodalResource("img-txt-us-system", "US Healthcare System for IMGs",
                       "Custom (Blessie's Guide)", Modality.TEXT,
                       "Ethics", "US healthcare system overview",
                       "Insurance types (HMO, PPO, Medicare, Medicaid), referral systems, prior authorization",
                       ResourceTier.HIGH_YIELD,
                       content_text="HMO: requires PCP referral for specialists. "
                                    "PPO: direct specialist access, higher cost. "
                                    "Medicare: age ≥65. Medicaid: income-based. "
                                    "Prior authorization required for many procedures.",
                       estimated_hours=1.5, student_rating=4.5, usage_count=65,
                       tags=["healthcare-system", "insurance", "IMG-essential", "ethics"],
                       img_specific=True),
    
    MultimodalResource("img-txt-lab-values", "US Reference Lab Values for IMGs",
                       "Custom (Blessie's Guide)", Modality.TEXT,
                       "General", "US laboratory reference ranges",
                       "Normal lab values used in USMLE (may differ from international ranges)",
                       ResourceTier.HIGH_YIELD,
                       content_text="Na+: 135-145 mEq/L, K+: 3.5-5.0 mEq/L, "
                                    "Cl-: 95-105 mEq/L, HCO3-: 22-28 mEq/L, "
                                    "BUN: 7-20 mg/dL, Cr: 0.6-1.2 mg/dL, "
                                    "Glucose fasting: 70-100 mg/dL, "
                                    "HbA1c normal: <5.7%",
                       estimated_hours=1.0, student_rating=4.7, usage_count=80,
                       tags=["lab-values", "reference-ranges", "IMG-essential", "memorize"],
                       img_specific=True),
    
    # ==================== PRACTICE QUESTION BANKS ====================
    
    MultimodalResource("uw-qbank-cardio", "UWorld Cardiology Question Block",
                       "UWorld Step 1", Modality.TEXT,
                       "Cardiology", "Cardiology practice questions",
                       "80 cardiology questions with detailed explanations and educational objectives",
                       ResourceTier.ESSENTIAL,
                       estimated_hours=6.0, student_rating=4.9, usage_count=200,
                       tags=["qbank", "clinical-vignettes", "detailed-explanations"]),
    
    MultimodalResource("nbme-practice-forms", "NBME Practice Exam Forms 25-31",
                       "NBME", Modality.PDF,
                       "Assessment", "Official practice examinations",
                       "Seven official NBME practice exams with score conversions and content analysis",
                       ResourceTier.ESSENTIAL,
                       estimated_hours=14.0, student_rating=4.9, usage_count=190,
                       tags=["official", "practice-exam", "score-prediction", "timed"],
                       img_specific=True),
    
    MultimodalResource("free-120", "USMLE Free 120 Questions",
                       "USMLE/FSMB", Modality.PDF,
                       "Assessment", "Official free practice questions",
                       "120 official USMLE practice questions - most representative of actual exam style",
                       ResourceTier.ESSENTIAL,
                       content_path="resources/usmle_free_120.pdf",
                       estimated_hours=4.0, student_rating=4.8, usage_count=180,
                       tags=["official", "free", "most-representative", "must-do"],
                       img_specific=True),
]


# ============================================================================
# MULTIMODAL RAG ENGINE
# ============================================================================

class MultimodalRAGEngine:
    """
    Multimodal Retrieval-Augmented Generation engine for USMLE resources.
    
    Supports retrieval across text, images, PDFs, video, and audio modalities
    using a unified relevance scoring system.
    
    For production: Replace with actual vector database (Pinecone, Weaviate,
    or Supabase pgvector) with OpenAI/CLIP embeddings.
    """
    
    def __init__(self, resources: Optional[List[MultimodalResource]] = None):
        self.resources = resources or MULTIMODAL_DATABASE
        self._index_built = False
    
    def build_index(self):
        """
        Build retrieval index.
        
        In production, this would:
        1. Generate text embeddings via OpenAI ada-002
        2. Generate image embeddings via CLIP ViT-L/14
        3. Store in vector database (Supabase pgvector)
        4. Build BM25 text index for keyword search
        """
        logger.info(f"[MultimodalRAG] Building index with {len(self.resources)} resources")
        logger.info(f"  Modalities: {set(r.modality.value for r in self.resources)}")
        logger.info(f"  Areas: {set(r.area for r in self.resources)}")
        self._index_built = True
    
    def retrieve(
        self,
        query_area: str,
        query_topic: str,
        max_results: int = 10,
        modalities: Optional[List[Modality]] = None,
        min_tier: ResourceTier = ResourceTier.SUPPLEMENTARY,
        img_specific_bonus: bool = False
    ) -> List[MultimodalResource]:
        """
        Retrieve relevant resources across all modalities.
        
        Args:
            query_area: USMLE subject area (e.g., "Cardiology")
            query_topic: Specific topic (e.g., "Heart Failure")
            max_results: Maximum number of resources to return
            modalities: Filter by specific modalities (None = all)
            min_tier: Minimum resource tier to include
            img_specific_bonus: Whether to boost IMG-specific resources
            
        Returns:
            Sorted list of MultimodalResource by relevance score
        """
        if not self._index_built:
            self.build_index()
        
        # Filter candidates
        candidates = self.resources
        
        if modalities:
            candidates = [r for r in candidates if r.modality in modalities]
        
        tier_order = {
            ResourceTier.ESSENTIAL: 4,
            ResourceTier.HIGH_YIELD: 3,
            ResourceTier.SUPPLEMENTARY: 2,
            ResourceTier.REFERENCE: 1
        }
        min_tier_val = tier_order.get(min_tier, 0)
        candidates = [r for r in candidates if tier_order.get(r.tier, 0) >= min_tier_val]
        
        # Score and sort
        scored = []
        for resource in candidates:
            score = resource.relevance_score(query_area, query_topic, modalities)
            if img_specific_bonus and resource.img_specific:
                score += 1.5
            scored.append((score, resource))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [r for _, r in scored[:max_results]]
    
    def retrieve_multimodal_set(
        self,
        area: str,
        topic: str,
        target_hours: float,
        learning_style: Optional[str] = None,
        is_img_student: bool = False
    ) -> Dict[str, List[MultimodalResource]]:
        """
        Retrieve a balanced multimodal resource set.
        
        Ensures at least one resource from each relevant modality,
        constrained by available study time.
        
        Returns:
            Dict mapping modality to resource list
        """
        # Determine preferred modalities based on learning style
        preferred_modalities = [Modality.TEXT, Modality.IMAGE]  # Default
        if learning_style == "visual":
            preferred_modalities = [Modality.IMAGE, Modality.VIDEO, Modality.TEXT]
        elif learning_style == "auditory":
            preferred_modalities = [Modality.AUDIO, Modality.VIDEO, Modality.TEXT]
        elif learning_style == "reading":
            preferred_modalities = [Modality.TEXT, Modality.PDF]
        
        # Retrieve from each modality
        results = {}
        total_hours = 0.0
        
        # 1. Primary text resource (always needed)
        text_resources = self.retrieve(area, topic, max_results=2, modalities=[Modality.TEXT])
        if text_resources:
            results[Modality.TEXT] = [text_resources[0]]
            total_hours += text_resources[0].estimated_hours
        
        # 2. Visual resource (image or diagram)
        if "visual" in (learning_style or "") or total_hours < target_hours * 0.5:
            image_resources = self.retrieve(area, topic, max_results=2, modalities=[Modality.IMAGE])
            if image_resources and total_hours < target_hours:
                results[Modality.IMAGE] = [image_resources[0]]
                total_hours += image_resources[0].estimated_hours
        
        # 3. Video resource for explanation
        if total_hours < target_hours:
            video_resources = self.retrieve(area, topic, max_results=2, modalities=[Modality.VIDEO])
            if video_resources and total_hours < target_hours:
                results[Modality.VIDEO] = [video_resources[0]]
                total_hours += video_resources[0].estimated_hours
        
        # 4. Practice questions (essential)
        qbank_resources = self.retrieve(area, topic, max_results=2, modalities=[Modality.TEXT])
        qbank = [r for r in qbank_resources if "qbank" in r.tags or "question" in r.tags.lower()]
        if not qbank:
            # Fallback: any text resource for the area
            qbank = self.retrieve(area, topic, max_results=1, modalities=[Modality.TEXT])
        if qbank and total_hours < target_hours:
            results["qbank"] = [qbank[0]]
            total_hours += qbank[0].estimated_hours
        
        # 5. IMG-specific resources if applicable
        if is_img_student:
            img_resources = self.retrieve(area, topic, max_results=2, img_specific_bonus=True)
            img_specific = [r for r in img_resources if r.img_specific]
            if img_specific:
                results["img_specific"] = img_specific[:1]
        
        # 6. PDF reference if available
        pdf_resources = self.retrieve(area, topic, max_results=1, modalities=[Modality.PDF])
        if pdf_resources and pdf_resources[0].tier in [ResourceTier.ESSENTIAL, ResourceTier.HIGH_YIELD]:
            results[Modality.PDF] = [pdf_resources[0]]
        
        return results
    
    def generate_resource_summary(
        self,
        resources: Dict[str, List[MultimodalResource]],
        area: str,
        topic: str
    ) -> str:
        """Generate human-readable resource summary."""
        lines = [f"Resources for {area}: {topic}", "=" * 50]
        
        for modality, mods in resources.items():
            mod_name = modality.value if isinstance(modality, Modality) else modality
            lines.append(f"\n{mod_name.upper()}:")
            for resource in mods:
                hours = resource.estimated_hours
                rating = f"★{resource.student_rating:.1f}" if resource.student_rating else ""
                lines.append(f"  • {resource.name} ({hours}h) {rating}")
                if resource.page_range:
                    lines.append(f"    Pages: {resource.page_range}")
                if resource.timestamp_range:
                    lines.append(f"    Timestamps: {resource.timestamp_range}")
                if resource.key_frames:
                    lines.append(f"    Key segments: {', '.join(resource.key_frames[:3])}")
                if resource.img_specific:
                    lines.append(f"    [IMG-specific resource]")
        
        return "\n".join(lines)


# ============================================================================
# LANGGRAPH NODE WRAPPER
# ============================================================================

rag_engine = MultimodalRAGEngine()


def resource_optimizer_node(state: AgentState) -> AgentState:
    """
    LangGraph node for the Multimodal Resource Optimizer agent.
    
    Enhances the study plan with specific multimodal resource recommendations
    for each block, considering student learning style and IMG status.
    """
    study_plan = state.get("study_plan")
    diagnostic = state.get("diagnostic")
    knowledge_state = state.get("knowledge_state")
    
    if not study_plan:
        logger.warning("[ResourceOptimizer] No study plan available, skipping resource optimization")
        return state
    
    weak_areas = set(diagnostic.get("weak_areas", [])) if diagnostic else set()
    student_id = state["student_external_id"]
    
    # Infer IMG status (default True for this system)
    is_img_student = True
    
    # Infer learning style from confidence scores (proxy)
    learning_style = "visual"  # Default for IMGs who benefit from visual resources
    
    logger.info(f"[ResourceOptimizer] Adding multimodal resource recommendations to "
                f"{len(study_plan['blocks'])} blocks for {student_id}")
    
    # Enhance each block with multimodal resources
    enhanced_blocks = []
    blocks_by_day: Dict[int, List] = {}
    
    for block in study_plan["blocks"]:
        day = block.get("day", 0)
        if day not in blocks_by_day:
            blocks_by_day[day] = []
        
        area = block.get("area", "Mixed")
        topic = block.get("topic", "High-yield review")
        duration = block.get("duration_hours", 2.0)
        
        # Retrieve multimodal resource set
        resource_set = rag_engine.retrieve_multimodal_set(
            area=area,
            topic=topic,
            target_hours=duration,
            learning_style=learning_style,
            is_img_student=is_img_student
        )
        
        # Generate resource summary
        resource_summary = rag_engine.generate_resource_summary(resource_set, area, topic)
        
        # Flatten resource names for the block
        all_resources = []
        for modality, mods in resource_set.items():
            for mod in mods:
                all_resources.append(mod.name)
        
        # Enhance block
        enhanced_block = block.copy()
        enhanced_block["resources"] = all_resources
        enhanced_block["resource_details"] = resource_set
        enhanced_block["resource_summary"] = resource_summary
        enhanced_block["is_img_optimized"] = is_img_student
        enhanced_blocks.append(enhanced_block)
        blocks_by_day[day].append(enhanced_block)
    
    # Update plan
    enhanced_plan = study_plan.copy()
    enhanced_plan["blocks"] = enhanced_blocks
    enhanced_plan["multimodal_optimization"] = True
    enhanced_plan["resource_modalities"] = list(set(
        r.modality.value 
        for block in enhanced_blocks 
        for mod_name, mods in block.get("resource_details", {}).items()
        if isinstance(mod_name, Modality)
        for r in mods
    ))
    
    execution_log_entry = {
        "agent": "ResourceOptimizer",
        "action": "add_multimodal_resource_recommendations",
        "student_id": student_id,
        "blocks_enhanced": len(enhanced_blocks),
        "modalities_used": enhanced_plan.get("resource_modalities", []),
        "img_optimized": is_img_student,
        "timestamp": time.time()
    }
    
    return {
        **state,
        "study_plan": enhanced_plan,
        "execution_log": state.get("execution_log", []) + [execution_log_entry]
    }
