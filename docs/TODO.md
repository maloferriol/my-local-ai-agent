# TODO

## Necessary

1. create models for data, like chat message, Tools, steps
   1. Do we add schema models for Retrival step or just logs ?
2. Create a UI for chat, end the while true loop
3. Create a first tool
4. Create a mcp server

## Workflow Agents

1. Create a class for agents
2. Create a way to add tools to agent so need to store the tool of an agent so need a Schema Model for Agents
3. Create a way to store prompts for agents

## Workflow DeepResearch

1. Create a tool to search the web
   1. maybe use mcp server for that
2. Add citation

## Workflow Local Database

1. Create a tool for Knowledge Retrieval
2. Create a local Vector Database
3. Integrate with OpenAI to get Embeddings
4. index a book in the database

## Workflow mixing Local Database with Search

1. Do Workflow DeepResearch + Workflow Local Database
2. Create a ReRanking model

## Workflow Evals

1. Update Database to add versionning
2. Update the DataLake to use LakeFS
3. Create an Eval Platform
4. Integrate Evals with tracing and versionning
   1. Evals should have links to Phoenix Arize
   2. Evals should have all the metadata to find the version of:
      1. the code, so a git version (make it mandatory to run evals on pushed code)
      2. the db, so Database version of the content
      3. the datalake, so the version of LakeFS
5. Evals should be retriable.
6. Offline inference
7. Online inference

## Workflow Documentation

1. Document the logging and tracing
2. Document the Telemetry Docker
