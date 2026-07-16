from .calculator import execute as calculator
from .time_tool import execute as time_tool
from .weather import execute as weather
from .bmi_calculator import execute as bmi_calculator
from .book_search import execute as book_search
from .currency_converter import execute as currency_converter
from .movie_search import execute as movie_search
from .music_search import execute as music_search

TOOLS = {
    "calculator": calculator,
    "time": time_tool,
    "weather": weather,
    "currency_converter": currency_converter,
    "bmi_calculator": bmi_calculator,
    "movie_search": movie_search,
    "book_search": book_search,
    "music_search": music_search,
}

def execute_tool(tool_name: str, arguments: dict):
    tool = TOOLS.get(tool_name)
    
    if tool is None:
        return f"Unknown tool: {tool_name}"
    return tool(arguments)
def list_table():
    return list(TOOLS.keys())

if __name__ == "__main__":
    print("Registered tools\n")
    print(
        execute_tool(
            "calculator",
            {
                "expression": "25*10"
            }
        )
    )
    print("\n")
    
    print(
        execute_tool(
            "time",
            {}
        )
    )
    print(
        execute_tool(
            "weather",
            {
                "city":"delhi"
            }
        )
    )