"""
Real LLM tool-calling experiment.

Flow:

    Student learning state
            ↓
          LLM
            ↓
      tool selection
            ↓
      Python tool execution
            ↓
        tool result
            ↓
          LLM
            ↓
    final recommendation

This file is intentionally isolated from LangGraph.
Once this works reliably, the tool-calling loop will be
integrated into the LangGraph workflow.
"""

from __future__ import annotations

import ast

from langchain_core.messages import HumanMessage, ToolMessage

from app.agents.llm import get_llm
from app.agents.tools import AVAILABLE_TOOLS


def normalize_tool_arguments(tool_name: str, arguments: dict) -> dict:
    """
    Normalize arguments produced by local LLMs before they reach
    the strongly typed Python tools.

    Some local models occasionally return structured values such
    as dictionaries as strings.

    Example:

        "{'Operating Systems': 52.0, 'React Hooks': 81.0}"

    should become:

        {
            "Operating Systems": 52.0,
            "React Hooks": 81.0,
        }

    We keep the actual tools strongly typed and perform normalization
    at the LLM/tool boundary instead.
    """

    args = dict(arguments)

    if tool_name == "summarize_weak_topics":
        value = args.get("retention_by_topic")

        if isinstance(value, str):
            try:
                parsed_value = ast.literal_eval(value)
            except (ValueError, SyntaxError) as exc:
                raise ValueError(
                    "Could not parse retention_by_topic tool argument: "
                    f"{value!r}"
                ) from exc

            if not isinstance(parsed_value, dict):
                raise ValueError(
                    "retention_by_topic must evaluate to a dictionary."
                )

            args["retention_by_topic"] = parsed_value

    return args


def run_tool_calling_experiment():
    """
    Run one complete LLM → tool → result → LLM cycle.
    """

    # Use a low temperature because this is structured decision-making,
    # not creative generation.
    llm = get_llm(temperature=0.0)

    # Make the StudyMentor tools available to the LLM.
    llm_with_tools = llm.bind_tools(AVAILABLE_TOOLS)

    # Fast lookup when the model requests a particular tool.
    tool_map = {
        tool.name: tool
        for tool in AVAILABLE_TOOLS
    }

    learning_state = {
        "weak_topics": {
            "Operating Systems": 52.0,
            "React Hooks": 81.0,
        },
        "due_questions": 4,
        "recent_reviews": [
            {"rating": "again"},
            {"rating": "hard"},
            {"rating": "again"},
        ],
    }

    prompt = f"""
You are StudyMentor's learning assistant.

You have access to tools that perform reliable application logic.

IMPORTANT:
- Use the available tools when they provide information you need.
- Do not calculate or guess tool results yourself.
- Use compute_next_review to determine when the student should
  review a question again.

The student just reviewed a question with:

rating: "good"
review_count: 2
difficulty: 2.5

Call the compute_next_review tool using exactly those values.

After receiving the tool result, briefly explain the recommended
next-review date to the student.
"""

    print("=== REAL LLM TOOL CALLING ===")

    # ---------------------------------------------------------------
    # STEP 1: LLM decides whether a tool is needed.
    # ---------------------------------------------------------------

    response = llm_with_tools.invoke(
        [
            HumanMessage(content=prompt)
        ]
    )

    print("\n=== MODEL RESPONSE ===")
    print(response.content)

    # ---------------------------------------------------------------
    # STEP 2: Inspect tool calls requested by the LLM.
    # ---------------------------------------------------------------

    print("\n=== TOOL CALLS REQUESTED BY MODEL ===")

    if not response.tool_calls:
        print("No tool calls were requested by the model.")
        return

    for call in response.tool_calls:
        print("Tool:", call["name"])
        print("Arguments:", call["args"])

    # ---------------------------------------------------------------
    # STEP 3: Execute each requested tool.
    # ---------------------------------------------------------------

    print("\n=== EXECUTING TOOLS ===")

    tool_messages: list[ToolMessage] = []

    for call in response.tool_calls:
        tool_name = call["name"]

        tool = tool_map.get(tool_name)

        if tool is None:
            raise RuntimeError(
                f"Model requested unavailable tool: {tool_name}"
            )

        # Normalize model-produced arguments before passing them
        # into the strongly typed Python tool.
        normalized_args = normalize_tool_arguments(
            tool_name,
            call["args"],
        )

        print(f"\nExecuting {tool_name} with:")
        print(normalized_args)

        # Actual Python function/tool execution.
        result = tool.invoke(normalized_args)

        print(f"\n{tool_name} -> {result}")

        # Convert the Python result into a ToolMessage so the LLM
        # can receive the result and continue reasoning.
        tool_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=call["id"],
            )
        )

    # ---------------------------------------------------------------
    # STEP 4: Send the tool result back to the LLM.
    # ---------------------------------------------------------------

    print("\n=== LLM RECEIVES TOOL RESULT ===")

    final_response = llm_with_tools.invoke(
        [
            HumanMessage(content=prompt),
            response,
            *tool_messages,
        ]
    )

    # ---------------------------------------------------------------
    # STEP 5: Final agent response.
    # ---------------------------------------------------------------

    print("\n=== FINAL AGENT RESPONSE ===")
    print(final_response.content)


if __name__ == "__main__":
    run_tool_calling_experiment()