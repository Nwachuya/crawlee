import re
from typing import Any, Dict, List


ENTITY_REGEX = re.compile(
    r"\b([A-Z][a-z0-9]+[A-Z][a-zA-Z0-9]*|API|JSON|REST|OAuth|HTTP|HTTPS|URL|SDK|JWT|CSS|DOM|SQL)\b"
)


def classify_complexity(text: str) -> str:
    length = len(text)
    has_code_or_acronyms = bool(re.search(r"`|function|const|let|var|class|<|>|HTTP|API|JSON|REST|SSL", text, re.I))
    if length > 350 or (length > 180 and has_code_or_acronyms):
        return "advanced"
    if length > 120 or has_code_or_acronyms:
        return "intermediate"
    return "beginner"


def generate_question(heading: str) -> Dict[str, str]:
    clean = re.sub(r"\s+", " ", heading).strip()
    if clean.endswith("?"):
        return {"question": clean, "type": "direct_question"}

    lower = clean.lower()
    if re.search(r"how to|setup|install|configure|api|guide|quickstart|usage", lower):
        return {"question": f"How do you configure and use {clean}?", "type": "procedural"}
    if re.search(r"what is|overview|architecture|concept|introduction|about", lower):
        return {"question": f"What is the core function and purpose of {clean}?", "type": "conceptual"}
    if re.search(r"limit|pricing|quota|rate|parameter|spec|option|feature", lower):
        return {"question": f"What are the key specifications and constraints for {clean}?", "type": "constraint_spec"}

    return {"question": f"What details are specified regarding {clean}?", "type": "factual"}


def build_export_formats(question: str, ideal_answer: str, context_quote: str, system_prompt: str) -> Dict[str, Any]:
    clean_q = question.rstrip("?")
    rejected = f"Based on general knowledge, {clean_q} can be handled using standard tools depending on configuration."
    return {
        "openai": {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
                {"role": "assistant", "content": ideal_answer},
            ]
        },
        "alpaca": {
            "instruction": question,
            "input": context_quote,
            "output": ideal_answer,
        },
        "sharegpt": {
            "conversations": [
                {"from": "system", "value": system_prompt},
                {"from": "human", "value": question},
                {"from": "gpt", "value": ideal_answer},
            ]
        },
        "dpo": {
            "prompt": question,
            "chosen": ideal_answer,
            "rejected": rejected,
        },
    }


def extract_sections_from_markdown(markdown_content: str) -> List[Dict[str, str]]:
    sections = []
    current_heading = ""
    current_lines: List[str] = []

    for line in markdown_content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            if current_heading:
                body_text = " ".join(current_lines).strip()
                if len(body_text) >= 40:
                    sections.append({"heading": current_heading, "body": body_text})
            current_heading = stripped.lstrip("#").strip()
            current_lines = []
            continue
        if current_heading:
            current_lines.append(stripped)

    if current_heading:
        body_text = " ".join(current_lines).strip()
        if len(body_text) >= 40:
            sections.append({"heading": current_heading, "body": body_text})

    if sections:
        return sections

    paragraphs = [
        " ".join(block.split())
        for block in markdown_content.split("\n\n")
        if len(" ".join(block.split())) >= 40
    ]
    return [{"heading": f"Section {idx + 1}", "body": paragraph} for idx, paragraph in enumerate(paragraphs)]
