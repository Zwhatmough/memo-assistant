"""Thin wrapper around the Anthropic Claude API.

One function: call_llm(). It sends a prompt and a pydantic schema to
Claude via tool use, and returns validated structured data. Every call
is logged (tokens, cost, duration) for the run log.

Why tool use instead of "please return JSON"?
- Tool use forces Claude to return data matching the schema.
- "Please return JSON" is a suggestion the model can ignore.
- Tool use failures are parse errors we can catch, not silent garbage.

Model split (decided Milestone 2):
- claude-haiku-4-5-20251001: extraction tasks (structured reading)
- claude-sonnet-5: classification and memo generation (analytical judgement)
"""

import time
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

# Pricing per million tokens (as of Jul 2026)
MODEL_PRICING = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-sonnet-5": {"input": 3.00, "output": 15.00},
}
# Fallback for unknown models
DEFAULT_PRICING = {"input": 3.00, "output": 15.00}

# Default models for each task type
EXTRACTION_MODEL = "claude-haiku-4-5-20251001"
ANALYSIS_MODEL = "claude-sonnet-5"


def get_pricing(model: str) -> dict:
    """Get per-million-token pricing for a model."""
    return MODEL_PRICING.get(model, DEFAULT_PRICING)


def estimate_cost(n_calls: int, avg_input_tokens: int, avg_output_tokens: int,
                  model: str) -> float:
    """Estimate total USD cost for a batch of API calls."""
    pricing = get_pricing(model)
    input_cost = (n_calls * avg_input_tokens / 1_000_000) * pricing["input"]
    output_cost = (n_calls * avg_output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def _schema_to_tool(name: str, schema_class: type[BaseModel]) -> dict:
    """Convert a pydantic model into a Claude tool definition."""
    return {
        "name": name,
        "description": f"Return extracted data as {name}",
        "input_schema": schema_class.model_json_schema(),
    }


def call_llm(
    prompt: str,
    schema_class: type[T],
    tool_name: str = "extract",
    model: str = EXTRACTION_MODEL,
    max_tokens: int = 4096,
    log: list[dict] | None = None,
) -> T:
    """Send a prompt to Claude and get back validated structured data.

    Args:
        prompt: The full prompt text (system + user content combined
                into the user message for simplicity).
        schema_class: The pydantic model the response must match.
        tool_name: Name for the tool definition.
        model: Claude model to use.
        max_tokens: Max tokens in the response.
        log: If provided, append a call record for the run log.

    Returns:
        An instance of schema_class, validated by pydantic.

    Raises:
        ValidationError: If both attempts fail schema validation.
        anthropic.APIError: If the API call itself fails.
    """
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    tool = _schema_to_tool(tool_name, schema_class)
    pricing = get_pricing(model)

    messages = [{"role": "user", "content": prompt}]

    for attempt in range(2):
        start = time.time()

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name},
            messages=messages,
        )

        duration = time.time() - start

        # Find the tool use block in the response
        tool_block = None
        for block in response.content:
            if block.type == "tool_use":
                tool_block = block
                break

        if tool_block is None:
            raise ValueError(f"No tool use in response (attempt {attempt + 1})")

        # Log the call
        usage = response.usage
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]

        record = {
            "model": model,
            "tool_name": tool_name,
            "attempt": attempt + 1,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cost_usd": round(input_cost + output_cost, 6),
            "duration_s": round(duration, 2),
            "success": False,
            "error": None,
        }

        # Validate against the pydantic schema
        try:
            result = schema_class.model_validate(tool_block.input)
            record["success"] = True
            if log is not None:
                log.append(record)
            return result

        except ValidationError as e:
            record["error"] = str(e)
            if log is not None:
                log.append(record)

            if attempt == 0:
                # Retry: send the error back so Claude can fix it
                messages = [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response.content},
                    {
                        "role": "user",
                        "content": f"Validation error: {e}. Please fix and try again.",
                    },
                ]
            else:
                raise  # second attempt failed — let the caller handle it
