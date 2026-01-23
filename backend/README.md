# Backend Directory Documentation

This directory contains the backend services for the My Local AI Agent application. It is primarily built with Python and FastAPI, providing the core logic for AI agent interactions, tool management, conversation handling, and data persistence.

## Structure

-   `src/`: Contains the main source code for the backend application.
    -   `app.py`: The main FastAPI application entry point.
    -   `conversation.py`: Handles conversation management and logic.
    -   `logging_config.py`: Configuration for application logging.
    -   `models.py`: Defines data models used across the application.
    -   `opentelemetry_instructions.md`: Documentation related to OpenTelemetry setup.
    -   `agent/`: Contains implementations for different AI agents.
        -   `my_local_agent/`: Specific implementation of a local AI agent.
            -   `route.py`: Defines API routes for the local agent.
            -   `tools.py`: Contains tools specific to the local agent.
    -   `database/`: Database-related functionalities.
        -   `db.py`: Handles database connection and operations.
    -   `models/`: Additional data models, potentially for planning and tracing.
        -   `planning.py`: Models related to AI planning.
        -   `tracing.py`: Models for tracing and observability.
    -   `tools/`: General tools that can be used by various agents.
        -   `registry.py`: Manages the registration and discovery of tools.
        -   `models.py`: Data models for tools.
        -   `implementations/`: Contains concrete implementations of various tools (e.g., `weather.py`).
-   `tests/`: Contains unit and integration tests for the backend services.
    -   `conftest.py`: Pytest configuration and fixtures.
    -   `test_*.py`: Various test files covering different modules (e.g., `test_conversation_manager.py`, `test_database_db.py`, `test_e2e_api.py`).
    -   `tools/`: Tests specifically for the tools module (e.g., `test_registry.py`).
-   `docs/`: Additional documentation specific to the backend.
    -   `DB_CONNECTION_MANAGEMENT.md`: Documentation on database connection management.
    -   `OllamaClientDoc.md`: Documentation for the Ollama client.
    -   `Plan.md`: High-level plan or design document.
-   `requirements.txt`: Lists all Python dependencies required for the backend.
-   `Dockerfile`: Defines the Docker image for the backend service.
-   `pytest.ini`: Pytest configuration file.
-   `.coveragerc`: Configuration for code coverage reporting.
-   `.gitignore`: Specifies files and directories to be ignored by Git.
-   `CLAUDE.md`, `GEMINI.md`, `curl_test_examples.md`: Specific documentation or examples related to Claude, Gemini, and curl testing.

## Key Technologies

-   **FastAPI**: Web framework for building APIs.
-   **Python**: Primary programming language.
-   **Pytest**: Testing framework.
-   **SQLAlchemy (likely via `db.py`)**: ORM for database interactions.
-   **OpenTelemetry**: For observability and tracing.

## Routing and Agent Independence

The backend's routing is designed to support multiple, independent AI agents. This is achieved by incorporating the agent's name directly into the URL structure (e.g., `/agent/{agent_name}/...`). This design has several implications:

-   **Independent Agent Development**: Each agent can have its own dedicated set of routes and logic, allowing for independent development, deployment, and scaling.
-   **Modularity**: New agents can be easily integrated into the system by defining their routes and associated logic without affecting existing agents.
-   **Clear Separation of Concerns**: The URL structure clearly delineates which agent an incoming request is intended for, promoting a modular and organized codebase.

## Agent Registration and Integration

New agents are integrated into the FastAPI application through a registration process. The main `app.py` file is responsible for including the API routes defined by each agent. For example, an agent's routes, such as those in `src/agent/my_local_agent/route.py`, are typically registered with the main FastAPI application, making them accessible under their respective agent-specific paths. This mechanism ensures that each agent's functionalities are exposed via the API while maintaining a clear separation within the overall application structure.

## Getting Started

Refer to the `Dockerfile` and `requirements.txt` for setting up the development environment. Detailed instructions for specific components can be found in the `docs/` directory.