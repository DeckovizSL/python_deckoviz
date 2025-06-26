import os
from typing import List, Optional
from pydantic import BaseModel
import pdfplumber
import re
import nltk
from nltk.tokenize import sent_tokenize
from ..llm import GeminiLLM

# Ensure nltk resources are available
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

class BookToFramesService:
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.llm = GeminiLLM(model_name=model_name)

    def extract_text(self, pdf_path: str, start_page: int, end_page: Optional[int] = None) -> str:
        full_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            start = max(0, start_page - 1)
            end = min(end_page, total_pages) if end_page else total_pages
            for i in range(start, end):
                text = pdf.pages[i].extract_text()
                if text:
                    full_text += text + "\n"
        return full_text

    def sentence_split(self, text: str) -> List[str]:
        try:
            return sent_tokenize(text)
        except Exception:
            return re.split(r'(?<=[.!?])\s+', text)

    def split_text_into_exact_sections(self, text: str, n_sections: int) -> List[str]:
        sentences = self.sentence_split(text)
        total_sentences = len(sentences)
        sections = []
        sentences_per_section = total_sentences // n_sections
        remainder = total_sentences % n_sections
        start = 0
        for i in range(n_sections):
            end = start + sentences_per_section + (1 if i < remainder else 0)
            section_sentences = sentences[start:end]
            section_text = " ".join(section_sentences).strip()
            sections.append(section_text)
            start = end
        return sections

    def scene_prompt_template(self, text: str) -> str:
        return (
            "You are an expert prompt engineer for an image generation model. "
            "Your task is to convert a story scene into a single, direct, and vivid image generation prompt. "
            "Follow these instructions strictly:"
            "\n\n--- INSTRUCTIONS ---\n"
            "1. Read the provided story scene.\n"
            "2. Create ONE SINGLE PARAGRAPH that is a visually descriptive prompt. This single paragraph is your only output.\n"
            "3. The prompt must be a direct instruction to an image model. Start with the visual description immediately.\n"
            "4. DO NOT add any extra text, explanations, headings, markdown, bullet points, or variations. \n"
            "5. DO NOT write 'Prompt:', 'Keywords:', 'Negative Prompt:', or anything similar. \n"
            "6. Your entire output must be only the prompt itself and nothing else.\n"
            "\n--- STORY SCENE ---\n"
            f"{text.strip()}"
            "\n\n--- FINAL PROMPT ---\n"
        )

    def generate_prompts_from_pdf(self, pdf_path: str, start_page: int, end_page: Optional[int], num_sections: int) -> List[str]:
        full_text = self.extract_text(pdf_path, start_page, end_page)
        sections = self.split_text_into_exact_sections(full_text, num_sections)
        prompts = []
        for section in sections:
            prompt_input = self.scene_prompt_template(section)
            result = self.llm._call(prompt_input)
            # Clean up any residual conversational artifacts.
            cleaned_result = result.strip().strip('`" ')
            prompts.append(cleaned_result)
        return prompts 