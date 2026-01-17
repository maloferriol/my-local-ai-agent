# Frontend Exploration Summary

## Overview
Successfully explored and documented the frontend codebase for the My Local AI Agent project. The frontend is a modern React 19 application built with Vite and React Router v7, featuring a conversational UI for interacting with LLM agents.

## Key Findings

### 1. Framework: React + Vite (NOT Next.js)
- React 19.0.0 with TypeScript
- Vite 6.3.4 as the build tool
- React Router DOM v7.5.3 for client-side routing
- Tailwind CSS v4.1.5 for styling
- Radix UI components for accessible UI primitives

### 2. Directory Structure
The frontend is organized into clear, logical sections:
- `src/main.tsx` - Entry point with routing setup
- `src/App.tsx` - Main component handling conversation logic
- `src/components/` - All UI components (ChatMessagesView, InputForm, WelcomeScreen, etc.)
- `src/components/ui/` - Reusable UI components (button, card, input, etc.)
- `src/components/agents/` - Agent-specific configuration and fields
- `src/lib/` - Utilities, types, and API functions

### 3. Routing Configuration
Routes defined in `main.tsx`:
- `/` - Homepage (shows WelcomeScreen when no messages)
- `/c/:conversationId` - Conversation page (shows ChatMessagesView with messages)

Both routes use the same `App.tsx` component, which conditionally renders based on state.

### 4. Conversation Page Location
The conversation page is located at:
- **File**: `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/components/ChatMessagesView.tsx`
- **Route**: `/c/:conversationId`
- **Triggered**: After user submits a query, backend creates conversation, app navigates to `/c/{id}`

### 5. Navigation & Back Button Patterns

**Current Navigation:**
1. **Homepage to Conversation**: 
   - User submits query on `/` (WelcomeScreen)
   - Backend returns conversation_id
   - App navigates to `/c/{id}` using `navigate('/c/{id}', { replace: true })`
   
2. **Conversation to Homepage**:
   - User clicks "New Search" button
   - Button calls `window.location.reload()`
   - Page reloads and returns to `/` (WelcomeScreen)

**Back Button Behavior:**
- Currently: Uses `{ replace: true }` in navigation
- This replaces history entries, preventing browser back button from working as expected
- Browser back button won't navigate between conversations
- Browser back button might close app or go to previous site

**Navigation Implementation:**
- Uses React Router's `useNavigate()` hook for programmatic navigation
- Uses `useParams()` to read `:conversationId` from URL
- Uses `useEffect` with conversationId dependency to fetch conversation messages

### 6. Homepage/Root URL Structure

**URL**: `/`
**Component**: `App.tsx` with `WelcomeScreen` sub-component
**Rendering**: Shows WelcomeScreen when `chats.length === 0`

**WelcomeScreen Features:**
- Large heading: "Welcome to Build Your Own Agent"
- Agent selector (currently: My Local Agent)
- Model selector (gpt-oss:20b, gemma3:4b)
- Mode selector (default, hybrid, sparse)
- Input textarea with Send button
- Footer text about project origin

### 7. Component Architecture

**App.tsx** (Main State Container):
- Manages: chats, conversationId, selectedAgent, isLoading, processedEventsTimeline
- Handles: API calls, message streaming, navigation
- Conditional rendering: WelcomeScreen vs ChatMessagesView

**InputForm.tsx** (Shared Input Component):
- Used in both WelcomeScreen and ChatMessagesView
- Props: onSubmit, onCancel, isLoading, hasHistory, agentControl
- hasHistory prop controls "New Search" button visibility

**ChatMessagesView.tsx** (Conversation Display):
- Displays message bubbles (UserMessageBubble, AiMessageBubble)
- Shows ActivityTimeline for agent activities
- Shows ThinkingStream for AI thinking
- Includes InputForm at bottom

**Agent System**:
- Registry pattern: `AgentRegistry.tsx`
- Available agents: MyLocalAgent (with config), GeminiAgent (scaffolding), RAGAgent (scaffolding)
- Each agent can have custom Fields component for configuration

### 8. API Communication
- **POST** `/backend/agent/{agentURL}` - Submit query with streaming response
  - Returns JSON events with stages: metadata, thinking, tool_result, content, finalize_answer
  
- **GET** `/backend/{agentURL}/conversation/{conversationId}` - Fetch conversation messages

### 9. State Management
- React Hooks only (useState, useRef, useCallback, useEffect)
- Custom hook: `useSelectedAgent()` - manages agent selection with localStorage
- URL params: conversationId stored in URL for persistence
- No Redux, Context API not heavily used

## Created Documentation Files

1. **FRONTEND_ANALYSIS.md** (9.0 KB)
   - Comprehensive analysis of framework, structure, routing, navigation
   - TypeScript types, API communication, key features
   
2. **FRONTEND_QUICK_REFERENCE.md**
   - Quick lookup guide for developers
   - Key files, navigation flow, important details
   - "How to" guide for common tasks (add back button, change styling, add agent, etc.)

3. **FRONTEND_ARCHITECTURE.txt**
   - Visual ASCII diagrams of architecture
   - HTTP request/response flow
   - URL & page structure
   - Navigation patterns
   - State management overview

## File Paths (Absolute)

### Key Source Files:
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/main.tsx` - Routing entry point
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/App.tsx` - Main app component
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/components/WelcomeScreen.tsx` - Landing page
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/components/ChatMessagesView.tsx` - Conversation view
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/components/InputForm.tsx` - Shared input component
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/lib/apis/agent/index.ts` - API functions
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/lib/types/index.ts` - TypeScript types

### Configuration Files:
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/package.json` - Dependencies
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/vite.config.ts` - Vite config
- `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/index.html` - HTML entry point

## Conclusions

The frontend is well-structured with clear separation of concerns:
- Clean routing with React Router v7
- Component-based architecture with reusable UI primitives
- Modern React patterns (hooks, custom hooks)
- Integration with LangChain for agent communication
- Streaming message support for real-time feedback
- Agent registry pattern for extensibility

The codebase follows TypeScript best practices and uses Tailwind CSS for a consistent dark-themed UI. Navigation uses React Router's built-in capabilities with programmatic navigation after API calls.

## Quick Commands

```bash
cd /Users/user/Code/github/maloferriol/my-local-ai-agent/frontend
npm install      # Install dependencies
npm run dev      # Start dev server (http://localhost:5173)
npm run build    # Build for production
npm run lint     # Run ESLint
```
