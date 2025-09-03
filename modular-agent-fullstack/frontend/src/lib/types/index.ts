export enum RoleType {
  User = 'user',
  Assistant = 'assistant',
  Tool = 'tool',
  System = 'system',
}

export interface Conversation {
  id: number;
  created_at?: string | null;
  updated_at?: string | null;
  title?: string | null;
  model?: string | null;
  metadata?: Record<string, any> | null;
  messages?: ChatMessage[];
}

export interface ChatMessage {
  id: string;
  role: RoleType;
  content?: string | null;
  timestamp?: string | null;
  thinking?: string | null;
  tool_name?: string | null;
  model?: string | null;
  metadata?: Record<string, any> | null;
}