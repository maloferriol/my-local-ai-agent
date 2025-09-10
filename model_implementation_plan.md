# Model Implementation Plan

## Current State Analysis

### Existing Structure (`backend/src/`)
```
backend/src/
├── models.py              # Core data models (ChatMessage, Conversation, Role enum)
├── conversation.py        # ConversationManager class for business logic
├── database/
│   └── db.py             # DatabaseManager with SQLite operations
├── agent/
│   └── my_local_agent/   # Agent-specific routing and logic
│       ├── route.py      # FastAPI routes and streaming chat logic
│       └── examples.py   # Tool implementations (weather functions)
├── app.py                # FastAPI application entry point
└── logging_config.py     # Logging configuration
```

### Current Models (`backend/src/models.py`)

**Implemented:**
- `Role` enum (USER, ASSISTANT, SYSTEM, TOOL)
- `ChatMessage` dataclass with proper typing and serialization
- `Conversation` dataclass with message management methods

**Features:**
- Type-safe with proper dataclass decorators
- Dictionary serialization via `to_dict()` methods
- Optional fields for metadata, timestamps, tool calls
- Message aggregation and conversation state management

## Recommended Model Organization

### Option 1: Keep Current Single File (Recommended)
**Rationale:** Current `models.py` is well-structured and manageable (~75 lines). Splitting would add complexity without clear benefits.

**Maintain:**
- `backend/src/models.py` - All core models
- Clear separation between data models and business logic
- Existing imports and dependencies remain unchanged

### Option 2: Split into Modular Structure (If Growth Required)
**Only if models.py exceeds ~200 lines or distinct model domains emerge:**

```
backend/src/models/
├── __init__.py           # Export all models
├── base.py              # Base classes, common utilities
├── message.py           # ChatMessage, Role enum
├── conversation.py      # Conversation model
└── metadata.py          # Metadata-related models
```

## Implementation Priorities

### 1. Enhance Current Models (High Priority)
- Add proper database field constraints
- Implement model validation methods
- Add serialization for different formats
- Extend metadata support for rich context

### 2. Current Database Schema Analysis
**Existing Tables:**
```sql
-- conversations table (current)
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- messages table (current)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    step INTEGER,
    role TEXT,
    content TEXT,
    thinking TEXT,
    tool_name TEXT,
    tool_calls TEXT,
    tool_results TEXT,
    model TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Gaps Identified:**
- Missing UUID support (currently using INTEGER IDs)
- Limited metadata/context storage
- No conversation metadata (temperature, system_prompt)
- No message relationships/references
- No execution tracing capabilities
- No component versioning system

## Phase 1: Incremental Model Enhancement (Days 1-5)

### 1.1 Enhance Current Models (`backend/src/models.py`)
**Immediate Tasks:**
1. Add validation methods to `ChatMessage` and `Conversation`
2. Extend metadata fields for richer context storage
3. Add UUID support while maintaining backward compatibility
4. Implement Pydantic models for enhanced validation
5. Add conversation configuration fields (temperature, system_prompt)

### 1.2 Extend Database Schema (Backward Compatible)
**Database Migration Strategy:**
```sql
-- Add new fields to existing tables (backward compatible)
ALTER TABLE conversations ADD COLUMN model_name TEXT;
ALTER TABLE conversations ADD COLUMN system_prompt TEXT;
ALTER TABLE conversations ADD COLUMN temperature REAL DEFAULT 0.7;
ALTER TABLE conversations ADD COLUMN metadata TEXT; -- JSON string

ALTER TABLE messages ADD COLUMN confidence_score REAL;
ALTER TABLE messages ADD COLUMN token_count INTEGER;
ALTER TABLE messages ADD COLUMN processing_time_ms INTEGER;
ALTER TABLE messages ADD COLUMN metadata TEXT; -- JSON string
ALTER TABLE messages ADD COLUMN parent_message_id INTEGER REFERENCES messages(id);
```

### 1.3 Update ConversationManager (`backend/src/conversation.py`)
**Enhancement Tasks:**
1. Add support for new model fields
2. Implement conversation configuration management
3. Add message relationship tracking
4. Extend metadata handling
5. Add validation before database operations

## Phase 2: Advanced Features (Days 6-12)

### 2.1 Optional: Add Planning Models
**New File**: `src/models/planning.py` (if planning features are needed)
- `AgentPlan` dataclass for multi-step task planning
- `PlanStep` dataclass for individual plan steps
- Integration with existing conversation flow

### 2.2 Optional: Add Execution Tracing
**New File**: `src/models/tracing.py` (if detailed tracing is required)
- `ExecutionTrace` for tracking complete agent executions
- `ExecutionSpan` for individual operations
- Integration with OpenTelemetry (already partially implemented)

### 2.3 Tool Management Enhancement
**Update**: `src/agent/my_local_agent/examples.py` and routing logic
- Implement `Tool` model for better tool management
- Add tool versioning and registration system
- Enhance tool result handling

## Phase 3: Integration and Testing (Days 13-18)

### 3.1 Current Service Analysis
**Existing Services:**
- `ConversationManager` in `src/conversation.py` - handles conversation lifecycle
- `DatabaseManager` in `src/database/db.py` - handles SQLite operations  
- Agent routing in `src/agent/my_local_agent/route.py` - handles streaming chat

**Service Integration Strategy:**
1. Enhance `ConversationManager` with new model features
2. Update `DatabaseManager` to support schema changes
3. Improve agent routing to use enhanced models
4. Add optional service layers only if needed for complex features

### 3.2 Testing Strategy
**Unit Tests:**
- Test enhanced models individually
- Test serialization/deserialization
- Test database operations with new fields
- Test conversation manager enhancements

**Integration Tests:**
- Test complete chat flows with enhanced models
- Test database migrations
- Test API endpoints with new model features
- Performance testing with metadata storage

## Implementation Recommendations

### Recommended Approach: Incremental Enhancement
**Start with Phase 1** - enhance existing models and database schema incrementally. This approach:
- Maintains system stability
- Preserves existing functionality
- Allows gradual feature rollout
- Reduces implementation risk

### When to Consider Phase 2 Features
Only implement advanced features if you need:
- **Planning Models**: Multi-step task execution with dependency management
- **Execution Tracing**: Detailed performance analysis and debugging
- **Tool Versioning**: Component lifecycle management and reproducible evaluations

### Current System Strengths
Your current implementation already has:
- ✅ Solid data models with proper typing
- ✅ Effective conversation management
- ✅ Working database persistence
- ✅ OpenTelemetry tracing integration
- ✅ Streaming chat with tool execution
- ✅ Clean separation of concerns

## Success Criteria

### Phase 1 Success
1. ✅ Enhanced models with validation and metadata support
2. ✅ Backward-compatible database schema extensions  
3. ✅ Improved conversation configuration management
4. ✅ Maintained system performance and stability

### Phase 2 Success (Optional)
1. ✅ Advanced planning capabilities for complex tasks
2. ✅ Comprehensive execution tracing and analysis
3. ✅ Component versioning for reproducible evaluations
4. ✅ Enhanced tool management and discovery

## Risk Mitigation

**Database Changes**: Use backward-compatible ALTER statements
**Performance Impact**: Monitor metadata storage overhead
**Complexity Growth**: Keep enhanced features optional and modular
**Testing Coverage**: Comprehensive tests for all model changes

This revised plan focuses on practical, incremental improvements to your existing well-structured codebase while keeping advanced features optional.