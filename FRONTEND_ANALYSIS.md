# Frontend Codebase Analysis

## 1. Overall Framework & Technology Stack

### Framework
**React 19.0.0** with **Vite** as the build tool (not Next.js)

### Key Dependencies:
- **Routing**: React Router DOM v7.5.3
- **Styling**: Tailwind CSS v4.1.5 + Class Variance Authority
- **UI Components**: Radix UI (scroll-area, select, tabs, tooltip, slot)
- **Markdown**: react-markdown
- **Icons**: lucide-react
- **LangChain Integration**: @langchain/core, @langchain/langgraph-sdk
- **Build Tools**: Vite 6.3.4, TypeScript 5.7.2

## 2. Frontend Directory Structure

```
frontend/
├── src/
│   ├── main.tsx              # Entry point with React Router setup
│   ├── App.tsx               # Main app component (handles conversation logic)
│   ├── global.css            # Global styles
│   ├── vite-env.d.ts         # Vite type definitions
│   │
│   ├── components/           # React components
│   │   ├── ChatMessagesView.tsx    # Displays messages in conversation
│   │   ├── InputForm.tsx           # Input area & send button
│   │   ├── WelcomeScreen.tsx       # Landing page
│   │   ├── ActivityTimeline.tsx    # Timeline of agent activities
│   │   ├── ThinkingStream.tsx      # Shows AI thinking content
│   │   ├── agents/
│   │   │   ├── MyLocalAgent.tsx    # Local agent config
│   │   │   ├── GeminiAgent.tsx     # Gemini agent (scaffolding)
│   │   │   └── RAGAgent.tsx        # RAG agent (scaffolding)
│   │   ├── registry/
│   │   │   └── AgentRegistry.tsx   # Agent registry & types
│   │   └── ui/                     # Reusable UI components (Radix-based)
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── input.tsx
│   │       ├── select.tsx
│   │       ├── badge.tsx
│   │       ├── textarea.tsx
│   │       ├── tabs.tsx
│   │       └── scroll-area.tsx
│   │
│   ├── lib/
│   │   ├── apis/
│   │   │   └── agent/
│   │   │       └── index.ts       # Agent API calls (getAgentResponse, getConversation)
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript types (Conversation, ChatMessage, RoleType)
│   │   └── utils.ts              # Utility functions (cn classname helper)
│   │
│   └── hooks/
│       └── useSelectedAgent.ts   # Custom hook for agent selection state
│
├── package.json              # Dependencies
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
├── index.html                # HTML entry point
└── Dockerfile                # Docker configuration
```

## 3. Routing Setup (React Router v7)

### Routes Defined in `main.tsx`:
```typescript
<BrowserRouter>
  <Routes>
    <Route path="/" element={<App />} />
    <Route path="/c/:conversationId" element={<App />} />
  </Routes>
</BrowserRouter>
```

### URL Structure:
- **Homepage**: `/` - Shows WelcomeScreen with empty chat
- **Conversation Page**: `/c/:conversationId` - Shows conversation with messages from the API

### How It Works:
1. User submits a query on the homepage (`/`)
2. Backend creates a conversation and returns `conversation_id`
3. App navigates to `/c/{conversation_id}` with `navigate('/c/${data.conversation_id}', { replace: true })`
4. App.tsx fetches the conversation using the ID from URL params
5. Messages are displayed in ChatMessagesView component

## 4. Navigation & Back Button Implementation

### Current Navigation Pattern:

1. **Homepage Navigation** (InputForm.tsx, line 136-140):
   ```typescript
   {hasHistory && (
     <Button onClick={() => window.location.reload()}>
       <SquarePen size={16} />
       New Search
     </Button>
   )}
   ```
   - "New Search" button reloads the page to return to `/`
   - Only shown when there's chat history (`hasHistory={true}`)

2. **Programmatic Navigation** (App.tsx, line 145):
   ```typescript
   if (data.stage === 'metadata' && data.conversation_id && !conversationId) {
     navigate(`/c/${data.conversation_id}`, { replace: true });
   }
   ```
   - Uses React Router's `useNavigate()` hook
   - Redirects to conversation after first response

3. **Error Handling** (App.tsx, line 43):
   ```typescript
   if (conversation_id but conversation not found) {
     navigate('/', { replace: true });
   }
   ```
   - Redirects back to homepage if conversation can't be found

### Navigation Hooks Used:
- `useNavigate()` - For programmatic navigation
- `useParams()` - To read `:conversationId` from URL
- Uses `{ replace: true }` to replace history entries (no back button to previous conversation)

## 5. Homepage/Root URL Structure

### Current Implementation:
1. **URL**: `/`
2. **Component**: `App.tsx` (same as conversation page)
3. **Condition**: 
   - If `chats.length === 0` → Show `WelcomeScreen`
   - Otherwise → Show `ChatMessagesView`

### WelcomeScreen (`WelcomeScreen.tsx`):
```typescript
- Large heading: "Welcome to Build Your Own Agent"
- Subtitle: "How can I help you today?"
- InputForm component for query entry
- Agent selector
- Footer text about project origin
```

### Features:
- Agent selector dropdown (My Local Agent)
- Model selector (gpt-oss:20b, gemma3:4b)
- Mode selector (default, hybrid, sparse)
- Input textarea with Send button
- Never shows "New Search" button (since `hasHistory={false}`)

## 6. Component Architecture

### Data Flow:
```
App.tsx (main state container)
  ├── useState: chats, isLoading, selectedAgent, processedEventsTimeline
  ├── useParams: conversationId from URL
  ├── useNavigate: navigate between routes
  └── Renders based on condition:
      ├── If empty: WelcomeScreen → InputForm
      └── If has chats: ChatMessagesView → InputForm + ChatMessages

InputForm.tsx (shared between both views)
  ├── Textarea for user input
  ├── Agent dropdown selector
  ├── Model/Mode selectors
  ├── Send button or Stop button (when loading)
  └── "New Search" button (only with hasHistory=true)

ChatMessagesView.tsx
  ├── ScrollArea with messages
  ├── Maps through messages array
  ├── Renders UserMessageBubble or AiMessageBubble
  ├── Shows ActivityTimeline for agent activities
  ├── Shows ThinkingStream for AI thinking
  └── InputForm at bottom

ActivityTimeline.tsx
  └── Shows timeline of agent actions (tool calls, results, etc.)

ThinkingStream.tsx
  └── Shows AI's thinking content (collapsible)
```

### State Management:
- **React Hooks only** (useState, useRef, useCallback, useEffect)
- **Custom Hook**: `useSelectedAgent()` - manages selected agent state with localStorage
- **URL Params**: conversationId stored in URL for persistence
- **Refs**: `scrollAreaRef` for auto-scroll, `chatsRef` for message history

## 7. Key Features

### Message Streaming:
- Server sends streaming JSON events
- App parses events and updates state incrementally
- Events include: thinking, tool_result, tool_error, content, finalize_answer

### Agent System:
- Registry pattern for multiple agents (MyLocalAgent, GeminiAgent, RAGAgent)
- Each agent can have custom Fields component for configuration
- Agent URL + query extra info passed to backend API

### UI/UX:
- Dark theme (neutral-800 background)
- Markdown rendering for assistant messages
- Copy button for each message
- Real-time thinking visibility
- Activity timeline for tool calls
- Loading spinner during processing

## 8. Vite Configuration

### Key Settings (`vite.config.ts`):
```typescript
- React + SWC plugin for fast compilation
- Tailwind CSS Vite plugin
- Path alias: "@" → "./src"
- allowedHosts: true (for Docker/host development)
```

## 9. TypeScript Types (`lib/types/index.ts`)

```typescript
enum RoleType {
  User = 'user',
  Assistant = 'assistant',
  Tool = 'tool',
  System = 'system',
}

interface Conversation {
  id: number;
  created_at?: string;
  updated_at?: string;
  title?: string;
  model?: string;
  metadata?: Record<string, any>;
  messages?: ChatMessage[];
}

interface ChatMessage {
  id: string;
  role: RoleType;
  content?: string;
  timestamp?: string;
  thinking?: string;
  tool_name?: string;
  model?: string;
  metadata?: Record<string, any>;
}
```

## 10. API Communication (`lib/apis/agent/index.ts`)

### Functions:
1. **getAgentResponse(query: Conversation, agentURL: string)**
   - POST to `/backend/agent/{agentURL}`
   - Receives streaming response
   - Returns Response object with body readable stream

2. **getConversation(conversationId: number, agentURL: string)**
   - GET to `/backend/{agentURL}/conversation/{conversationId}`
   - Returns Conversation object with all messages

## 11. Entry Points

### HTML Entry (`index.html`):
```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

### React DOM (`main.tsx`):
- Creates React root in #root element
- Wraps app with BrowserRouter for routing
- Renders Routes with "/" and "/c/:conversationId" paths
