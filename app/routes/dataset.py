import re

import trafilatura
from fastapi import APIRouter
from selectolax.parser import HTMLParser

from ..schemas import DatasetRequest
from ..services.dataset import (
    ENTITY_REGEX,
    build_export_formats,
    classify_complexity,
    extract_sections_from_markdown,
    generate_question,
)
from ..services.fetch import fetch_html


router = APIRouter()


@router.post("/dataset")
async def dataset_endpoint(payload: DatasetRequest):
    target_url = str(payload.url)
    html_text = await fetch_html(target_url, payload.impersonate)
    tree = HTMLParser(html_text)
    markdown_content = (
        trafilatura.extract(
            html_text,
            output_format="markdown",
            include_links=False,
            include_images=False,
        )
        or ""
    )

    title_tag = tree.css_first("title")
    title = title_tag.text().strip() if title_tag else "Documentation Page"
    system_prompt = f"You are an expert technical assistant trained on {title}. Provide accurate, structured responses."

    for noise in tree.css("nav, header, footer, aside, script, style, iframe, .sidebar, .comments"):
        noise.decompose()

    dataset = []
    seen_questions = set()
    headings = tree.css("h1, h2, h3, h4, h5")

    for heading in headings:
        heading_text = heading.text().strip()
        if not heading_text or len(heading_text) < 3 or heading_text in seen_questions:
            continue

        body_text = ""
        current = heading.next
        step = 0
        while current and step < 10:
            if current.tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                break
            text = current.text().strip()
            if len(text) > 20:
                body_text += " " + text
            current = current.next
            step += 1

        body_text = body_text.strip()
        if len(body_text) >= 40:
            seen_questions.add(heading_text)
            q_info = generate_question(heading_text)
            question = q_info["question"]
            context_quote = body_text[:220] + "..." if len(body_text) > 220 else body_text
            ideal_answer = body_text[:600] + "..." if len(body_text) > 600 else body_text
            entities = list(set(ENTITY_REGEX.findall(ideal_answer)))[:5]
            complexity = classify_complexity(ideal_answer)

            dataset.append(
                {
                    "id": f"pair_{len(dataset) + 1}",
                    "question": question,
                    "context_quote": context_quote,
                    "ideal_answer": ideal_answer,
                    "confidence_score": 0.94,
                    "taxonomy": {
                        "question_type": q_info["type"],
                        "complexity_level": complexity,
                        "entities": entities,
                    },
                    "metrics": {
                        "prompt_tokens_est": max(1, len(question) // 4),
                        "completion_tokens_est": max(1, len(ideal_answer) // 4),
                    },
                    "formats": build_export_formats(question, ideal_answer, context_quote, system_prompt),
                }
            )

    if not dataset and markdown_content:
        for section in extract_sections_from_markdown(markdown_content):
            heading_text = section["heading"]
            if heading_text in seen_questions:
                continue

            seen_questions.add(heading_text)
            q_info = generate_question(heading_text)
            question = q_info["question"]
            body_text = section["body"]
            context_quote = body_text[:220] + "..." if len(body_text) > 220 else body_text
            ideal_answer = body_text[:600] + "..." if len(body_text) > 600 else body_text
            entities = list(set(ENTITY_REGEX.findall(ideal_answer)))[:5]
            complexity = classify_complexity(ideal_answer)

            dataset.append(
                {
                    "id": f"pair_{len(dataset) + 1}",
                    "question": question,
                    "context_quote": context_quote,
                    "ideal_answer": ideal_answer,
                    "confidence_score": 0.94,
                    "taxonomy": {
                        "question_type": q_info["type"],
                        "complexity_level": complexity,
                        "entities": entities,
                    },
                    "metrics": {
                        "prompt_tokens_est": max(1, len(question) // 4),
                        "completion_tokens_est": max(1, len(ideal_answer) // 4),
                    },
                    "formats": build_export_formats(question, ideal_answer, context_quote, system_prompt),
                }
            )

    total_tokens = sum(item["metrics"]["prompt_tokens_est"] + item["metrics"]["completion_tokens_est"] for item in dataset)
    all_words = re.findall(r"\w+", " ".join(item["question"] + " " + item["ideal_answer"] for item in dataset).lower())
    ttr = round(len(set(all_words)) / len(all_words), 2) if all_words else 0.0

    return {
        "success": True,
        "url": target_url,
        "total_pairs_generated": len(dataset),
        "dataset_health": {
            "quality_score": min(98, max(60, 70 + int(ttr * 15) + (5 if len(dataset) >= 5 else 0))),
            "vocabulary_diversity_ratio": ttr,
            "total_dataset_tokens": total_tokens,
        },
        "exports": {
            "openai_chatml": [item["formats"]["openai"] for item in dataset],
            "dpo_preference": [item["formats"]["dpo"] for item in dataset],
        },
        "dataset": dataset,
    }
