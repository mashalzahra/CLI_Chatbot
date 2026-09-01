"""
Multi-provider CLI chatbot with sliding-window memory and live cost tracking.
Run with: python -m chatbot.cli
"""
import argparse
from dotenv import load_dotenv
load_dotenv()  # reads .env file so GEMINI_API_KEY is available
from bot.memory import ConversationManager
from bot.providers import call_model

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
}

HELP_TEXT = """
Commands:
  /clear               Clear conversation history
  /save <file>         Save conversation history to a JSON file (default: conversation.json)
  /load <file>         Load conversation history from a JSON file
  /quit                Exit
"""


def run(provider: str, system_prompt: str, max_tokens: int, input_fn=input, print_fn=print):
    """
    Core REPL loop. input_fn/print_fn are injectable so tests can run
    without touching real stdin/stdout.
    """
    model = DEFAULT_MODELS[provider]
    memory = ConversationManager(system_prompt=system_prompt, max_tokens=max_tokens)
   

    print_fn(f"Chatting with {provider} ({model}). Type /help for commands.")

    while True:
        try:
            user_input = input_fn("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print_fn("\nbye.")
            return

        if not user_input:
            continue
        if user_input == "/quit":
            return
        if user_input == "/help":
            print_fn(HELP_TEXT)
            continue
        if user_input == "/clear":
            memory.clear()
            print_fn("Conversation cleared.")
            continue
        if user_input.startswith("/save"):
            parts = user_input.split(maxsplit=1)
            path = parts[1] if len(parts) == 2 else "conversation.json"
            memory.save(path)
            print_fn(f"Saved to {path}")
            continue
        if user_input.startswith("/load"):
            parts = user_input.split(maxsplit=1)
            path = parts[1] if len(parts) == 2 else "conversation.json"
            memory.load(path)
            print_fn(f"Loaded from {path}")
            continue

        memory.add("user", user_input)
        reply, usage = call_model(provider, model, memory.messages)
        memory.add("assistant", reply)
        print_fn(f"\n{provider}> {reply}")



def main():
    parser = argparse.ArgumentParser(description="Gemini CLI chatbot with memory")
    parser.add_argument("--provider", default="gemini", choices=DEFAULT_MODELS.keys())
    parser.add_argument("--persona", default="You are a helpful, concise assistant.")
    parser.add_argument(
        "--max-tokens", type=int, default=3000,
        help="Sliding-window token budget before old messages get dropped"
    )
    args = parser.parse_args()
    run(args.provider, args.persona, args.max_tokens)


if __name__ == "__main__":
    main()
