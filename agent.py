from LLM import chat
from memory import load_memory, save_memory
from prompts import SYSTEM_PROMPT
from parser import parse_tool_call
import json
import importlib.util
import os
from types import ModuleType
from typing import Any

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "tools")


def _load_tool_module(module_name: str, file_name: str) -> ModuleType:
    file_path = os.path.join(TOOLS_DIR, file_name)
    spec = importlib.util.spec_from_file_location(module_name, file_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load tool module: {module_name}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

calculator_tool = _load_tool_module("calculator_tool", "calculator.py")
time_tool = _load_tool_module("time_tool", "time_tool.py")
weather = _load_tool_module("weather_tool", "weather.py")
pdf_tool = _load_tool_module("pdf_tool", "pdf_tool.py")
currency_tool = _load_tool_module("currency_tool", "currency_converter.py")
bmi_tool = _load_tool_module("bmi_tool", "bmi_calculator.py")
movie_tool = _load_tool_module("movie_tool", "movie_search.py")
book_tool = _load_tool_module("book_tool", "book_search.py")
music_tool = _load_tool_module("music_tool", "music_search.py")


def _execute_tool(tool_name: str, arguments: dict[str, Any]):
    if tool_name == "calculator":
        expression = arguments.get("expression", "")

        try:
            return calculator_tool.calculator(expression)
        except Exception as e:
            return f"Calculator Error: {e}"

    if tool_name == "time":
        try:
            return time_tool.execute(arguments)
        except Exception as e:
            return f"Time Error: {e}"

    if tool_name == "weather":
        try:
            return weather.execute(arguments)
        except Exception as e:
            return f"Weather Error: {e}"

    if tool_name == "pdf_tool":
        try:
            return pdf_tool.execute(arguments)
        except Exception as e:
            return f"PDF Tool Error: {e}"

    if tool_name == "currency_converter":
        try:
            return currency_tool.execute(arguments)
        except Exception as e:
            return f"Currency Converter Error: {e}"

    if tool_name == "bmi_calculator":
        try:
            return bmi_tool.execute(arguments)
        except Exception as e:
            return f"BMI Calculator Error: {e}"

    if tool_name == "movie_search":
        try:
            return movie_tool.execute(arguments)
        except Exception as e:
            return f"Movie Search Error: {e}"

    if tool_name == "book_search":
        try:
            return book_tool.execute(arguments)
        except Exception as e:
            return f"Book Search Error: {e}"

    if tool_name == "music_search":
        try:
            return music_tool.execute(arguments)
        except Exception as e:
            return f"Music Search Error: {e}"

    return "Unknown tool."


class Agent:

    def run(self, user_input: str, attachments: list[dict[str, Any]] | None = None) -> str:

        # Load memory
        memory = load_memory()

        # First conversation (tool detection)
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        messages.extend(memory)

        if attachments:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Uploaded files available for safe tool use only. "
                        "Use the provided paths exactly as shown and never invent a file path.\n"
                        + json.dumps(attachments, indent=2, ensure_ascii=False)
                    ),
                }
            )

        messages.append({
            "role": "user",
            "content": user_input
        })

        # First LLM response
        llm_response = chat(messages)

        # Check if a tool is requested
        tool_request = parse_tool_call(llm_response)

        # No tool required
        if tool_request is None:

            memory.append({
                "role": "user",
                "content": user_input
            })

            memory.append({
                "role": "assistant",
                "content": llm_response
            })

            save_memory(memory)

            return llm_response

        print("Tool Requested")

        # Execute tool
        tool_name = tool_request.get("tool")
        arguments = {
            key: value
            for key, value in tool_request.items()
            if key != "tool"
        }

        tool_result = _execute_tool(tool_name, arguments)

        print("Observation:", tool_result)

        # Second conversation (final answer)
        final_messages = [
            {
                "role": "system",
                "content": """
You are a helpful AI assistant.

A tool has already executed.

DO NOT call any tool again.

DO NOT output JSON.

Use the tool result to answer the user's original question naturally.

Example:

User:
What is 7*7?

Tool Result:
49

Assistant:
The answer is 49.
"""
            },
            {
                "role": "user",
                "content": user_input
            },
            {
                "role": "assistant",
                "content": f"Tool Name: {tool_name}\nTool Result: {tool_result}"
            }
        ]

        final_response = chat(final_messages)

        # Save memory
        memory.append({
            "role": "user",
            "content": user_input
        })

        memory.append({
            "role": "assistant",
            "content": final_response
        })

        save_memory(memory)

        return final_response