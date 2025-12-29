import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    _loaded: bool = False
    
    @classmethod
    def load(cls) -> bool:
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"
        
        if env_path.exists():
            load_dotenv(env_path)
            cls._loaded = True
        return cls._loaded
    
    @classmethod
    def is_configured(cls) -> bool:
        return cls._loaded
