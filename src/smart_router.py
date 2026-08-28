"""
Smart Intent Router — Odysseus / JARVIS
========================================
Analyzes the user's prompt and routes it to the most suitable model:

  - CODE / PROGRAMMING   → qwen2.5-coder:7b   (deep accuracy)
  - REASONING / MATH     → deepseek-r1:8b      (chain-of-thought)
  - GENERAL / FAST CHAT  → gemini / groq / llama3.2  (instant reply)

The router is purely keyword + pattern based — zero extra LLM call overhead.
It runs in microseconds before the request is forwarded to any provider.
"""

import re
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model ID constants — override via environment variables if needed
# ---------------------------------------------------------------------------
_MODEL_FAST      = os.getenv("ROUTER_MODEL_FAST",      "llama3.2:1b")
_MODEL_CODE      = os.getenv("ROUTER_MODEL_CODE",      "qwen2.5-coder:7b")
_MODEL_REASONING = os.getenv("ROUTER_MODEL_REASONING", "deepseek-r1:7b")

# Standard endpoint URLs
_OLLAMA_ENDPOINT = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
_GEMINI_ENDPOINT = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
_GEMINI_KEY      = os.getenv("GEMINI_API_KEY", "")
_GROQ_ENDPOINT   = os.getenv("GROQ_BASE_URL",   "https://api.groq.com/openai/v1")

# ---------------------------------------------------------------------------
# Intent pattern banks
# ---------------------------------------------------------------------------

# Coding / Programming triggers
_CODE_PATTERNS = re.compile(
    r"""
    \b(
        code|coding|program|programming|script|function|class|method|
        bug|debug|error|exception|traceback|fix|refactor|optimize|
        algorithm|data\s*structure|api|rest|graphql|endpoint|
        python|javascript|typescript|java|c\+\+|rust|go|golang|
        html|css|sql|bash|shell|powershell|
        git|github|docker|kubernetes|linux|
        loop|recursion|regex|json|yaml|xml|csv|
        import|library|package|module|pip|npm|
        flask|fastapi|django|react|vue|next\.?js|
        array|list|dict|dictionary|string|integer|boolean|
        machine\s*learning|neural|train|model|dataset|
        test|unit\s*test|pytest|assert|mock|
        file|files|folder|folders|directory|directories|downloads|desktop|document|documents|path|scan|count
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Reasoning / Math / Logic triggers
_REASONING_PATTERNS = re.compile(
    r"""
    \b(
        math|mathematics|calculus|algebra|geometry|trigonometry|
        solve|equation|formula|proof|theorem|calculate|computation|
        probability|statistics|integral|derivative|matrix|vector|
        logic|reasoning|step\s*by\s*step|chain\s*of\s*thought|
        complex|analyze|analysis|hypothesis|compare|contrast|
        philosophy|ethics|debate|argument|fallacy|paradox|
        strategy|planning|decision|optimize|trade.?off|
        explain\s+why|explain\s+how|what\s+causes|what\s+happens\s+if
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# General / Casual / Fast reply triggers
_FAST_PATTERNS = re.compile(
    r"""
    \b(
        hi|hello|hey|thanks|thank\s*you|good\s*morning|good\s*night|
        what\s+is|who\s+is|where\s+is|when\s+is|tell\s+me|
        list|summarize|summary|idea|suggest|recommend|write|create|
        translate|weather|news|fact|trivia|joke|story|
        capital|country|city|history|culture|language|
        recipe|food|travel|movie|music|sport|game|book
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class PromptIntent:
    CODE      = "code"
    REASONING = "reasoning"
    GENERAL   = "general"


def detect_intent(prompt: str) -> str:
    """
    Detect the intent of a user prompt by weighing coding vs reasoning signals.
    """
    if not prompt or not isinstance(prompt, str):
        return PromptIntent.GENERAL

    text = prompt.strip()

    # Score each intent by number of keyword matches
    code_score      = len(_CODE_PATTERNS.findall(text))
    reasoning_score = len(_REASONING_PATTERNS.findall(text))

    # If there is a stronger math/reasoning signal, route to Reasoning
    if reasoning_score > code_score:
        return PromptIntent.REASONING

    # If coding signal is stronger, route to Code
    if code_score > reasoning_score:
        return PromptIntent.CODE

    # Tie breakers
    if code_score >= 1:
        return PromptIntent.CODE
    if reasoning_score >= 1:
        return PromptIntent.REASONING

    return PromptIntent.GENERAL


def route_prompt(prompt: str, user_groq_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Route prompt automatically to the optimal model and endpoint.

    Returns:
    {
        "intent": "code" | "reasoning" | "general",
        "model": "<model_name>",
        "endpoint_url": "<http...>",
        "headers": {...},
        "reason": "<user-facing description>"
    }
    """
    intent = detect_intent(prompt)
    groq_key = (user_groq_key or os.getenv("GROQ_API_KEY", "")).strip()

    if intent == PromptIntent.CODE:
        return {
            "intent": intent,
            "model": _MODEL_CODE,
            "endpoint_url": _OLLAMA_ENDPOINT,
            "headers": {},
            "reason": "[CODE] Coding task detected -> Routed to Local Qwen 2.5 Coder 7B (Fast & Accurate)",
        }
    elif intent == PromptIntent.REASONING:
        return {
            "intent": intent,
            "model": _MODEL_REASONING,
            "endpoint_url": _OLLAMA_ENDPOINT,
            "headers": {},
            "reason": "[REASONING] Deep reasoning detected -> Routed to Local DeepSeek R1 7B (Chain-of-Thought)",
        }
    else:
        # 100% Local Offline General Chat via Llama 3.2
        return {
            "intent": intent,
            "model": _MODEL_FAST,
            "endpoint_url": _OLLAMA_ENDPOINT,
            "headers": {},
            "reason": "[FAST] General conversation -> Routed to Local Llama 3.2 (100% Offline & Unlimited)",
        }

    return {
        "intent":   intent,
        "model":    model,
        "reason":   reason,
        "fallback": fallback,
    }


# ---------------------------------------------------------------------------
# Quick self-test (run with: python -m src.smart_router)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_prompts = [
        "Write a Python function to sort a list using merge sort",
        "Hey! What is the capital of France?",
        "Solve this differential equation step by step: dy/dx = 3x^2",
        "Debug this JavaScript error: TypeError: Cannot read property of undefined",
        "Tell me a fun fact about space",
        "Explain why quicksort is faster than bubble sort in average cases",
        "How do I make a pasta carbonara?",
        "Refactor this Flask API to use async/await",
    ]
    print("\nSmart Router -- Intent Detection Test\n" + "=" * 50)
    for p in test_prompts:
        result = route_prompt(p)
        print(f"\nPrompt : {p[:70]}")
        print(f"  Intent : {result['intent'].upper()}")
        print(f"  Model  : {result['model']}")
        print(f"  Reason : {result['reason']}")
