import { myLocalAgentRegistry } from "@/components/agents/MyLocalAgent";

// this is the agent registry
export const agentRegistry = {
  "My Local Agent": myLocalAgentRegistry,
};

// this is the agent lists
export type AgentType = keyof typeof agentRegistry;

export interface SelectedAgentParams {
  selectedAgent: AgentType;
  setSelectedAgent: (value: AgentType) => void;
}
