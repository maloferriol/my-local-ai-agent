# Frontend Quick Reference Guide

## Key Files for Development

### Routing & Navigation
- **`frontend/src/main.tsx`** - Entry point, defines routes
  - Routes: `/` and `/c/:conversationId`
  - Both use the same `App` component
  
- **`frontend/src/App.tsx`** - Main app logic
  - Handles navigation: `useNavigate()`, `useParams()`
  - Fetches conversations via `getConversation()`
  - Manages chat state and message streaming
  - Conditionally renders `WelcomeScreen` or `ChatMessagesView`

### Page Components
- **`frontend/src/components/WelcomeScreen.tsx`** - Landing page
  - Shows when `chats.length === 0`
  - Displays InputForm with agent selector
  
- **`frontend/src/components/ChatMessagesView.tsx`** - Conversation view
  - Shows when user has sent messages
  - Displays message bubbles, activity timeline, thinking stream
  - Contains InputForm at bottom

### Input & Forms
- **`frontend/src/components/InputForm.tsx`** - Shared input component
  - Textarea, Send/Stop button
  - Agent selector dropdown
  - Model & Mode selectors (from active agent)
  - "New Search" button (reloads page to go to `/`)
  - `hasHistory` prop controls visibility of "New Search"

### Agent System
- **`frontend/src/components/registry/AgentRegistry.tsx`** - Agent registry
  - Central registry for available agents
  - Defines agent types: AgentType
  
- **`frontend/src/components/agents/MyLocalAgent.tsx`** - Local agent
  - Model selector (gpt-oss:20b, gemma3:4b)
  - Mode selector (default, hybrid, sparse)
  - Event processing for streaming responses

### API Communication
- **`frontend/src/lib/apis/agent/index.ts`** - API functions
  - `getAgentResponse(query, agentURL)` - POST agent query, returns streaming response
  - `getConversation(id, agentURL)` - GET conversation messages

### Types & Utilities
- **`frontend/src/lib/types/index.ts`** - TypeScript interfaces
  - `RoleType` enum (user, assistant, tool, system)
  - `Conversation` interface
  - `ChatMessage` interface
  
- **`frontend/src/hooks/useSelectedAgent.ts`** - Agent selection hook
  - Manages selectedAgent state with localStorage

## Navigation Flow

### Going from Homepage to Conversation
1. User enters query on `/` (WelcomeScreen)
2. Submit calls `handleSubmit()` in App.tsx
3. Backend creates conversation, returns `conversation_id` in metadata
4. App detects metadata event: `navigate('/c/{id}', { replace: true })`
5. Page now shows `/c/{conversation_id}`
6. App.tsx fetches full conversation with `getConversation()`
7. ChatMessagesView displays all messages

### Going from Conversation to Homepage
1. User clicks "New Search" button in InputForm
2. Button calls `window.location.reload()`
3. App re-mounts, `conversationId` is gone
4. `chats.length === 0`, so WelcomeScreen displays
5. URL is back at `/`

### Back Button Behavior
- Currently: NOT USED - navigation uses `{ replace: true }`
- This replaces browser history entries
- Browser back button won't work as expected between conversations
- Browser back button might close app or go to previous site

## Important Implementation Details

### State Management
```typescript
App.tsx states:
- chats: ChatMessage[] - conversation messages
- processedEventsTimeline: ProcessedEvent[] - live agent activity
- selectedAgent: AgentType - current agent selection
- isLoading: boolean - request in progress
- thinkingContent: string - AI thinking text
- conversationId: from URL params
```

### Message Streaming
App reads streaming JSON events from `/backend/agent/{agentURL}`:
```
{stage: 'thinking', response: '...'}
{stage: 'tool_result', tool: 'search', result: '...'}
{stage: 'content', response: 'text chunk...'}
{stage: 'finalize_answer'}
```

### Component Props Pattern
InputForm takes `hasHistory` prop to determine if it's on:
- WelcomeScreen: `hasHistory={false}` - no "New Search" button
- ChatMessagesView: `hasHistory={true}` - shows "New Search" button

## Files by Purpose

### To Add Back Button
- Modify: `frontend/src/components/InputForm.tsx` - Add back navigation button
- Modify: `frontend/src/main.tsx` or routing logic - Handle back navigation

### To Change Homepage URL
- Modify: `frontend/src/main.tsx` - Change route path from "/" to "/home"
- Update references in App.tsx `navigate()` calls

### To Add New Agent
- Create: `frontend/src/components/agents/NewAgent.tsx`
- Modify: `frontend/src/components/registry/AgentRegistry.tsx` - Add to registry

### To Change Styling
- Modify: `frontend/src/global.css` - Global styles
- Modify: Component files - Use Tailwind CSS classes
- Components use dark theme: `bg-neutral-800`, `text-neutral-100`

### To Change API Endpoints
- Modify: `frontend/src/lib/apis/agent/index.ts` - Update fetch URLs
- Currently: `/backend/agent/{agentURL}` and `/backend/{agentURL}/conversation/{id}`

## Configuration Files
- **`frontend/vite.config.ts`** - Build config, path alias "@"
- **`frontend/tsconfig.json`** - TypeScript settings
- **`frontend/index.html`** - HTML entry point with #root div
- **`frontend/package.json`** - Dependencies and scripts

## Build & Run Commands
```bash
cd frontend
npm install                # Install dependencies
npm run dev                # Start dev server (default: http://localhost:5173)
npm run build              # Build for production
npm run preview            # Preview production build
npm run lint               # Run ESLint
```
