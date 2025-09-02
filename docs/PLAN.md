# Misc

## Plan

1. get the python app a good cli argument
2. create a config file
3. create a prompt management system
4. Add Logging
5. Add 
6. Add Tools and MCP Servers
7. Add a Browser tool
8. Add a Vector Database
9. Index a Book in the Vector Database
10. Do EVALs

## What I want to learn

1. an app in terminal, like how to do args well and print pretty text in terminal
2. manage the prompt well, I feel like the prompts can become a pain quickly, maybe we should have a versionning
3. Manage logging, maybe add a database, and hopefuly tracing 

## TODO

### Database

1. create a UI in the terminal to select the conversation
2. let the user select old or new conversation
3. print the conversation history if a user selects

### Tools

1. create a Tool Class
2. Create a Tool Registry to manage the tools and their description
3. create first mcp
4. create classes for STEPS
5. Create a tool that list can be used to list other tools. Like Math would list addition and substractions

### Logging

1. [done] create a config
2. [done] create log files
3. Integrate with OpenTelemetry
4. Investigate creating a logging stack using Pydantic for schema and Pandas for displaying the data

-------
## Draft

1. Create Tool class
2. create tool registry


Add LakeFS to maintaint the Knowledge DATA 
Then use that during eval and inference to keep track of the version of the data. 

Then Enable tracking of data in Evals 

It will allow for comparison of the data between 2 runs 

Also integrate with a vector database

Create a Chat UI as it's quit annoying 