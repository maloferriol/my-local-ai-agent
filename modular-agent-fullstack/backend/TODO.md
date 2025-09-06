# Backend TODO

## Conversation Management

### 1. Modify Conversation Handling Logic

-   **File:** `modular-agent-fullstack/backend/src/agent/my_local_agent/route.py`
-   **Task:** Update the main conversation endpoint.
-   **Details:**
    -   If `conversation_id` is `null` or `0`:
        -   Create a new conversation in the database.
        -   Append the first user message.
        -   Return the `conversation_id` of the new conversation.
    -   If `conversation_id` is provided:
        -   Load the existing conversation from the database.
        -   Append the new user message to the conversation.

### 2. Create New Endpoint for Conversation History

-   **Task:** Add a new endpoint to fetch a conversation by its ID.
-   **Endpoint:** `GET /conversation/{conversation_id}`
-   **Details:**
    -   This endpoint will be used by the frontend to load existing chat histories.
    -   It should query the database for the conversation and all associated messages.
    -   It should return the full conversation object.

# Frontend TODO

## Conversation Display

### 1. Implement Conversation Loading from URL

-   **Task:** On page load, parse the URL to check for a `conversation_id`. If a `conversation_id` is present, make a `GET` request to the `/conversation/{conversation_id}` endpoint and display the fetched conversation history in the chat view.

### 2. Handle New Conversations

-   **Task:** Manage `conversation_id` when submitting messages.
-   **Details:**
    -   When sending a message, if a `conversation_id` is in the URL, include it in the request. Otherwise, send `null` or `0`.
    -   After the backend responds to a new conversation, extract the new `conversation_id` from the payload and update the URL to `/?conversation_id={new_conversation_id}`.

# Bug: Conversation not found

## Analysis

The "Conversation not found" error originates in the frontend when the backend's `/conversation/{conversation_id}` endpoint returns a 404 error. This indicates that the requested conversation ID does not exist in the database.

The root cause is likely one of the following:
1.  A new conversation is not being created correctly in the database when a new chat begins.
2.  The `conversation_id` is not being correctly returned to the frontend.
3.  The `conversation_id` is being lost or corrupted between the frontend and backend.

## Debugging Steps

### 1. Verify Conversation Creation

-   **File:** `modular-agent-fullstack/backend/src/agent/my_local_agent/db.py`
-   **Function:** `create_conversation`
-   **Action:** Add logging to this function to verify that it is being called and that a valid `conversation_id` is being generated and returned.

    ```python
    def create_conversation(self, title: str = "") -> int:
        """Creates a new conversation and returns its ID."""
        try:
            random_title = (
                title if title != "" else DatabaseUtils.generate_random_name(3)
            )
            print(f"[DB] Creating conversation with title: {random_title}") # Add this line
            conversation_id = self.execute_query(
                "INSERT INTO conversations (title) VALUES (?)", (random_title,)
            )
            print(f"[DB] Created conversation with ID: {conversation_id}") # Add this line
            return conversation_id
        except sqlite3.Error as e:
            logger.error("Error creating conversation: %s", e)
            print("[DB] Error creating conversation:", e)
            raise
    ```

### 2. Trace the `conversation_id`

-   **File:** `modular-agent-fullstack/backend/src/agent/my_local_agent/route.py`
-   **Function:** `invoke`
-   **Action:** Add logging to trace the `conversation_id` as it is received from the frontend and passed to the `ConversationManager`.

    ```python
    async def invoke(query: Conversation):
        # ...
        conversation_id = query.id
        print(f"[ROUTE] Received invoke request with conversation_id: {conversation_id}") # Add this line
        # ...
        if not conversation_id or conversation_id == 0:
            # ...
            conversation_id = conv_manager.start_new_conversation(title=title, model=model)
            print(f"[ROUTE] Created new conversation with ID: {conversation_id}") # Add this line
        else:
            conv_manager.load_conversation(conversation_id)
            print(f"[ROUTE] Loaded existing conversation with ID: {conversation_id}") # Add this line
        # ...
    ```

### 3. Inspect the Frontend Request

-   **File:** `modular-agent-fullstack/frontend/src/App.tsx`
-   **Function:** `handleSubmit`
-   **Action:** Use the browser's developer tools to inspect the network request sent to the `/invoke` endpoint. Verify that the `id` field in the JSON payload contains the correct `conversation_id`.

### 4. Check the Database Manually

-   Use a SQLite browser to open the `conversation_data.db` file in the `modular-agent-fullstack/backend/databases` directory.
-   Inspect the `conversations` table to see if the conversations are being created with the expected IDs.

By following these steps, you should be able to identify where the `conversation_id` is being lost or why the conversation is not being created correctly.
