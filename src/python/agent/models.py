from typing import Literal, List, Optional, Any
from pydantic import BaseModel, Field


class InputField(BaseModel):
    """Definition of a single input field."""
    name: str = Field(description="Unique identifier for the field")
    label: str = Field(description="Human-readable label for the field")
    type: Literal["text", "number", "select", "boolean"] = Field(description="Type of input control")
    default: Optional[Any] = Field(None, description="Default value")
    options: Optional[List[str]] = Field(None, description="Options for select type")
    min: Optional[float] = Field(None, description="Minimum value for number type")
    max: Optional[float] = Field(None, description="Maximum value for number type")
    step: Optional[float] = Field(None, description="Step value for number type")


class InputRequest(BaseModel):
    """Structured request for user input."""
    description: str = Field(description="Explanation of why input is needed")
    fields: List[InputField] = Field(description="List of fields to request")
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Please provide parameters for the filter.",
                "fields": [
                    {"name": "radius", "label": "Radius", "type": "number", "default": 1.0}
                ]
            }
        }
