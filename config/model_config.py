"""
Model configuration and parameters for AI models.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class ModelParameters:
    """Parameters for a specific model."""
    
    name: str
    provider: str
    max_tokens: int
    temperature: float = 0.7
    top_p: float = 0.95
    timeout: int = 60
    max_retries: int = 3
    supports_vision: bool = False
    supports_streaming: bool = False
    context_window: int = 8192


@dataclass
class ModelConfig:
    """Configuration for all AI models used in the application."""
    
    # Gemini Models
    gemini_flash: ModelParameters = field(
        default_factory=lambda: ModelParameters(
            name="gemini-1.5-flash",
            provider="google",
            max_tokens=8192,
            temperature=0.7,
            top_p=0.95,
            timeout=60,
            max_retries=3,
            supports_vision=True,
            supports_streaming=True,
            context_window=1000000,  # 1M tokens
        )
    )
    
    gemini_pro: ModelParameters = field(
        default_factory=lambda: ModelParameters(
            name="gemini-1.5-pro",
            provider="google",
            max_tokens=8192,
            temperature=0.7,
            top_p=0.95,
            timeout=90,
            max_retries=3,
            supports_vision=True,
            supports_streaming=True,
            context_window=1000000,  # 1M tokens
        )
    )
    
    # Groq Models
    llama_70b: ModelParameters = field(
        default_factory=lambda: ModelParameters(
            name="llama-3.1-70b-versatile",
            provider="groq",
            max_tokens=8192,
            temperature=0.7,
            top_p=0.95,
            timeout=30,
            max_retries=3,
            supports_vision=False,
            supports_streaming=True,
            context_window=32768,
        )
    )
    
    mixtral_8x7b: ModelParameters = field(
        default_factory=lambda: ModelParameters(
            name="mixtral-8x7b-32768",
            provider="groq",
            max_tokens=32768,
            temperature=0.7,
            top_p=0.95,
            timeout=30,
            max_retries=3,
            supports_vision=False,
            supports_streaming=True,
            context_window=32768,
        )
    )
    
    llama_vision: ModelParameters = field(
        default_factory=lambda: ModelParameters(
            name="llama-3.2-11b-vision-preview",
            provider="groq",
            max_tokens=8192,
            temperature=0.7,
            top_p=0.95,
            timeout=45,
            max_retries=3,
            supports_vision=True,
            supports_streaming=True,
            context_window=8192,
        )
    )
    
    def get_model(self, model_name: str) -> ModelParameters:
        """
        Get model parameters by name.
        
        Args:
            model_name: Model identifier
            
        Returns:
            ModelParameters instance
            
        Raises:
            ValueError: If model not found
        """
        model_map = {
            "gemini-1.5-flash": self.gemini_flash,
            "gemini-1.5-pro": self.gemini_pro,
            "llama-3.1-70b-versatile": self.llama_70b,
            "mixtral-8x7b-32768": self.mixtral_8x7b,
            "llama-3.2-11b-vision-preview": self.llama_vision,
        }
        
        if model_name not in model_map:
            raise ValueError(f"Unknown model: {model_name}")
        
        return model_map[model_name]
    
    def get_fallback_model(self, primary_model: str) -> str:
        """
        Get fallback model for a primary model.
        
        Args:
            primary_model: Primary model name
            
        Returns:
            Fallback model name
        """
        fallback_map = {
            "gemini-1.5-flash": "llama-3.2-11b-vision-preview",
            "gemini-1.5-pro": "gemini-1.5-flash",
            "llama-3.1-70b-versatile": "mixtral-8x7b-32768",
            "mixtral-8x7b-32768": "llama-3.1-70b-versatile",
            "llama-3.2-11b-vision-preview": "gemini-1.5-flash",
        }
        
        return fallback_map.get(primary_model, "gemini-1.5-flash")
    
    def list_available_models(self, provider: str = None) -> List[str]:
        """
        List all available models, optionally filtered by provider.
        
        Args:
            provider: Optional provider filter (google, groq)
            
        Returns:
            List of model names
        """
        models = [
            self.gemini_flash,
            self.gemini_pro,
            self.llama_70b,
            self.mixtral_8x7b,
            self.llama_vision,
        ]
        
        if provider:
            models = [m for m in models if m.provider == provider]
        
        return [m.name for m in models]


# System prompts for different tasks
SYSTEM_PROMPTS = {
    "ocr": """You are an expert at extracting text from handwritten notes and images.
Your task is to:
1. Accurately transcribe all visible text, including handwriting
2. Preserve the structure and hierarchy (headings, bullet points, etc.)
3. Identify and extract mathematical formulas, equations, and diagrams
4. Note any unclear or illegible sections with [UNCLEAR: description]
5. Maintain the original organization and flow

Format your response as structured markdown.""",
    
    "format": """You are a note formatting specialist.
Your task is to:
1. Convert raw extracted text into well-formatted markdown notes
2. Apply proper heading hierarchy (# ## ###)
3. Create clean bullet points and numbered lists
4. Format code blocks, equations, and special content appropriately
5. Add appropriate emphasis (bold, italic) for key concepts
6. Ensure readability and consistent formatting

Follow the user's preferred note-taking style.""",
    
    "analyze": """You are an educational content analyzer.
Your task is to:
1. Identify key concepts, definitions, and important information
2. Extract main topics and subtopics
3. Generate concise summaries
4. Detect relationships between concepts
5. Highlight critical information for study
6. Suggest relevant tags and categories

Provide your analysis in a structured format.""",
    
    "plan": """You are a personalized study planning assistant.
Your task is to:
1. Analyze recent notes and identify learning gaps
2. Prioritize subjects based on difficulty and importance
3. Create balanced daily study schedules
4. Apply spaced repetition principles
5. Adapt to the user's learning style and preferences
6. Provide specific, actionable study tasks

Generate a comprehensive yet realistic daily study plan.""",
}


# Generation parameters for specific tasks
TASK_PARAMETERS = {
    "ocr": {
        "temperature": 0.3,  # Lower for accuracy
        "max_tokens": 8192,
        "top_p": 0.9,
    },
    "format": {
        "temperature": 0.5,
        "max_tokens": 4096,
        "top_p": 0.95,
    },
    "analyze": {
        "temperature": 0.6,
        "max_tokens": 4096,
        "top_p": 0.95,
    },
    "plan": {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 0.95,
    },
    "summarize": {
        "temperature": 0.5,
        "max_tokens": 2048,
        "top_p": 0.9,
    },
}


@lru_cache()
def get_model_config() -> ModelConfig:
    """
    Get cached model configuration instance.
    
    Returns:
        ModelConfig instance
    """
    return ModelConfig()


def get_system_prompt(task: str) -> str:
    """
    Get system prompt for a specific task.
    
    Args:
        task: Task type
        
    Returns:
        System prompt string
    """
    return SYSTEM_PROMPTS.get(task, "You are a helpful AI assistant.")


def get_task_parameters(task: str) -> Dict[str, Any]:
    """
    Get generation parameters for a specific task.
    
    Args:
        task: Task type
        
    Returns:
        Dictionary of parameters
    """
    return TASK_PARAMETERS.get(task, {"temperature": 0.7, "max_tokens": 4096})