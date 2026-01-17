# Frontend Documentation Index

This directory contains comprehensive documentation about the frontend codebase for the My Local AI Agent project.

## Documentation Files

### 1. FRONTEND_EXPLORATION_SUMMARY.md (START HERE)
**Purpose**: High-level overview of the entire frontend exploration
**Contents**:
- Framework and technology stack overview
- Key findings and conclusions
- Directory structure summary
- Routing configuration
- Navigation patterns
- API communication overview
- File paths for key components

**Best for**: Quick understanding of what the frontend is and how it works

---

### 2. FRONTEND_ANALYSIS.md
**Purpose**: Deep dive technical analysis of the frontend codebase
**Contents**:
- Detailed framework analysis
- Complete directory structure with descriptions
- Routing setup explained
- Navigation & back button implementation details
- Homepage/root URL structure
- Component architecture with data flow diagrams
- State management approach
- Key features and implementations
- Vite configuration details
- TypeScript types definitions
- API communication specifications
- Entry points

**Best for**: Understanding technical details and implementation patterns

---

### 3. FRONTEND_QUICK_REFERENCE.md
**Purpose**: Developer quick reference guide for common tasks
**Contents**:
- Key files with descriptions
- Navigation flow explanations
- Back button behavior analysis
- State management summary
- Component props patterns
- Files by purpose (what to modify for different tasks)
- Configuration files overview
- Build & run commands

**Best for**: Quick lookup when working on specific features or modifications

---

### 4. FRONTEND_ARCHITECTURE.txt
**Purpose**: Visual ASCII diagrams of architecture and data flow
**Contents**:
- HTTP request/response flow diagram
- URL & page structure diagram
- Navigation patterns diagram
- State management overview
- Routing definition
- API endpoints specification
- React hooks and utilities listing

**Best for**: Visual learners who want to see the overall structure and data flow

---

## Quick Navigation

### I want to understand...

**...what framework is being used?**
- Read: FRONTEND_EXPLORATION_SUMMARY.md - Section "Framework"
- Read: FRONTEND_ANALYSIS.md - Section 1 "Overall Framework & Technology Stack"

**...where the conversation page is located?**
- Read: FRONTEND_EXPLORATION_SUMMARY.md - Section "Conversation Page Location"
- Check file: `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/components/ChatMessagesView.tsx`

**...how routing works?**
- Read: FRONTEND_EXPLORATION_SUMMARY.md - Section "Routing Configuration"
- Read: FRONTEND_ANALYSIS.md - Section 3 "Routing Setup (React Router v7)"
- View: FRONTEND_ARCHITECTURE.txt - Section "ROUTING DEFINITION"
- Check file: `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/main.tsx`

**...how navigation and back buttons are implemented?**
- Read: FRONTEND_EXPLORATION_SUMMARY.md - Section "Navigation & Back Button Patterns"
- Read: FRONTEND_ANALYSIS.md - Section 4 "Navigation & Back Button Implementation"
- Read: FRONTEND_QUICK_REFERENCE.md - Section "Navigation Flow"
- View: FRONTEND_ARCHITECTURE.txt - Section "NAVIGATION PATTERNS"
- Check files:
  - `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/App.tsx` (lines 145, 43)
  - `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/components/InputForm.tsx` (lines 136-140)

**...the homepage/root URL structure?**
- Read: FRONTEND_EXPLORATION_SUMMARY.md - Section "Homepage/Root URL Structure"
- Read: FRONTEND_ANALYSIS.md - Section 5 "Homepage/Root URL Structure"
- View: FRONTEND_ARCHITECTURE.txt - Section "URL & PAGE STRUCTURE" - Homepage section
- Check files:
  - `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/components/WelcomeScreen.tsx`
  - `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/src/main.tsx`

**...the overall directory structure?**
- Read: FRONTEND_EXPLORATION_SUMMARY.md - Section "Directory Structure"
- Read: FRONTEND_ANALYSIS.md - Section 2 "Frontend Directory Structure"

**...the component architecture?**
- Read: FRONTEND_ANALYSIS.md - Section 6 "Component Architecture"
- View: FRONTEND_ARCHITECTURE.txt - Section "HTTP REQUEST / RESPONSE FLOW"

**...how to add a back button?**
- Read: FRONTEND_QUICK_REFERENCE.md - Section "To Add Back Button"

**...how to change styling?**
- Read: FRONTEND_QUICK_REFERENCE.md - Section "To Change Styling"

**...how to add a new agent?**
- Read: FRONTEND_QUICK_REFERENCE.md - Section "To Add New Agent"

---

## File Structure Quick Reference

```
Frontend Root: /Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/

Source Files:
├── src/main.tsx                          [Entry point, routing]
├── src/App.tsx                           [Main app, conversation logic]
├── src/components/
│   ├── WelcomeScreen.tsx                [Landing page]
│   ├── ChatMessagesView.tsx             [Conversation display]
│   ├── InputForm.tsx                    [Shared input component]
│   ├── ActivityTimeline.tsx             [Agent activity timeline]
│   ├── ThinkingStream.tsx               [AI thinking display]
│   ├── agents/
│   │   ├── MyLocalAgent.tsx             [Local agent config]
│   │   ├── GeminiAgent.tsx              [Gemini agent]
│   │   └── RAGAgent.tsx                 [RAG agent]
│   ├── registry/
│   │   └── AgentRegistry.tsx            [Agent registry]
│   └── ui/                              [Reusable UI components]
├── lib/
│   ├── apis/agent/index.ts              [API functions]
│   ├── types/index.ts                   [TypeScript types]
│   └── utils.ts                         [Utilities]
└── hooks/
    └── useSelectedAgent.ts              [Agent selection hook]

Configuration Files:
├── package.json                         [Dependencies]
├── vite.config.ts                       [Vite configuration]
├── tsconfig.json                        [TypeScript config]
└── index.html                           [HTML entry point]
```

---

## Key Concepts

### Routes
- `/` - Homepage (WelcomeScreen)
- `/c/:conversationId` - Conversation page (ChatMessagesView)

### State Management
- React Hooks only (useState, useRef, useCallback, useEffect)
- Custom hook: useSelectedAgent()
- URL params: conversationId
- No Redux or Context API

### Navigation
1. Homepage → Conversation: User submits query → navigate('/c/{id}')
2. Conversation → Homepage: User clicks "New Search" → window.location.reload()
3. Browser back: Uses { replace: true } so browser back doesn't work as expected

### API Endpoints
- POST `/backend/agent/{agentURL}` - Submit query (streaming)
- GET `/backend/{agentURL}/conversation/{conversationId}` - Fetch messages

---

## Common Development Tasks

### Find where to add a feature...
→ Read FRONTEND_QUICK_REFERENCE.md "Files by Purpose" section

### Understand data flow...
→ View FRONTEND_ARCHITECTURE.txt or read FRONTEND_ANALYSIS.md Section 6

### Find specific UI component...
→ Check FRONTEND_ANALYSIS.md Section 2 directory structure

### Debug routing issue...
→ Check main.tsx and App.tsx, read routing sections in any document

### Modify styling...
→ Components use Tailwind CSS classes, see FRONTEND_QUICK_REFERENCE.md "To Change Styling"

### Add new agent type...
→ See FRONTEND_QUICK_REFERENCE.md "To Add New Agent"

---

## Technology Stack Summary

- **Framework**: React 19.0.0
- **Build Tool**: Vite 6.3.4
- **Routing**: React Router DOM v7.5.3
- **Styling**: Tailwind CSS v4.1.5
- **UI Components**: Radix UI
- **Language**: TypeScript 5.7.2
- **Icons**: lucide-react
- **Markdown**: react-markdown
- **LangChain**: @langchain/core, @langchain/langgraph-sdk

---

## Questions & Answers

**Q: Is this Next.js?**
A: No, it's React 19 with Vite (not Next.js). See FRONTEND_EXPLORATION_SUMMARY.md.

**Q: How do I run the frontend?**
A: See FRONTEND_QUICK_REFERENCE.md "Build & Run Commands" section.

**Q: Where do I modify the homepage?**
A: Edit `src/components/WelcomeScreen.tsx`. See FRONTEND_ANALYSIS.md Section 5.

**Q: How does the app navigate between pages?**
A: See FRONTEND_QUICK_REFERENCE.md "Navigation Flow" or FRONTEND_ARCHITECTURE.txt "NAVIGATION PATTERNS".

**Q: Where is the API communication code?**
A: In `src/lib/apis/agent/index.ts`. See FRONTEND_ANALYSIS.md Section 10.

**Q: How do I add a back button?**
A: See FRONTEND_QUICK_REFERENCE.md "To Add Back Button" section.

---

## Document Maintenance Notes

- Documentation created: November 14, 2025
- Framework version: React 19.0.0, Vite 6.3.4, React Router v7.5.3
- Project directory: `/Users/user/Code/github/maloferriol/my-local-ai-agent/frontend/`

To update documentation:
1. If adding/removing routes: Update main.tsx, FRONTEND_ANALYSIS.md Section 3, FRONTEND_ARCHITECTURE.txt
2. If changing components: Update FRONTEND_ANALYSIS.md Section 2 (directory) and Section 6
3. If changing API endpoints: Update FRONTEND_ANALYSIS.md Section 10, FRONTEND_ARCHITECTURE.txt
4. If changing navigation logic: Update FRONTEND_ANALYSIS.md Section 4, FRONTEND_QUICK_REFERENCE.md "Navigation Flow"

