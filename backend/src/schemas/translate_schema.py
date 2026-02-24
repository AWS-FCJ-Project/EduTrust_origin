from enum import Enum

from pydantic import BaseModel, Field


class Language(str, Enum):
    VIETNAMESE = "vietnamese"
    ENGLISH = "english"


class TranslateRequest(BaseModel):
    language: Language = Field(..., description="Target language")
    text: str = Field(..., description="Text to translate")


class TranslateResponse(BaseModel):
    text: str = Field(..., description="Translated text")
