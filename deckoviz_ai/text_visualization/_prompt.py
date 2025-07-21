# Prompt logic for text visualization will be implemented here. 

def generate_visualization_prompt(text_chunk: str, user_prompt: str) -> str:
    """
    Generate a visualization prompt for the AI, combining the user-provided visualization prompt and the text chunk.
    """
    return (
        f"You are an expert prompt engineer for an image generation model. "
        f"Your task is to create a vivid, direct image generation prompt based on the following instructions and text.\n"
        f"--- USER VISUALIZATION INSTRUCTION ---\n"
        f"{user_prompt.strip()}\n"
        f"--- TEXT TO VISUALIZE ---\n"
        f"{text_chunk.strip()}\n"
        f"--- FINAL PROMPT ---\n"
        f"(Output only the image prompt, no extra text, no explanations, no headings.)"
    ) 