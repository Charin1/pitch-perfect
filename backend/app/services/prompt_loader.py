# From: backend/app/services/prompt_loader.py
# ----------------------------------------
from pathlib import Path

# A simple in-memory cache to avoid reading files from disk repeatedly.
_prompt_cache = {}
PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(path: str) -> str:
    """
    Loads a prompt template from a file in the 'prompts' directory.
    
    Args:
        path: The relative path to the file within the 'prompts' directory
              (e.g., 'analysis/overview.txt').
              
    Returns:
        The content of the file as a string.
    """
    if path in _prompt_cache:
        return _prompt_cache[path]

    file_path = PROMPTS_DIR / path
    if not file_path.is_file():
        raise FileNotFoundError(f"Prompt file not found at: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()
            _prompt_cache[path] = prompt_text
            return prompt_text
    except Exception as e:
        raise IOError(f"Could not read prompt file at: {file_path}") from e