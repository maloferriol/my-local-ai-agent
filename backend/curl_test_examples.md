# Testing Backend with curl

You can also test the backend API using curl commands once the server is running.

## Start the Backend Server

```bash
# Option 1: With Docker Compose (includes all dependencies)
docker-compose -f docker-compose.dev.yml up backend

# Option 2: Directly with uvicorn (requires environment setup)
cd backend
export OLLAMA_URL=http://localhost:11434
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

## Test with curl

### 1. Get Non-existent Conversation
```bash
curl -X GET http://localhost:8123/agent/my_local_agent/conversation/999
# Expected: 404 with {"detail": "Conversation not found"}
```

### 2. Start New Conversation
```bash
curl -X POST http://localhost:8123/agent/my_local_agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "id": 0,
    "title": "Test Conversation",
    "model": "gpt-oss:20b",
    "messages": [
      {
        "role": "user",
        "content": "Hello, what is the weather like?",
        "model": "gpt-oss:20b"
      }
    ]
  }'
```

### 3. Continue Existing Conversation
```bash
# Use the conversation_id from the previous response
curl -X POST http://localhost:8123/agent/my_local_agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "title": "Test Conversation",
    "model": "gpt-oss:20b",
    "messages": [
      {
        "role": "user",
        "content": "Thank you!",
        "model": "gpt-oss:20b"
      }
    ]
  }'
```

### 4. Get Conversation by ID
```bash
curl -X GET http://localhost:8123/agent/my_local_agent/conversation/1
```

## Response Format

The `/invoke` endpoint returns a streaming response with JSON objects separated by newlines:

```json
{"stage": "metadata", "conversation_id": 1}
{"stage": "content", "response": "Hello! "}
{"stage": "content", "response": "I'll check the weather for you."}
{"stage": "tool_result", "tool": "get_weather", "result": "22°C and sunny"}
{"stage": "content", "response": "The weather is 22°C and sunny!"}
{"stage": "finalize_answer"}
```

## Benefits of curl Testing

- **Real HTTP requests** - Tests the actual network stack
- **Manual verification** - You can see exactly what the API returns
- **Integration testing** - Tests with real Ollama service if available
- **Debugging** - Easy to modify requests and see responses
- **CI/CD** - Can be scripted for automated testing