import os
from typing import List, Optional, Literal
import re
import pdfplumber
from ._schemas import TextVisualizationInput, TextVisualizationOutput
from ._prompt import generate_visualization_prompt
from ..llm import GeminiLLM

# Utility for paragraph splitting
def split_into_paragraphs(text: str) -> List[str]:
    # Split on two or more newlines, strip whitespace
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    return paras

class TextVisualizationService:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.llm = GeminiLLM(model_name=model_name)

    def extract_text_from_pdf(self, pdf_path: str, start_page: int, end_page: Optional[int] = None) -> List[str]:
        """
        Extract text per page from a PDF, for the given page range (1-indexed, inclusive).
        Returns a list of page texts.
        """
        pages_text = []
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            start = max(0, start_page - 1)
            end = min(end_page, total_pages) if end_page else total_pages
            for i in range(start, end):
                text = pdf.pages[i].extract_text()
                pages_text.append(text or "")
        return pages_text

    def split_pdf_by_paragraph(self, pdf_path: str, start_page: int, end_page: Optional[int] = None) -> List[str]:
        """
        Extracts all text in the page range and splits into paragraphs.
        """
        pages_text = self.extract_text_from_pdf(pdf_path, start_page, end_page)
        full_text = "\n".join(pages_text)
        return split_into_paragraphs(full_text)

    def split_pdf_by_page(self, pdf_path: str, start_page: int, end_page: Optional[int] = None) -> List[str]:
        """
        Returns a list of text, one per page.
        """
        return self.extract_text_from_pdf(pdf_path, start_page, end_page)

    def split_pdf_by_2_images_per_page(self, pdf_path: str, start_page: int, end_page: Optional[int] = None) -> List[str]:
        """
        For each page, split the text in half (by character count) for 2 images per page.
        """
        pages_text = self.extract_text_from_pdf(pdf_path, start_page, end_page)
        sections = []
        for page_text in pages_text:
            if not page_text:
                sections.extend(["", ""])
                continue
            mid = len(page_text) // 2
            sections.append(page_text[:mid].strip())
            sections.append(page_text[mid:].strip())
        return sections

    def split_text_by_paragraph(self, text: str) -> List[str]:
        return split_into_paragraphs(text)

    def generate_prompts(self, data: TextVisualizationInput) -> List[str]:
        prompts = []
        if data.input_type == "text":
            if data.image_density != "1_image_per_paragraph":
                raise ValueError("Only '1_image_per_paragraph' is supported for text input.")
            if not data.text:
                raise ValueError("Text input is required for input_type 'text'.")
            chunks = self.split_text_by_paragraph(data.text)
            for chunk in chunks:
                if not chunk:  # Skip empty chunks
                    continue
                # 1. Generate the full system prompt for the LLM
                llm_input_prompt = generate_visualization_prompt(chunk, data.visualization_prompt)

                # 2. Call the LLM to get the clean, final image prompt
                final_image_prompt = self.llm._call(llm_input_prompt)

                # 3. Clean up the LLM's output and add to the list
                cleaned_prompt = final_image_prompt.strip().strip('`" ')
                prompts.append(cleaned_prompt)
        elif data.input_type == "pdf":
            if not data.pdf_file_path:
                raise ValueError("PDF file path is required for input_type 'pdf'.")
            start = data.page_start or 1
            end = data.page_end
            if data.image_density == "1_image_per_paragraph":
                chunks = self.split_pdf_by_paragraph(data.pdf_file_path, start, end)
            elif data.image_density == "1_image_per_page":
                chunks = self.split_pdf_by_page(data.pdf_file_path, start, end)
            elif data.image_density == "2_images_per_page":
                chunks = self.split_pdf_by_2_images_per_page(data.pdf_file_path, start, end)
            else:
                raise ValueError("Invalid image_density for PDF input.")
            for chunk in chunks:
                if not chunk:  # Skip empty chunks
                    continue
                # 1. Generate the full system prompt for the LLM
                llm_input_prompt = generate_visualization_prompt(chunk, data.visualization_prompt)

                # 2. Call the LLM to get the clean, final image prompt
                final_image_prompt = self.llm._call(llm_input_prompt)

                # 3. Clean up the LLM's output and add to the list
                cleaned_prompt = final_image_prompt.strip().strip('`" ')
                prompts.append(cleaned_prompt)
        else:
            raise ValueError("Invalid input_type.")
        return prompts

    # Add more methods for prompt generation and image generation as needed 