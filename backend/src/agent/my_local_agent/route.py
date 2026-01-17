import logging.config
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from ollama import AsyncClient
from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.context import get_current

from rich import print

from .tools import MyLocalAgentToolRegistry
from src.database.db import DatabaseManager
from src.models import Conversation
from src.logging_config import LOGGING_CONFIG
from src.conversation import ConversationManager
from src.services.llm_service import LLMService
from src.services.tool_execution_service import ToolExecutionService
from src.services.chat_orchestration_service import ChatOrchestrationService
from src.config.model_config import get_model_registry
from src.utils.error_handling import print_trace, create_error_stream_response


# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Initialize tracer
tracer = trace.get_tracer(__name__)

# Constants
CONVERSATION_NOT_FOUND_MSG = "Conversation not found"

# Initialize tool registry for this agent
tool_registry = MyLocalAgentToolRegistry.create_registry()
logger.info(f"Tool registry initialized with {len(tool_registry.tools)} tools")

# Initialize Ollama client
try:
    ollama_client = AsyncClient(host=os.environ["OLLAMA_URL"])
except Exception as e:
    print(f"FAIL Ollama client initialization error: {e}")
    logger.error(f"Failed to initialize Ollama client: {e}")
    raise

# Initialize services
llm_service = LLMService(ollama_client)
tool_execution_service = ToolExecutionService(tool_registry)
model_registry = get_model_registry()
chat_orchestration_service = ChatOrchestrationService(
    llm_service=llm_service,
    tool_execution_service=tool_execution_service,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    """
    print("Application startup: Ensuring database tables exist...")
    with DatabaseManager() as db:
        db.create_init_tables()
        logger.info("Database tables verified.")
    yield
    # On shutdown, you can add cleanup logic if needed
    print("Application shutdown.")


app = FastAPI(
    lifespan=lifespan,
)


@app.get("/conversation/{conversation_id}", response_model=Conversation)
@tracer.start_as_current_span(name="get_conversation", kind=SpanKind.INTERNAL)
async def get_conversation(
    conversation_id: int,
):
    """
    Fetch a conversation by its ID.

    Args:
        conversation_id: The ID of the conversation to fetch.

    Returns:
        The conversation object.
    """
    print("/conversation/")
    print("==========================================================================")
    conv_manager = ConversationManager.load_existing(conversation_id)
    if conv_manager:
        return conv_manager.get_current_conversation()
    else:
        raise HTTPException(status_code=404, detail=CONVERSATION_NOT_FOUND_MSG)


@app.get("/tools/stats")
@tracer.start_as_current_span(name="get_tool_stats", kind=SpanKind.INTERNAL)
async def get_tool_stats():
    """
    Get statistics about registered tools.

    Returns:
        Tool registry statistics including usage metrics.
    """
    return tool_registry.get_tool_stats()


@app.get("/tools")
@tracer.start_as_current_span(name="get_tools", kind=SpanKind.INTERNAL)
async def get_tools():
    """
    Get list of all available tools with their metadata.

    Returns:
        List of available tools with their versions and metadata.
    """
    active_tools = tool_registry.get_active_tools()
    return [tool.to_dict() for tool in active_tools]


@app.get("/conversation/{conversation_id}/enhanced-summary")
@tracer.start_as_current_span(name="get_enhanced_summary", kind=SpanKind.INTERNAL)
async def get_enhanced_conversation_summary(conversation_id: int):
    """
    Get enhanced conversation summary with planning and tracing information.

    Args:
        conversation_id: The ID of the conversation

    Returns:
        Enhanced summary with planning, tracing, and performance metrics
    """
    conv_manager = ConversationManager.load_existing(conversation_id)
    if not conv_manager:
        raise HTTPException(status_code=404, detail=CONVERSATION_NOT_FOUND_MSG)

    return conv_manager.get_enhanced_summary()


@app.post("/invoke")
async def invoke(
    conversation: Conversation,
):
    """
    Handle user queries by streaming responses from Ollama.

    Args:
        conversation: UserQuery object containing messages and model configuration

    Returns:
        StreamingResponse containing chat responses and tool execution results
    """
    with tracer.start_as_current_span(
        "invoke",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    ) as span:
        logger.info(
            "Received chat request with %d messages",
            len(conversation.messages) if conversation.messages else 0,
        )

        user_message = conversation.messages[-1] if conversation.messages else None
        if not user_message:
            raise HTTPException(status_code=400, detail="Query contains no messages.")

        print(f"User message model: {user_message.model}")
        print(f"User message content: {user_message.content}")
        print("==========================================================================")
        print("conversation object:", conversation)
        
        if conversation.id == 0:
            # Create a new conversation
            conv_manager = ConversationManager.create_new(model=user_message.model)
        else:
            # Load existing conversation
            conv_manager = ConversationManager.load_existing(
                conversation.id,
            )

        if not conv_manager:
            raise HTTPException(status_code=404, detail=CONVERSATION_NOT_FOUND_MSG)

        # Add the user's new message to the conversation state
        conv_manager.add_user_message(
            content=user_message.content, model=user_message.model
        )

        model = user_message.model or "gpt-oss:20b"  # Default model
        span.set_attribute("llm.model_name", model)

        try:
            # Validate conversation state
            if not chat_orchestration_service.validate_conversation_state(conv_manager):
                raise HTTPException(
                    status_code=400, detail="Invalid conversation state"
                )

            parent_ctx = get_current()
            return StreamingResponse(
                chat_orchestration_service.stream_chat_with_tools(
                    model, conv_manager, parent_ctx
                ),
                media_type="text/plain",
            )
        except Exception as e:
            print_trace(e)
            logger.error(f"Failed to create StreamingResponse: {e}")
            # Return error response using utility function
            error_response = {
                "stage": "error",
                "response": f"Response creation error: {str(e)}",
            }
            return StreamingResponse(
                iter([create_error_stream_response(error_response)]),
                media_type="text/plain",
            )
