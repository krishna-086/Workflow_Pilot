import logging
from typing import Optional
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from config import settings, GROQ_MODEL, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Task type definitions
REASONING_TASKS = {
    "planning",
    "decision_making",
    "error_analysis",
    "complex_reasoning"
}

EXTRACTION_TASKS = {
    "action_item_extraction",
    "owner_identification",
    "classification",
    "summarization",
    "sentiment"
}

# LLM instances
heavy_llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=settings.groq_api_key,
    temperature=0.1
)

fast_llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=settings.google_api_key,
    temperature=0.1
)


def get_llm(task_type: str) -> BaseChatModel:
    """
    Route to the appropriate LLM based on task type.

    Args:
        task_type: Type of task (e.g., "planning", "summarization")

    Returns:
        BaseChatModel instance
    """
    if not settings.llm_routing_enabled:
        logger.info(f"LLM routing disabled, using heavy_llm for task: {task_type}")
        return heavy_llm

    if task_type in EXTRACTION_TASKS:
        logger.info(f"Routing task '{task_type}' to fast_llm (Gemini)")
        return fast_llm
    else:
        logger.info(f"Routing task '{task_type}' to heavy_llm (Groq)")
        return heavy_llm


async def call_llm(
    task_type: str,
    messages: list,
    structured_output: Optional[type] = None
) -> tuple[str, str, int]:
    """
    Call the appropriate LLM with fallback logic.

    Args:
        task_type: Type of task for routing
        messages: List of messages to send to the LLM
        structured_output: Optional Pydantic model for structured output

    Returns:
        Tuple of (response_content, model_name_used, approximate_token_count)
    """
    llm = get_llm(task_type)
    primary_model = GROQ_MODEL if llm == heavy_llm else GEMINI_MODEL
    fallback_llm = fast_llm if llm == heavy_llm else heavy_llm
    fallback_model = GEMINI_MODEL if fallback_llm == fast_llm else GROQ_MODEL

    try:
        # Apply structured output if requested
        if structured_output:
            llm = llm.with_structured_output(structured_output)

        # Call the LLM
        response = await llm.ainvoke(messages)

        # Extract content and estimate tokens
        if structured_output:
            response_content = response
            token_count = _estimate_tokens(str(response))
        else:
            response_content = response.content
            token_count = _estimate_tokens(response_content)

        logger.info(f"Successfully called {primary_model} for task '{task_type}'")
        return (response_content, primary_model, token_count)

    except Exception as e:
        logger.warning(f"Primary LLM ({primary_model}) failed for task '{task_type}': {e}")
        logger.info(f"Falling back to {fallback_model}")

        try:
            # Apply structured output to fallback
            if structured_output:
                fallback_llm = fallback_llm.with_structured_output(structured_output)

            # Call fallback LLM
            response = await fallback_llm.ainvoke(messages)

            # Extract content and estimate tokens
            if structured_output:
                response_content = response
                token_count = _estimate_tokens(str(response))
            else:
                response_content = response.content
                token_count = _estimate_tokens(response_content)

            logger.info(f"Successfully called fallback {fallback_model} for task '{task_type}'")
            return (response_content, fallback_model, token_count)

        except Exception as fallback_error:
            logger.error(f"Fallback LLM ({fallback_model}) also failed: {fallback_error}")
            raise Exception(f"Both primary and fallback LLMs failed for task '{task_type}'")


async def call_llm_simple(task_type: str, prompt: str) -> tuple[str, str, int]:
    """
    Convenience function for simple prompt calls.

    Args:
        task_type: Type of task for routing
        prompt: Simple string prompt

    Returns:
        Tuple of (response_content, model_name_used, approximate_token_count)
    """
    messages = [HumanMessage(content=prompt)]
    return await call_llm(task_type, messages)


def _estimate_tokens(text: str) -> int:
    """
    Rough token estimation (approximate).
    Average English text: ~4 characters per token.
    """
    return len(text) // 4
