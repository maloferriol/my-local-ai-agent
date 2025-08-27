"""
Core AI agent logic.
Manages the agent's behavior,
tool execution, and coordinates with the conversation manager.
"""

from typing import Iterator, Dict, Callable
from ollama import chat
from ollama._types import ChatResponse

from db.sqlite_db_manager import DatabaseManager
from utils.database_utils import DatabaseUtils
from tools.examples import get_weather, get_weather_conditions
from .conversation import ConversationManager
from cli.formatters import Formatters
from loggers.logging_config import get_logger

<<<<<<< Updated upstream
# Configure logging
logger = logging.getLogger(__name__)
=======

# Get OpenTelemetry-enabled logger
logger = get_logger(__name__)
>>>>>>> Stashed changes


class Agent:
    """
    Main AI agent class that coordinates the chat interaction, tool execution,
    and conversation management.
    """

    def __init__(self, model: str = "gpt-oss:20b", stream: bool = True):
        """
        Initialize the AI agent.

        Args:
            model: The Ollama model to use
            stream: Whether to use streaming responses
        """
        self.model = model
        self.stream = stream
        self.db_manager = DatabaseManager()
        self.conversation_manager = ConversationManager(self.db_manager)
        self.available_tools = self._get_available_tools()

        # Initialize database
        self.db_manager.connect()
        self.db_manager.create_init_tables()

        logger.info("Agent initialized with model: %s, streaming: %s", model, stream)

    def _get_available_tools(self) -> Dict[str, Callable]:
        """
        Returns a dictionary of available tools.

        Returns:
            Dictionary mapping tool names to their functions
        """
        available_tools = {
            "get_weather": get_weather,
            "get_weather_conditions": get_weather_conditions,
            "generate_random_name": DatabaseUtils.generate_random_name,
        }

        logger.debug("Available tools: %s", list(available_tools.keys()))
        return available_tools

    def _display_startup_info(self):
        """Display startup information including tools and recent conversations."""
        from rich.console import Console

        console = Console()
        console.print(Formatters.create_tools_list_section(self.available_tools))

        conversations = self.db_manager.get_conversations(limit=10)
        console.print(Formatters.create_conversation_list_section(conversations))

    def run(self):
        """Start the interactive chat loop."""
        print("Interactive chat started. Type '/quit' or Ctrl-D to exit.\n")

        # Display available tools and recent conversations
        self._display_startup_info()

        # Start the conversation loop
        self._run_conversation_loop()

    def _run_conversation_loop(self):
        """Main conversation loop."""
        from rich.console import Console

        console = Console()
        conversation_messages = []

        while True:
            try:
                user_input = self._get_user_input()
                if not user_input:
                    continue

                if self._should_exit(user_input):
                    console.print("[bold red]Bye.")
                    break

                # Process the user input
                self._process_user_input(user_input, conversation_messages)

            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

    def _get_user_input(self) -> str:
        """Get input from the user."""
        from rich.console import Console

        console = Console()
        return console.input("[bold green]You: ").strip()

    def _should_exit(self, user_input: str) -> bool:
        """Check if the user wants to exit."""
        return user_input.lower() in ("/quit", "/exit", "quit", "exit")

    def _get_conversation_id(self) -> int:
        """Get a new conversation ID."""

        if self.conversation_manager.get_current_conversation() is None:
            return self.conversation_manager.start_new_conversation()
        else:
            return self.conversation_manager.get_current_conversation().id

    def _process_user_input(self, user_input: str, conversation_messages: list):
        """Process a single user input and generate a response."""
        step = len(conversation_messages) + 1
        conversation_id = self._get_conversation_id()

        logger.info("Created new conversation with ID: %s", conversation_id)

        # Add user message to conversation
        user_message = {"role": "user", "content": user_input}
        conversation_messages.append(user_message)

        # Store user message in database
        self.db_manager.insert_message(
            conversation_id=conversation_id,
            step=step,
            role="user",
            content=user_input,
            model=self.model,
        )

        logger.debug("User: %s", user_input)

        # Generate AI response
        response_content, thinking = self._generate_ai_response(
            conversation_messages, step, conversation_id
        )

        # Store AI response in database
        self.db_manager.insert_message(
            conversation_id=conversation_id,
            step=step,
            role="assistant",
            content=response_content,
            thinking=thinking,
            model=self.model,
        )

        # Add AI response to conversation history
        self._append_assistant_message_with_thinking(
            conversation_messages, response_content, thinking
        )

        logger.debug("Conversation length: %d", len(conversation_messages))

    def _generate_ai_response(
        self, conversation_messages: list, step: int, conversation_id: int
    ) -> tuple[str, str]:
        """
        Generate an AI response using the Ollama model.

        Args:
            conversation_messages: Current conversation history
            step: Current conversation step
            conversation_id: Database conversation ID

        Returns:
            Tuple of (response_content, thinking)
        """

        if self.stream:
            return self._generate_streaming_response(
                conversation_messages, step, conversation_id
            )
        else:
            return self._generate_non_streaming_response(
                conversation_messages, step, conversation_id
            )

    def _generate_streaming_response(
        self, conversation_messages: list, step: int, conversation_id: int
    ) -> tuple[str, str]:
        """Generate a streaming response from the AI model."""
        from rich.console import Console

        console = Console()

        full_response = ""
        thinking = ""

        # Get streaming response
        response_stream: Iterator[ChatResponse] = chat(
            model=self.model,
            messages=conversation_messages,
            stream=True,
            think="low",
            tools=list(self.available_tools.values()),
        )

        # Process streaming response
        first_printed_response = False
        first_printed_thinking = False

        for chunk in response_stream:
            if chunk.message.content:
                if not first_printed_response:
                    console.print("[bold yellow]\nAssistant: ", end="")
                    first_printed_response = True
                print(chunk.message.content, end="")
                full_response += chunk.message.content

            if chunk.message.thinking:
                if not first_printed_thinking:
                    console.print("[bold yellow]\nThinking: ", end="")
                    first_printed_thinking = True
                console.print(chunk.message.thinking, end="")
                thinking += chunk.message.thinking

        console.print()  # newline after streaming finishes

        # Handle tool calls if any
        if hasattr(chunk.message, "tool_calls") and chunk.message.tool_calls:
            self._handle_tool_calls(
                chunk.message.tool_calls, conversation_messages, step, conversation_id
            )

        return full_response, thinking

    def _generate_non_streaming_response(
        self, conversation_messages: list, step: int, conversation_id: int
    ) -> tuple[str, str]:
        """Generate a non-streaming response from the AI model."""
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console()

        full_response = ""
        thinking = ""

        # Get non-streaming response
        response: ChatResponse = chat(
            model=self.model, messages=conversation_messages, stream=False, think="low"
        )

        # Process response content
        if response.message.content:
            console.print("[bold yellow]\nAssistant:", end="\n")

            console.print(Markdown(response.message.content), end="")
            full_response = response.message.content

        # Process thinking
        if getattr(response.message, "thinking", None):
            console.print("[bold yellow]\nThinking: ", end="\n")
            from rich.console import Console
            from rich.markdown import Markdown

            console = Console()
            console.print(Markdown(response.message.thinking), end="")
            thinking = response.message.thinking

        # Handle tool calls if any
        if hasattr(response.message, "tool_calls") and response.message.tool_calls:
            self._handle_tool_calls(
                response.message.tool_calls,
                conversation_messages,
                step,
                conversation_id,
            )

        return full_response, thinking

    def _handle_tool_calls(
        self, tool_calls, conversation_messages: list, step: int, conversation_id: int
    ):
        """Handle tool calls from the AI model."""
        from rich.console import Console

        console = Console()

        for tool_call in tool_calls:
            function_to_call = self.available_tools.get(tool_call.function.name)
            if function_to_call:
                console.print(
                    f"Calling tool: {tool_call.function.name}, "
                    f"with arguments: {tool_call.function.arguments}",
                    end="",
                )

                try:
                    result = function_to_call(**tool_call.function.arguments)
                    console.print("[bold magenta]Tool result:" + "{result}")

                    # Add tool result to conversation
                    conversation_messages.append(
                        {
                            "role": "tool",
                            "content": result,
                            "tool_name": tool_call.function.name,
                        }
                    )

                    # Store tool result in database
                    self.db_manager.insert_message(
                        conversation_id=conversation_id,
                        step=step,
                        role="tool",
                        content=result,
                        tool_name=tool_call.function.name,
                        model=self.model,
                    )

                except Exception as e:
                    logger.error(f"Error executing tool {tool_call.function.name}: {e}")
                    console.print(f"[bold red]Tool execution error: {e}")
            else:
                console.print(f"Tool {tool_call.function.name} not found")

    def _append_assistant_message_with_thinking(
        self, messages: list, content: str, thinking: str
    ) -> list:
        """
        Append an assistant message with thinking to the messages list.

        Args:
            messages: List of conversation messages
            content: The assistant's response content
            thinking: The assistant's thinking process

        Returns:
            Updated messages list
        """
        messages.append({"role": "assistant", "content": content, "thinking": thinking})

        logger.debug("Appended assistant message with thinking: %s", messages[-1])
        return messages
