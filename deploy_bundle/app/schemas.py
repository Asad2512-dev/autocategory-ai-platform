from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    brand: str | None = None


class CandidateCategory(BaseModel):
    category: str
    confidence: float


class PredictResponse(BaseModel):
    predicted_category: str
    suggested_new_category: str | None = None
    confidence: float
    low_confidence: bool
    review_needed: bool
    flagged_for_retraining: bool
    top_candidates: list[CandidateCategory]
    prediction_source: str
    message: str


class FeedbackRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    predicted_category: str = Field(..., min_length=1)
    corrected_category: str = Field(..., min_length=1)
    confidence: float
    low_confidence: bool
    review_needed: bool
    flagged_for_retraining: bool
    prediction_source: str = Field(..., min_length=1)


class FeedbackResponse(BaseModel):
    saved: bool
    path: str


class GeminiFallbackCheckRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    brand: str | None = None


class ModelInfoResponse(BaseModel):
    """Additive endpoint metadata; safe for existing mobile clients that do not call it."""

    ready: bool
    model_name: str
    app_version: str = "1.0.0"
    num_labels: int = 0
    labels: list[str] = Field(default_factory=list)
    model_dir: str
    training_generated_at: str | None = None
    error: str | None = None


class GeminiFallbackCheckResponse(BaseModel):
    success: bool
    gemini_enabled: bool
    fallback_tested: bool
    prediction_source: str
    predicted_category: str | None = None
    suggested_new_category: str | None = None
    confidence: float | None = None
    review_needed: bool | None = None
    reason: str | None = None
    raw_response_available: bool
    message: str
    error: str | None = None
