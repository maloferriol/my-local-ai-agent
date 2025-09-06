import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Brain, ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";

interface ThinkingStreamProps {
  thinkingContent: string;
  isThinking: boolean;
}

export function ThinkingStream({
  thinkingContent,
  isThinking,
}: ThinkingStreamProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [hasContent, setHasContent] = useState(false);

  // Set hasContent to true when we first receive content
  useEffect(() => {
    if (thinkingContent) {
      setHasContent(true);
    }
  }, [thinkingContent]);

  if (!hasContent) return null;

  return (
    <Card className="border-none rounded-lg bg-neutral-700 mt-4">
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
