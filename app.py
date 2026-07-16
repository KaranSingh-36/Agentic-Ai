from agent import Agent


def main():
    print("=" * 60)
    print("AI AGENT".center(60))
    print("=" * 60)
    print("Type 'exit' to quit.\n")

    agent = Agent()

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        try:
            response = agent.run(user_input)
            print(f"\nAgent: {response}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()