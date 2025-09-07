import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Brain, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { useState } from "react";

interface ThinkingStreamProps {
  thinkingContent: string;
  isThinking: boolean;
  isInitialyCollapsed: boolean;
}

export function ThinkingStream({
  thinkingContent,
  isThinking,
  isInitialyCollapsed,
}: ThinkingStreamProps) {
  const [isCollapsed, setIsCollapsed] = useState(isInitialyCollapsed);
  // Show component when there's thinking content or when actively thinking
  if (!thinkingContent && !isThinking) return null;

  return (
    <Card className="border-none rounded-lg bg-neutral-700 mt-4" style={{ width: '100%' }}>
      <CardHeader className="pb-2">
        <CardDescription className="flex items-center justify-between">
          <div
            className="flex items-center justify-start text-sm w-full gap-2 text-neutral-100 cursor-pointer"
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-blue-400" />
              Thinking Process
              {isThinking && (
                <Loader2 className="h-3 w-3 text-neutral-400 animate-spin ml-2" />
              )}
            </div>
            {isCollapsed ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronUp className="h-4 w-4" />
            )}
          </div>
        </CardDescription>
      </CardHeader>
      {!isCollapsed && (
        <ScrollArea className="max-h-60 overflow-y-auto">
          <CardContent>
            <div className="space-y-2">
              <p className="text-sm text-neutral-300 whitespace-pre-wrap">
                {thinkingContent || "Thinking..."}
              </p>
            </div>
          </CardContent>
        </ScrollArea>
      )}
    </Card>
  );
}
