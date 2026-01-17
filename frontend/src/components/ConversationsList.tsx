import { ConversationSummary } from "@/lib/apis/agent";
import { ConversationItem } from "./ConversationItem";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2 } from "lucide-react";

interface ConversationsListProps {
  conversations: ConversationSummary[];
  isLoading: boolean;
  selectedConversationId?: number;
  onSelectConversation: (conversationId: number) => void;
}

export function ConversationsList({
  conversations,
  isLoading,
  selectedConversationId,
  onSelectConversation,
}: ConversationsListProps) {
  return (
    <ScrollArea className="flex-1 min-h-0">
      <div className="space-y-2 p-3">
        {isLoading && conversations.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-neutral-400" />
          </div>
        ) : conversations.length === 0 ? (
          <p className="text-sm text-neutral-400 text-center py-8">
            No conversations yet
          </p>
        ) : (
          conversations.map((conversation) => (
            <ConversationItem
              key={conversation.id}
              conversation={conversation}
              isSelected={selectedConversationId === conversation.id}
              onClick={onSelectConversation}
            />
          ))
        )}
      </div>
    </ScrollArea>
  );
}
