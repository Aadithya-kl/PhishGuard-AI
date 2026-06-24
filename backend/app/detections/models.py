import enum
from pydantic import BaseModel, Field
from typing import List

class DetectionSeverity(str, enum.Enum):
    info = "Info"
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"



class MitreMapping(BaseModel):
    technique_id: str
    tactic: str
    name: str

class DetectionResult(BaseModel):
    detection_name: str
    category: str
    severity: DetectionSeverity
    confidence: int = Field(ge=0, le=100)
    risk_contribution: float
    matched_patterns: List[str] = Field(default_factory=list)
    mitre_mappings: List[MitreMapping] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    explanation: str
