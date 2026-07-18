from pydantic import BaseModel
from typing import Literal

class ModerationResult(BaseModel):
    decision: Literal["ALLOW", "BLOCK", "HUMAN_REVIEW"]
    reason: str