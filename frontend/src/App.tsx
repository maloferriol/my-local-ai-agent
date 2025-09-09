import type { ChatMessage, Conversation } from "@/lib/types";
import { RoleType } from "@/lib/types";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { getAgentResponse, getConversation } from "@/lib/apis/agent";
import { useSelectedAgent } from "@/hooks/useSelectedAgent";

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<Record<string, ProcessedEvent[]>>({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  const [chats, setChats] = useState<ChatMessage[]>([]);
  const chatsRef = useRef<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [thinkingContent, setThinkingContent] = useState<string>("");
  const [isThinking, setIsThinking] = useState<boolean>(false);
  // select agent states
  const { selectedAgent, setSelectedAgent } = useSelectedAgent();
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchConversation = async () => {
      if (conversationId) {
        console.log("Fetching conversation with ID:", conversationId)
        setIsLoading(true);
        console.log("parseInt parseInt parseInt Fetching conversation with ID:", parseInt(conversationId, 10));
        const conversation = await getConversation(parseInt(conversationId, 10), `agent/my_local_agent`);
        console.log("Fetched conversation:", conversation)
        if (conversation) {
          setChats(conversation.messages);
        } else {
          // Handle case where conversation is not found
          console.error("Conversation not found");
          // maybe redirect to home page
          navigate('/', { replace: true });
        }
        setIsLoading(false);
      }
    };
    fetchConversation();
  }, [conversationId, navigate]);

  useEffect(() => {
    chatsRef.current = chats;
    // check the scroll area
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [chats]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !isLoading &&
      chats.length > 0
    ) {
      const lastMessage = chats[chats.length - 1];
      if (lastMessage && lastMessage.role === RoleType.Assistant && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [chats, isLoading, processedEventsTimeline]);

  // Helper: Build a Conversation payload that includes only the latest user message
  const buildLatestOnlyConversation = useCallback(
    (idParam: string | undefined, newUserMessage: ChatMessage): Conversation => {
      const trimmedContent = (newUserMessage.content ?? "").trim();
      return {
        id: idParam ? parseInt(idParam, 10) : 0,
        messages: [
          {
            ...newUserMessage,
            content: trimmedContent,
          },
        ],
      };
    },
    []
  );

  const handleSubmit = useCallback(
    (submittedInputValue: string, agentURL: string, eventInfo: (data: any) => any, queryExtraInfo: any) => {

      // I didn't accept this change as I don't understand why we would need this isLoading check
      // if (!submittedInputValue.trim() || isLoading) return;
      if (!submittedInputValue.trim()) return;
      setProcessedEventsTimeline([]);
      // Reset thinking state for new request
      setIsThinking(false);
      hasFinalizeEventOccurredRef.current = false;
      // test the func
      const getAnswer = async (inputQuery: Conversation) => {
        console.log("inputQuery", inputQuery)
        let message: string = "";
        let processedEvent: ProcessedEvent | null = null;
        // Reset thinking content at the start of a new message
        setThinkingContent("");
        const res = await getAgentResponse(inputQuery, agentURL);
        if ("error" in res) {
          // set the error message
          setChats((chats) => [
            ...(chats || []),
            {
              role: RoleType.System,
              content: res.error,
              id: Date.now().toString(),
            },
          ]);
          console.error("No response from assistant: ", res.error);
        } else { 
          const reader = res.body?.getReader();
          if (!reader) throw new Error("body is not available");
          const decoder = new TextDecoder("utf-8");
          let buffer: string = "";
          // start to process response
          while (true){
            const { value, done } = await reader.read();
            buffer += decoder.decode(value, {stream: true});
            setIsLoading(!done);
            if (done) break;
            const lines = buffer.split("\n");
            buffer = lines.pop()!;
            for (const line of lines) {
              if (line !== ""){
                const data = JSON.parse(line);

                if (data.stage === 'metadata' && data.conversation_id && !conversationId) {
                  navigate(`/c/${data.conversation_id}`, { replace: true });
                }

                const { titleDetails, extraInfo } = eventInfo(data);
                processedEvent = {
                  title: titleDetails,
                  data: extraInfo,
                };
                if (processedEvent && !hasFinalizeEventOccurredRef.current) {
                  setProcessedEventsTimeline((prevEvents) => [
                    ...prevEvents,
                    processedEvent!,
                  ]);
                }

                // Handle thinking stage
                if (data.stage === "thinking") {
                  setIsThinking(true);
                  if (data.response) {
                    setThinkingContent(prev => prev + data.response);
                  }
                }

                // Handle tool results
                if (data.stage === "tool_result") {
                  // Add tool result to activity timeline
                  const toolEvent = {
                    title: `Tool: ${data.tool}`,
                    data: `Result: ${data.result}`,
                  };
                  setProcessedEventsTimeline((prevEvents) => [
                    ...prevEvents,
                    toolEvent,
                  ]);
                }

                // Handle tool errors
                if (data.stage === "tool_error") {
                  const errorEvent = {
                    title: `Tool Error: ${data.tool}`,
                    data: `Error: ${data.error}`,
                  };
                  setProcessedEventsTimeline((prevEvents) => [
                    ...prevEvents,
                    errorEvent,
                  ]);
                }

                // Handle incremental content chunks
                if (data.stage === "content") {
                  if (data.response) {
                    message += data.response;
                    // Always update the last Assistant message or create new one
                    setChats((chats) => {
                      const lastMessage = chats[chats.length - 1];
                      if (lastMessage && lastMessage.role === RoleType.Assistant){
                        // Update existing Assistant message
                        const updatedLastMessage = {
                          ...lastMessage,
                          content: message,
                        };
                        return [
                          ...chats.slice(0, chats.length - 1),
                          updatedLastMessage,
                        ];
                      } else {
                        // Create new Assistant message
                        return [
                          ...chats,
                          {
                            role: RoleType.Assistant,
                            content: message,
                            id: Date.now().toString(),
                          }
                        ];
                      }
                    });
                  }
                }

                // Handle finalize answer - end of a turn marker
                if (data.stage === "finalize_answer") {
                  setIsThinking(false);
                  // no-op for now; message has already been accumulated via content
                }
              }
            }
          }
        }
      };

      const newUserMessage: ChatMessage = {
        role: RoleType.User,
        content: submittedInputValue,
        id: Date.now().toString(),
        model: queryExtraInfo.reasoning_model
      }

      setChats((chats) => [
        ...(chats || []),
        newUserMessage,
      ]);

      // execute the func with only the latest user message
      const latestOnlyPayload = buildLatestOnlyConversation(conversationId, newUserMessage);
      getAnswer(latestOnlyPayload);
    }, [isLoading, conversationId, navigate]
  );

  const handleCancel = useCallback(() => {
    window.location.reload();
  }, []);

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      <main className="flex-1 flex flex-col overflow-hidden max-w-4xl mx-auto w-full">
        <div
          className={`flex-1 overflow-y-auto ${chats.length === 0 ? "flex" : ""}`}
        >
          {chats.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={isLoading}
              onCancel={handleCancel}
              agentControl={{selectedAgent, setSelectedAgent}}
            />
          ) : (
            <ChatMessagesView
              messages={chats}
              isLoading={isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
              agentControl={{selectedAgent, setSelectedAgent}}
              thinkingContent={thinkingContent}
              isThinking={isThinking}
            />
          )}
        </div>
      </main>
    </div>
  );
}
