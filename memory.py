import json
import os

MEMORY_FILE = "data/memory.json"


def load_memory() -> list:
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except Exception:
        return []


def save_memory(memory: list) -> None:
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=4, ensure_ascii=False)


def add_message(memory: list, role: str, content: str) -> list:
    memory.append({
        "role": role,
        "content": content
    })
    return memory


if __name__ == "__main__":
    print("Loading memory")
    memory = load_memory()

    print(memory)

    print("\nAdding messages...")
    memory = add_message(memory, "user", "hello")
    memory = add_message(memory, "assistant", "hi how are you")

    save_memory(memory)

    print(load_memory())