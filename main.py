from orchestrator import Orchestrator


def main():
    print("=" * 60)
    print("  Agentic AI Assistant")
    print("  Type your goal. Type 'quit' to exit.")
    print("=" * 60)

    orchestrator = Orchestrator()

    while True:
        print()
        user_goal = input("Your goal: ").strip()

        if not user_goal:
            continue

        if user_goal.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        print("\nWorking on it...\n")
        result = orchestrator.run(user_goal)
        print("\n" + "-" * 60)
        print(result)
        print("-" * 60)


if __name__ == "__main__":
    main()
