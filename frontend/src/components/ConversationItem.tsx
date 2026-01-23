import { ConversationSummary } from "@/lib/apis/agent";
import { MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConversationItemProps {
  conversation: ConversationSummary;
  isSelected?: boolean;
  onClick: (conversationId: number) => void;
}

export function ConversationItem({
  conversation,
  isSelected = false,
  onClick,
}: ConversationItemProps) {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Unknown date";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: date.getFullYear() !== new Date().getFullYear() ? "numeric" : undefined,
    });
  };

  return (
    <button
      onClick={() => onClick(conversation.id)}
      className={cn(
        "w-full px-3 py-2 rounded-lg text-left transition-colors duration-200 flex items-start gap-2 hover:bg-neutral-700",
        isSelected ? "bg-neutral-600" : "bg-neutral-800"
      )}
      title={conversation.title || "Untitled conversation"}
    >
      <MessageCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-neutral-400" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-neutral-200 truncate">
          {conversation.title || "Untitled"}
        </p>
        <p className="text-xs text-neutral-400 mt-0.5">
          {conversation.message_count} messages • {formatDate(conversation.timestamp)}
        </p>
      </div>
    </button>
  );
}
