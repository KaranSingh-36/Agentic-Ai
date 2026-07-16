import json


def parse_tool_call(response: str):
    try:
        tool_request = json.loads(response)

        if (
            isinstance(tool_request, dict)
            and "tool" in tool_request
        ):
            return tool_request

    except Exception:
        pass

    return None

if __name__ == "__main__":
    # response = "hello how are you"
    response ="""
    {
        "tool" : "calculator",
        "expression" : "25**2"
    }
    """

    results = parse_tool_call(response)
    print(results)
    