import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getConversations, ConversationSummary } from "@/lib/apis/agent";
import { ConversationsList } from "./ConversationsList";
import { Button } from "@/components/ui/button";
import { ChevronLeft, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConversationsSidebarProps {
  agentURL: string;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  onNewConversation?: () => void;
}

export function ConversationsSidebar({
  agentURL,
  isCollapsed = false,
  onToggleCollapse,
  onNewConversation,
}: ConversationsSidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { conversationId } = useParams<{ conversationId: string }>();

  useEffect(() => {
    const fetchConversations = async () => {
      setIsLoading(true);
      const data = await getConversations(agentURL);
      if (data) {
        setConversations(data);
      }
      setIsLoading(false);
    };

    fetchConversations();
  }, [agentURL]);

  const handleSelectConversation = (id: number) => {
    navigate(`/c/${id}`);
  };

  const handleNewConversation = () => {
    if (onNewConversation) {
      onNewConversation();
    }
    navigate("/");
  };

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-neutral-900 border-r border-neutral-700 transition-all duration-300",
        isCollapsed ? "w-0 min-w-0" : "w-64 min-w-[16rem]"
      )}
    >
      {!isCollapsed && (
        <>
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-neutral-700">
            <h2 className="text-sm font-semibold text-neutral-200">Conversations</h2>
            {onToggleCollapse && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleCollapse}
                className="p-1 h-auto text-neutral-400 hover:text-neutral-200"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* New Conversation Button */}
          <div className="px-3 py-2 border-b border-neutral-700">
            <Button
              onClick={handleNewConversation}
              className="w-full bg-neutral-700 hover:bg-neutral-600 text-neutral-100"
              size="sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Conversation
            </Button>
          </div>

          {/* Conversations List */}
          <ConversationsList
            conversations={conversations}
            isLoading={isLoading}
            selectedConversationId={
              conversationId ? parseInt(conversationId, 10) : undefined
            }
            onSelectConversation={handleSelectConversation}
          />
        </>
      )}

      {isCollapsed && onToggleCollapse && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCollapse}
          className="m-2 p-1 h-auto text-neutral-400 hover:text-neutral-200"
          title="Expand sidebar"
        >
          <ChevronLeft className="h-4 w-4 rotate-180" />
        </Button>
      )}
    </div>
  );
}
