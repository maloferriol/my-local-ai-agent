// import { geminiAgentRegistry } from "@/components/agents/GeminiAgent";
// import { ragAgentRegistry } from "@/components/agents/RAGAgent";
import { myLocalAgentRegistry } from "@/components/agents/MyLocalAgent";

// this is the agent registry
export const agentRegistry = {
  // "Gemini Agent": geminiAgentRegistry,
  // "RAG Agent": ragAgentRegistry,
  "My Local Agent": myLocalAgentRegistry,
};

// this is the agent lists
export type AgentType = keyof typeof agentRegistry;

export interface SelectedAgentParams {
  selectedAgent: AgentType;
  setSelectedAgent: (value: AgentType) => void;
}

// Note: stateful hooks moved to src/hooks/useSelectedAgent.ts to satisfy Fast Refresh