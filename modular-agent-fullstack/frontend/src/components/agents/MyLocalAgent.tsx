import { useEffect, useState } from "react";
import { Cpu, Ghost, NotebookTabs, Binoculars, Waypoints, Bolt } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

// interface of the params
interface ExtraInfoParams {
  model: string;
  mode: string;
}

interface ModelSelectorParams {
  model: string;
  setModel: (value: string) => void;
}

interface ModeSelectorParams {
  mode: string;
  setMode: (value: string) => void;
}

// this hook is used as the state used in the RAG Agent
const useRagAgentState = () => {
  const [model, setModel] = useState("gpt-oss:20b");
  const [mode, setMode] = useState("default");
  return { model, setModel, mode, setMode };
};

// model selector
const ModelSelector = ({ model, setModel }: ModelSelectorParams) => {
  return (
    <Select value={model} onValueChange={setModel}>
      <SelectTrigger className="w-[160px] bg-transparent border-none cursor-pointer">
        <SelectValue placeholder="Model" />
      </SelectTrigger>
      <SelectContent className="bg-neutral-700 border-neutral-600 text-neutral-300 cursor-pointer">
        <SelectItem
          value="gpt-oss:20b"
          className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
        >
          <div className="flex items-center">
            <Ghost className="h-4 w-4 mr-2 text-blue-400" /> gpt-oss 20B
          </div>
        </SelectItem>
        <SelectItem
          value="gemma3:4b"
          className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
        >
          <div className="flex items-center">
            <Ghost className="h-4 w-4 mr-2 text-blue-400" /> Gemma 3
          </div>
        </SelectItem>
      </SelectContent>
    </Select>
  );
};

const ModeSelector = ({ mode, setMode }: ModeSelectorParams) => {
  return (
    <Select value={mode} onValueChange={setMode}>
      <SelectTrigger className="w-[130px] bg-transparent border-none cursor-pointer">
        <SelectValue placeholder="Mode" />
      </SelectTrigger>
      <SelectContent className="bg-neutral-700 border-neutral-600 text-neutral-300 cursor-pointer">
        <SelectItem
          value="default"
          className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
        >
          <div className="flex items-center">
            <Binoculars className="h-4 w-4 mr-2 text-green-400" /> Default
          </div>
        </SelectItem>
        <SelectItem
          value="hybrid"
          className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
        >
          <div className="flex items-center">
            <Bolt className="h-4 w-4 mr-2 text-red-400" /> Hybrid
          </div>
        </SelectItem>
        <SelectItem
          value="sparse"
          className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
        >
          <div className="flex items-center">
            <Waypoints className="h-4 w-4 mr-2 text-blue-400" /> Sparse
          </div>
        </SelectItem>
      </SelectContent>
    </Select>
  );
};

// event info list
interface StreamEventData {
  stage: string;
  metadata?: unknown;
  tool?: string;
  result?: string;
  error?: string;
  response?: string;
}

const eventInfo = (data: StreamEventData) => {
  let titleDetails: string = "";
  let extraInfo;
  // decide the stage
  switch(data.stage) {
    case "finalize_answer":
      titleDetails = "Finalizing the Answers";
      extraInfo = "Composing and presenting the final answer.";
      break;
    case "rag_search":
      const chunks = Array.isArray(data.metadata) ? data.metadata : [];
      const numChunks = chunks.length;
      titleDetails = "Search Knowledge Base Using RAG";
      extraInfo = `Gathered ${numChunks} chunks from RAG Database.`;
      break;
    case "reasoning":
      titleDetails = "Reasoning with Retrieved Information";
      extraInfo = "Analyzing and synthesizing information from retrieved chunks.";
      break;
    case "thinking":
      titleDetails = "LLM Thinking";
      extraInfo = "The LLM is processing the input and generating a response...";
      break;
    case "tool_result":
      titleDetails = `Tool: ${data.tool}`;
      extraInfo = `Executed with result: ${data.result}`;
      break;
    case "tool_error":
      titleDetails = `Tool Error: ${data.tool}`;
      extraInfo = `Error: ${data.error}`;
      break;
  }
  return { titleDetails, extraInfo }; 
}; 

const getQueryExtraInfo = ({ model, mode }: ExtraInfoParams) => {
  const reasoning_model = model;
  const rag_mode = mode;
  console.log('reasoning_model', reasoning_model);
  console.log('rag_mode', rag_mode);
  return { reasoning_model, rag_mode };
};

// build the fields of the agent content
const MyLocalAgentFields = ({ onReady }: { onReady: (extraInfo: { reasoning_model: string; rag_mode: string }, eventInfoFunc: (data: StreamEventData) => { titleDetails: string; extraInfo: unknown }, agentURL: string) => void }) => {
  const { model, setModel, mode, setMode } = useRagAgentState();
  useEffect(() => {
    const extraInfo = getQueryExtraInfo({ model, mode });
    const eventInfoFunc = eventInfo;
    const agentURL = "my_local_agent/invoke";
    onReady(extraInfo, eventInfoFunc, agentURL);
  }, [ model, mode ]);
  return (
    <>
      <div className="flex flex-row gap-2 bg-neutral-700 border-neutral-600 text-neutral-300 focus:ring-neutral-500 rounded-xl rounded-t-sm pl-2  max-w-[100%] sm:max-w-[90%]">
        <div className="flex flex-row items-center text-sm ml-2">
          <Cpu className="h-4 w-4 mr-2" />
          Model
        </div>
        <ModelSelector model={model} setModel={setModel} />
      </div>
      <div className="flex flex-row gap-2 bg-neutral-700 border-neutral-600 text-neutral-300 focus:ring-neutral-500 rounded-xl rounded-t-sm pl-2  max-w-[100%] sm:max-w-[90%]">
        <div className="flex flex-row items-center text-sm ml-2">
          <NotebookTabs className="h-4 w-4 mr-2" />
          Mode
        </div>
        <ModeSelector mode={mode} setMode={setMode} />
      </div>
    </>
  );    
};

// agent registry
export const myLocalAgentRegistry = () => {
  return {
    Fields: MyLocalAgentFields,
  };
};