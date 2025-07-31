from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict

class Query(BaseModel):
    question: str
    context: Optional[Dict] = Field(
        default={
            'id':None
        }
    )
    created: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What is the news that have impacts?",
                    "context": {
                        'id':['']
                    }
                }
            ]
        }
    }