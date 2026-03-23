from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ScrapedMetrics(BaseModel):
	word_count: int = Field(..., ge=0)
	h1_count: int = Field(..., ge=0)
	h2_count: int = Field(..., ge=0)
	h3_count: int = Field(..., ge=0)
	cta_count: int = Field(..., ge=0)
	internal_links: int = Field(..., ge=0)
	external_links: int = Field(..., ge=0)
	image_count: int = Field(..., ge=0)
	missing_alt_text_percent: float = Field(..., ge=0, le=100)
	meta_title: Optional[str] = None
	meta_description: Optional[str] = None


class Recommendation(BaseModel):
	priority: Literal["High", "Medium", "Low"]
	issue: str
	action: str
	reasoning: str
	expected_impact: str


class Scores(BaseModel):
	current_seo_score: int = Field(..., ge=0, le=100)
	potential_seo_score: int = Field(..., ge=0, le=100)
	current_ux_score: int = Field(..., ge=0, le=100)
	potential_ux_score: int = Field(..., ge=0, le=100)


class AIAnalysis(BaseModel):
	seo_structure: str
	messaging_clarity: str
	cta_usage: str
	content_depth: str
	ux_concerns: str
	recommendations: List[Recommendation]
	scores: Scores
