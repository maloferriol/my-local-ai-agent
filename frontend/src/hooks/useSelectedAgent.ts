import { useState } from "react";
import type { AgentType } from "@/components/registry/AgentRegistry";

export const useSelectedAgent = () => {
  const [selectedAgent, setSelectedAgent] = useState<AgentType>("My Local Agent");
  return { selectedAgent, setSelectedAgent };
};

/**
 * Last LLM Message:
 * 
 * I notice there are a couple of key issues in your code that are causing the HMR (Hot Module Replacement) and ESLint errors. Let me help you fix them.

The main error about Fast Refresh incompatibility in AgentRegistry.tsx is because the file is exporting both a regular object (agentRegistry) and a hook function (getSelectedAgentState). To fix this and follow React's best practices, we should:

Move the getSelectedAgentState hook into a proper custom hook (hooks must start with "use")
Move it to a separate file to comply with Fast Refresh requirements
Let me help you restructure this:

First, I'll create a new file for the hook:
 */

// import { useState } from "react";
// import { AgentType } from "@/components/registry/AgentRegistry";

// export const useSelectedAgent = () => {
//   const [selectedAgent, setSelectedAgent] = useState<AgentType>("My Local Agent");
//   console.log('selectedAgent', selectedAgent);
//   return { selectedAgent, setSelectedAgent };
// };
