# Implementation Plan: Integrated Chat Schema + Execution Tracing

## Overview
This plan integrates the enhanced conversation models (ChatMessage, Conversation, AgentPlan, etc.) with the execution tracing system (ExecutionTrace, ExecutionSpan, ComponentVersion) to create a comprehensive AI agent platform with full evaluation capabilities.

## Phase 1: Foundation Setup (Days 1-3)

### 1.1 Project Structure Setup
```
backend/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── conversation.py      # ChatMessage, Conversation, etc.
│   │   ├── planning.py          # AgentPlan, PlanStep
│   │   ├── tracing.py          # ExecutionTrace, ExecutionSpan
│   │   └── components.py       # ComponentVersion, Tool
│   ├── services/
│   │   ├── conversation_service.py
│   │   ├── tracing_service.py
│   │   └── agent_service.py
│   ├── storage/
│   │   ├── database.py
│   │   └── migrations/
│   └── config/
└── tests/
```

### 1.2 Update Your Existing Models
**Action**: Modify your current `backend/src/models.py`

**Changes needed**:
- Replace simple `ChatMessage` with enhanced version from artifact
- Add UUID support to your existing `Conversation` model
- Integrate the new enums (`MessageRole`, `MessageType`, etc.)

**Migration strategy**:
1. Create new model files alongside existing `models.py`
2. Implement data migration scripts
3. Update imports gradually
4. Remove old `models.py` once migration is complete

### 1.3 Database Schema Design
Create migration files for the new tables:

```sql
-- conversations table (enhanced version of your existing)
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    model_name TEXT,
    system_prompt TEXT,
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER,
    metadata JSONB,
    tags TEXT[]
);

-- messages table (enhanced version)
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    turn_id UUID,
    role TEXT NOT NULL,
    message_type TEXT NOT NULL,
    content TEXT,
    thinking TEXT,
    confidence_score REAL,
    timestamp TIMESTAMP,
    model_name TEXT,
    token_count INTEGER,
    processing_time_ms INTEGER,
    metadata JSONB,
    parent_message_id UUID REFERENCES messages(id),
    references UUID[]
);

-- tool_calls table (new)
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY,
    message_id UUID REFERENCES messages(id),
    name TEXT NOT NULL,
    arguments JSONB,
    created_at TIMESTAMP
);

-- agent_plans table (new)
CREATE TABLE agent_plans (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    title TEXT,
    description TEXT,
    status TEXT,
    current_step_index INTEGER DEFAULT 0,
    context JSONB,
    max_retries INTEGER DEFAULT 3,
    timeout_minutes INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- plan_steps table (new)
CREATE TABLE plan_steps (
    id UUID PRIMARY KEY,
    plan_id UUID REFERENCES agent_plans(id),
    description TEXT,
    status TEXT DEFAULT 'pending',
    result TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    dependencies UUID[],
    step_order INTEGER
);

-- component_versions table (tracing)
CREATE TABLE component_versions (
    component_id TEXT,
    version_hash TEXT,
    component_type TEXT,
    version_name TEXT,
    definition JSONB,
    created_at TIMESTAMP,
    created_by TEXT,
    description TEXT,
    tags JSONB,
    PRIMARY KEY (component_id, version_hash)
);

-- execution_traces table (tracing)
CREATE TABLE execution_traces (
    trace_id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    user_input TEXT,
    final_output TEXT,
    execution_status TEXT,
    initial_memory_state JSONB,
    initial_conversation_state JSONB,
    system_config JSONB,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_duration_ms INTEGER,
    total_tokens_used INTEGER,
    total_cost_usd REAL,
    user_id TEXT,
    session_id TEXT
);

-- execution_spans table (tracing)
CREATE TABLE execution_spans (
    span_id UUID PRIMARY KEY,
    trace_id UUID REFERENCES execution_traces(trace_id),
    parent_span_id UUID REFERENCES execution_spans(span_id),
    operation_type TEXT,
    operation_name TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    inputs JSONB,
    outputs JSONB,
    memory_snapshot JSONB,
    conversation_context JSONB,
    status TEXT,
    error_details JSONB,
    tokens_used INTEGER,
    cost_usd REAL,
    attributes JSONB
);

-- span_components table (links spans to component versions)
CREATE TABLE span_components (
    span_id UUID REFERENCES execution_spans(span_id),
    component_id TEXT,
    version_hash TEXT,
    FOREIGN KEY (component_id, version_hash) REFERENCES component_versions(component_id, version_hash),
    PRIMARY KEY (span_id, component_id, version_hash)
);
```

## Phase 2: Core Models Implementation (Days 4-7)

### 2.1 Implement Conversation Models
**File**: `src/models/conversation.py`

**Tasks**:
1. Copy enhanced models from artifact 1: `ChatMessage`, `Conversation`, `ToolCall`
2. Add database persistence methods (`save()`, `load()`, etc.)
3. Add validation using Pydantic
4. Implement serialization/deserialization
5. Add relationship management (foreign keys)

**Key implementation points**:
- Use UUIDs consistently
- Implement proper enum handling
- Add database session management
- Create helper methods for common queries

### 2.2 Implement Planning Models  
**File**: `src/models/planning.py`

**Tasks**:
1. Implement `AgentPlan` and `PlanStep` from artifact 1
2. Add state machine logic for plan execution
3. Implement dependency resolution for steps
4. Add persistence layer integration
5. Create plan execution helpers

### 2.3 Implement Tracing Models
**File**: `src/models/tracing.py`

**Tasks**:
1. Implement `ExecutionTrace`, `ExecutionSpan`, `ComponentVersion` from artifact 2
2. Add automatic span linking and parent-child relationships
3. Implement specialized span types (`LLMCallSpan`, `ToolCallSpan`, etc.)
4. Add efficient serialization for large traces
5. Create indexing for fast queries

### 2.4 Implement Component Management
**File**: `src/models/components.py`

**Tasks**:
1. Implement `Tool` model from artifact 1
2. Add `ComponentVersion` registry
3. Implement content-addressable hashing
4. Add component lifecycle management
5. Create version resolution logic

## Phase 3: Service Layer Implementation (Days 8-12)

### 3.1 Conversation Service
**File**: `src/services/conversation_service.py`

```python
class ConversationService:
    def __init__(self, db_session, tracing_service):
        self.db = db_session
        self.tracing = tracing_service
    
    def create_conversation(self, user_id: str) -> Conversation:
        """Create new conversation with tracing"""
        
    def add_message(self, conversation_id: UUID, message: ChatMessage) -> ExecutionTrace:
        """Add message and create execution trace"""
        
    def get_conversation_history(self, conversation_id: UUID, limit: int = 50):
        """Get conversation with optional summarization"""
        
    def branch_conversation(self, conversation_id: UUID, from_message_id: UUID):
        """Create conversation branch"""
```

### 3.2 Tracing Service
**File**: `src/services/tracing_service.py`

```python
class TracingService:
    def start_trace(self, conversation_id: UUID, user_input: str) -> ExecutionTrace:
        """Initialize new execution trace"""
        
    def create_span(self, trace_id: UUID, operation_type: str, **kwargs) -> ExecutionSpan:
        """Create and link new span"""
        
    def complete_trace(self, trace: ExecutionTrace, final_output: str):
        """Finalize and store trace"""
        
    def get_trace_analysis(self, trace_id: UUID) -> Dict[str, Any]:
        """Generate evaluation metrics for trace"""
```

### 3.3 Agent Service (Integration Layer)
**File**: `src/services/agent_service.py`

```python
class AgentService:
    def __init__(self, conversation_service, tracing_service, llm_client, tools):
        """Main agent orchestration service"""
        
    def process_user_input(self, conversation_id: UUID, user_input: str) -> str:
        """Complete agent execution with full tracing"""
        # 1. Start execution trace
        # 2. Load conversation context
        # 3. Execute agent reasoning (with LLMCallSpan)
        # 4. Execute tools if needed (with ToolCallSpan)
        # 5. Generate final response (with LLMCallSpan)
        # 6. Update conversation
        # 7. Complete and store trace
        
    def execute_plan_step(self, plan_id: UUID, step_id: UUID):
        """Execute specific plan step with tracing"""
```

## Phase 4: Database Integration (Days 13-15)

### 4.1 Database Connection and Session Management
**File**: `src/storage/database.py`

**Tasks**:
1. Set up SQLAlchemy or your preferred ORM
2. Implement connection pooling
3. Add transaction management
4. Create database session factory
5. Add migration system

### 4.2 Repository Pattern Implementation
Create repository classes for each model:

```python
class ConversationRepository:
    def save(self, conversation: Conversation)
    def get_by_id(self, conversation_id: UUID)
    def get_recent_messages(self, conversation_id: UUID, limit: int)
    
class TracingRepository:
    def save_trace(self, trace: ExecutionTrace)
    def get_trace(self, trace_id: UUID)
    def get_traces_for_conversation(self, conversation_id: UUID)
    def query_traces(self, filters: Dict[str, Any])
```

### 4.3 Data Migration Scripts
Create scripts to migrate from your current schema:

1. Backup existing data
2. Create new tables
3. Migrate conversation data to new format
4. Update foreign key relationships
5. Verify data integrity

## Phase 5: Agent Integration (Days 16-20)

### 5.1 Tool System Integration
**Tasks**:
1. Migrate existing tools to new `Tool` model
2. Implement automatic component versioning
3. Add tool call tracing to existing tool execution
4. Create tool registry with version management

### 5.2 LLM Integration with Tracing
**Tasks**:
1. Wrap LLM calls with `LLMCallSpan` creation
2. Capture prompt templates as `ComponentVersion`
3. Store model configurations as versions
4. Add token counting and cost tracking

### 5.3 Memory and Planning Integration
**Tasks**:
1. Integrate `AgentPlan` with existing agent logic
2. Add plan execution tracing
3. Implement memory snapshot capture
4. Create plan state persistence

## Phase 6: API and Interface Updates (Days 21-23)

### 6.1 Update API Endpoints
Modify existing endpoints to work with new models:

```python
# Enhanced endpoints
POST /conversations                    # Create with tracing
GET /conversations/{id}/messages       # Enhanced message format  
POST /conversations/{id}/messages      # Returns trace info
GET /conversations/{id}/traces         # New: get execution traces
GET /traces/{trace_id}                 # New: detailed trace analysis
```

### 6.2 Add Evaluation Endpoints
```python
GET /traces/{trace_id}/analysis        # Execution analysis
GET /conversations/{id}/evaluation     # Conversation-level metrics
POST /traces/query                     # Advanced trace querying
GET /components/{id}/versions          # Component version history
```

## Phase 7: Testing and Validation (Days 24-26)

### 7.1 Unit Tests
- Test all new models individually
- Test serialization/deserialization
- Test database operations
- Test trace creation and linking

### 7.2 Integration Tests
- Test complete agent execution flows
- Test conversation branching
- Test plan execution with tracing
- Test cross-conversation queries

### 7.3 Performance Testing
- Test trace storage performance
- Test conversation loading with many messages
- Test query performance on traces
- Optimize database indexes

## Phase 8: Documentation and Deployment (Days 27-30)

### 8.1 Documentation
- API documentation updates
- Model relationship diagrams
- Tracing architecture documentation
- Evaluation platform user guide

### 8.2 Deployment Strategy
1. Deploy database migrations
2. Deploy new models and services
3. Update API endpoints
4. Migrate existing data
5. Validate system functionality

## Key Implementation Tips

### A. Start with Simple Cases
Begin implementation with basic user message → agent response flows before adding complex planning and tool usage.

### B. Use Feature Flags
Implement feature flags to gradually roll out new tracing without breaking existing functionality.

### C. Maintain Backward Compatibility
Design migration strategy that allows rollback if needed.

### D. Focus on Core Integration Points
The main integration happens in `AgentService.process_user_input()` - this is where conversation models meet tracing.

### E. Test Incrementally
Test each phase thoroughly before moving to the next. The integration of two complex systems requires careful validation.

## Success Criteria

By the end of this implementation:

1. ✅ Enhanced conversation models store rich message context
2. ✅ Complete execution traces capture every operation
3. ✅ Component versioning enables reproducible evaluations  
4. ✅ Agent planning integrates with conversation flow
5. ✅ Evaluation platform can analyze any execution in detail
6. ✅ System maintains performance with full tracing enabled

## Risk Mitigation

**Performance Impact**: Implement trace sampling and async storage
**Data Volume**: Add trace retention policies and archival
**Complexity**: Start with core models, add advanced features incrementally
**Migration Issues**: Extensive testing of data migration scripts

This plan provides a structured approach to integrating both schema designs while maintaining system stability and enabling powerful evaluation capabilities.