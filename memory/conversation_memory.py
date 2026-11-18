
class ConversationMemory:

    def __init__(self, max_turns=5):
        self.max_turns = max_turns
        self.history = []

    def add_turn(self, question, answer, sources=None):

        self.history.append({
            "question": question,
            "answer": answer,
            "sources": sources or [],
        })

        # Keep only the most recent conversations
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def get_history(self):
        return self.history.copy()

    def get_formatted_history(self):

        if not self.history:
            return "No previous conversation."

        formatted = []

        for turn in self.history:
            formatted.append(
                f"User: {turn['question']}\n"
                f"Assistant: {turn['answer']}"
            )

        return "\n\n".join(formatted)

    def clear(self):
        self.history.clear()

    def is_empty(self):
        return len(self.history) == 0

    def show_history(self):

        if self.is_empty():
            print("\nNo conversation history available.")
            return

        print("\n========== CHAT HISTORY ==========")

        for index, turn in enumerate(self.history, start=1):

            print(f"\nConversation {index}")
            print("User:", turn["question"])
            print("Assistant:", turn["answer"])

        print("\n==================================")
