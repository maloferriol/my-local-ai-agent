import { Conversation } from "@/lib/types";

// this is used to fetch the data
export const getAgentResponse = async (query: Conversation, agentURL: string) => {
  try{
    const res = await fetch(`/backend/agent/${agentURL}`, {
      method: "POST",
      headers: {
          "Content-Type": "application/json",
      },
      body: JSON.stringify(query),
    });
    if (!res.ok) {
      const errorMsg = await res.text();
      throw new Error(`Server responded with ${res.status}: ${errorMsg}`);
    }
    return res;
  } catch (error) {
    console.error("Failed to get the response: ", error);
    return { "error": `Failed to get the agent response: ${error}`};
  }
};

export const getConversation = async (conversationId: number, agentURL: string) => {
  try {
    const res = await fetch(`/backend/${agentURL}/conversation/${conversationId}`);
    if (!res.ok) {
      const errorMsg = await res.text();
      throw new Error(`Server responded with ${res.status}: ${errorMsg}`);
    }
    const conversation: Conversation = await res.json();
    return conversation;
  } catch (error) {
    console.error("Failed to get the conversation: ", error);
    return null;
  }
};



