from typing import Optional

FLUX_PROMPT_TEMPLATE = """
{base_prompt}
Style: {style}
"""

def build_flux_prompt(base_prompt: str, style: Optional[str] = None) -> str:
    if style:
        return FLUX_PROMPT_TEMPLATE.format(base_prompt=base_prompt, style=style)
    return base_prompt 