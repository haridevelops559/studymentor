"""
LangGraph Tool-Calling Agent.

Concepts demonstrated:
- LLM tool binding
- ToolNode
- tools_condition
- Agent -> Tool -> Agent loop
- ToolMessage
- LangGraph state
- Multiple tools selected by the LLM

This is intentionally isolated from the main adaptive-learning graph.
Once this works, it can be integrated into the main StudyMentor graph.
"""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.llm import get_llm
from app.agents.tools import AVAILABLE_TOOLS


class ToolAgentState(dict):
    """
    State passed through the tool-calling graph.

    add_messages allows LangGraph to append:
        HumanMessage
        AIMessage
        ToolMessage
        AIMessage
    instead of replacing the previous messages.
    """

    messages: Annotated[list[BaseMessage], add_messages]


def build_tool_agent_graph():
    """
    Build:

        START
          |
          v
        agent
          |
          | tool call?
          |
       yes|       no
          v        v
       tools      END
          |
          v
        agent
          |
          ...
    """

    llm = get_llm()

    tools: list[BaseTool] = AVAILABLE_TOOLS

    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: ToolAgentState) -> dict:
        """
        Ask the LLM what to do next.

        The LLM may:
        - answer directly
        - request one or more tools

        ToolNode executes requested tools separately.
        """

        response = llm_with_tools.invoke(state["messages"])

        return {
            "messages": [response],
        }

    graph = StateGraph(ToolAgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")

    # If the LLM requested a tool:
    #     agent -> tools
    #
    # Otherwise:
    #     agent -> END
    graph.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    # After ToolNode executes, return the tool result to the LLM.
    graph.add_edge("tools", "agent")

    return graph.compile()


def run_summary_tool_test():
    """
    Test 1:
    LLM should select summarize_weak_topics.
    """

    app = build_tool_agent_graph()

    prompt = """
You are StudyMentor's learning assistant.

The student's retention data is:

Operating Systems: 52.0%
React Hooks: 81.0%

Use the summarize_weak_topics tool to identify which topic
the student should focus on next.

After receiving the tool result, give a concise recommendation.
"""

    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=prompt)
            ]
        }
    )

    print("\n=== SUMMARY TOOL TEST ===")

    for message in result["messages"]:
        print(f"\n[{message.__class__.__name__}]")
        print(message.content)

        if getattr(message, "tool_calls", None):
            print("Tool calls:")
            for call in message.tool_calls:
                print(
                    f"  - {call['name']}: {call['args']}"
                )


def run_review_tool_test():
    """
    Test 2:
    LLM should select compute_next_review.
    """

    app = build_tool_agent_graph()

    prompt = """
You are StudyMentor's learning assistant.

A student just reviewed a question.

Review rating: good
Review count: 2
Current difficulty: 2.5

Use the compute_next_review tool to determine the next review date.

Do not calculate the date yourself.

After receiving the tool result, briefly explain the recommendation.
"""

    result = app.invoke(
        {
            "messages": [
                HumanMessage(content=prompt)
            ]
        }
    )

    print("\n=== NEXT REVIEW TOOL TEST ===")

    for message in result["messages"]:
        print(f"\n[{message.__class__.__name__}]")
        print(message.content)

        if getattr(message, "tool_calls", None):
            print("Tool calls:")
            for call in message.tool_calls:
                print(
                    f"  - {call['name']}: {call['args']}"
                )


if __name__ == "__main__":
    print("======================================")
    print("LANGGRAPH TOOL-CALLING AGENT")
    print("======================================")

    run_summary_tool_test()
    run_review_tool_test()