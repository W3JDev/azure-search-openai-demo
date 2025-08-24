from __future__ import annotations

import json
import os
from dataclasses import dataclass

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from openai import AsyncOpenAI


@dataclass
class ValidationResult:
    """Outcome from validating an answer."""

    sentiment: str
    score: float


async def validate(question: str, answer: str, context: str) -> ValidationResult:
    """Validate an answer using Azure AI services.

    The answer sentiment is evaluated with the Text Analytics API and the
    quality/compliance score is produced by an Azure OpenAI evaluation.
    """

    endpoint = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT")
    key = os.getenv("AZURE_TEXT_ANALYTICS_KEY")

    ta_client: TextAnalyticsClient | None = None
    if endpoint and key:
        ta_client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    sentiment = "unknown"
    if ta_client:
        sentiment_result = ta_client.analyze_sentiment([answer])
        sentiment = sentiment_result[0].sentiment

    openai_client = AsyncOpenAI()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a system that evaluates the quality and compliance "
                "of answers. Return a JSON object with a numeric 'score' field "
                "between 0 and 1 indicating the overall quality."
            ),
        },
        {
            "role": "user",
            "content": f"Question: {question}\nContext: {context}\nAnswer: {answer}",
        },
    ]

    model = os.getenv("AZURE_OPENAI_VALIDATION_MODEL", "gpt-4o-mini")
    response = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"},
    )

    score = 0.0
    try:
        score_data = json.loads(response.choices[0].message.content)
        score = float(score_data.get("score", 0))
    except Exception:
        pass

    return ValidationResult(sentiment=sentiment, score=score)
