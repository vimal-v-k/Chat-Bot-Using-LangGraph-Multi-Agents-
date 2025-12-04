# # import asyncio
# # import logging
# # from datetime import datetime
# # from langgraph.graph import END, StateGraph,START
# # from langgraph.runtime import Runtime
# # from memory_agent import utils
# # from memory_agent.context import Context
# # from memory_agent.state import State
# # from langchain_mcp_adapters.client import MultiServerMCPClient
# # from pydantic import BaseModel, Field
# # from typing import Literal
# # from langchain_core.messages import SystemMessage
# # from langgraph.checkpoint.memory import InMemorySaver
# # from memory_agent import mcp_wrapper as mcp
# # from langchain_core.messages import AIMessage, ToolMessage
# # from langchain_core.runnables import RunnableConfig
# # from memory_agent.configuration import Configuration
# # from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage


# # logger = logging.getLogger(__name__)


# # async def store_memory(state: State):
# #     print(f"Current Activity: {state.messages[-1].additional_kwargs.get('agent_name')}")
# #     current_activity = state.messages[-1].additional_kwargs.get('agent_name')
# #     print(f"Current activity: {current_activity}")
# #     return {"messages": state.messages[-1]}



# # class TestDriveState(State):
# #     user_id: str = ""  # Add default
# #     vehicle_model: str = ""  # Add default
# #     current_tool: dict = None
# #     current_mcp_server: str = None

# # class GeneralState(State):
# #     user_id: str



# # # Step 1: Create MCP client and load tools
# # async def setup_mcp_client(runtime: Runtime[Context]):
# #     if getattr(runtime.context, "mcp_client", None) is None:
# #         runtime.context.mcp_client  = MultiServerMCPClient(
# #             {
# #                 "Sales": {
# #                     "transport": "streamable_http",
# #                     "url": "http://localhost:8800/mcp",
# #                 },
# #                 # "Service": {
# #                 #     "transport": "streamable_http",
# #                 #     "url": "http://localhost:8900/mcp",
# #                 # }
# #             }
# #         )
# #     return runtime.context.mcp_client


# # async def initialize_llm(runtime: Runtime[Context]):
# #     """Load LLM once and store in runtime.context"""
# #     if getattr(runtime.context, "llm", None) is None:
# #         runtime.context.llm = utils.load_chat_model(runtime.context.model)
# #         print("LLM Loaded once and stored in context.")


# # # 3. Create Test Drive Agent  
# # async def test_drive_node(state: TestDriveState, runtime: Runtime[Context]):
# #     """Extract the user's state from the conversation and update the memory."""
# #     await initialize_llm(runtime)
# #     user_id = runtime.context.user_id
# #     # model = runtime.context.model
# #     llm = runtime.context.llm
# #     system_prompt = runtime.context.testdrive_prompt
# #     formatted = f"User ID: {user_id}"
# #     sys = system_prompt.format(user_info=formatted, time=datetime.now().isoformat())
    
# #     client = await setup_mcp_client(runtime)
# #     mcp_tools = await client.get_tools()
# #     print("MCP Tools Loaded:", [tool.name for tool in mcp_tools])

# #     # llm = utils.load_chat_model(model)
# #     # print("LLM Loaded:", llm)

# #     msg = await llm.bind_tools([*mcp_tools]).ainvoke(
# #         [{"role": "system", "content": sys}, *state.messages]
# #     )
# #     print("Test Drive Node Message:", msg)

# #     msg.additional_kwargs["agent_name"] = "Lead Management"
# #     print("Lead Management Agent Invoked")
# #     return {"messages": [msg]}




# # # async def lead_tools_node(state: TestDriveState, runtime: Runtime[Context]):
# # #     """Run Lead Management tools using MCP and LLM."""
# # #     if getattr(runtime.context, "llm", None) is None:
# # #         await initialize_llm(runtime)
# # #     # Fetch tools from all servers
# # #     llm = runtime.context.llm
# # #     # MCP_SERVERS = {
# # #     #     "Sales": {"transport": "streamable_http", "url": "http://localhost:8800/mcp"},
# # #     #     "Service": {"transport": "streamable_http", "url": "http://localhost:8900/mcp"},
# # #     # }
# # #     client = await setup_mcp_client(runtime)

# # #     tools = []
# # #     server_tool_map = {}  # Map tool name to server
# # #     print("Loading tools from MCP servers...")
# # #     print("MCP_SERVERS:", client.servers.keys())
# # #     print("MCP Server iterms", client.servers.keys())
# # #     print("Look here ")
# # #     print(client.servers.keys(),"This is for keys")
# # #     print(client.servers.items(),"This is for items")
# # #     for server_name, server_config in client.servers.keys():
# # #         server_tools = await mcp.apply(server_name, server_config, mcp.GetTools())
# # #         tools.extend(server_tools)
# # #         for tool in server_tools:
# # #             server_tool_map[tool["function"]["name"]] = server_name
    
# # #     # Load LLM
# # #     # llm = utils.load_chat_model(runtime.context.model)
# # #     formatted = f"User ID: {runtime.context.user_id}"
# # #     sys = runtime.context.testdrive_prompt.format(user_info=formatted, time=datetime.now().isoformat())

# # #     try:
# # #     # Call LLM with bound tools
# # #         response = await llm.bind_tools(tools).ainvoke(
# # #             [{"role": "system", "content": sys}, *state.messages]
# # #         )
# # #     except Exception as e:
# # #         logger.error(f"LLM invocation failed: {e}")
# # #         return {"messages": state.messages, "current_tool": None}

# # #     response.additional_kwargs["agent_name"] = "Lead Management"
    


# # #     # -------- Track selected tool if model called one --------
# # #     current_tool = None
# # #     # Only consider responses that are AI messages with tool calls
# # #     from langchain_core.messages import AIMessage, ToolMessage

# # #     if isinstance(response, AIMessage) and getattr(response, "tool_calls", None):
# # #         current_tool = next(
# # #             (
# # #                 tool
# # #                 for tool in tools
# # #                 if tool["function"]["name"] == response.tool_calls[0].get("name")
# # #             ),
# # #             None,
# # #         )
    

# # #     state.current_tool = current_tool
# # #     # Safely assign server_name from map instead of metadata
# # #     if current_tool:
# # #         state.current_mcp_server = server_tool_map.get(current_tool["function"]["name"])
# # #     else:
# # #         state.current_mcp_server = None

# # #     # -------- Handle "I don't know" or "other server more relevant" --------
# # #     IDK_RESPONSE = "I don't know"
# # #     OTHER_SERVERS_MORE_RELEVANT = "Other servers more relevant"

# # #     if response.content in (IDK_RESPONSE, OTHER_SERVERS_MORE_RELEVANT):
# # #         # Only setup routing if this is not immediately after a tool call
# # #         if not isinstance(state.messages[-1], ToolMessage):
# # #             return {"current_mcp_server": None}

# # #     # -------- Return messages and the current tool (if any) --------
# # #     return {"messages": [response], "current_tool": current_tool}
# # async def lead_tools_node(state: TestDriveState, runtime: Runtime[Context]):
# #     """Run Lead Management tools using MCP and LLM."""
    
# #     # Ensure LLM is initialized
# #     if getattr(runtime.context, "llm", None) is None:
# #         await initialize_llm(runtime)

# #     llm = runtime.context.llm
# #     client = await setup_mcp_client(runtime)

# #     print("Loading tools from MCP servers...")

# #     # ✅ CORRECT APPROACH: Get tools directly as StructuredTool objects
# #     mcp_tools = await client.get_tools()
# #     print("✅ MCP Tools Loaded:", [tool.name for tool in mcp_tools])

# #     # Format system prompt
# #     formatted = f"User ID: {runtime.context.user_id}"
# #     sys = runtime.context.testdrive_prompt.format(
# #         user_info=formatted, 
# #         time=datetime.now().isoformat()
# #     )

# #     # LLM call with bound tools
# #     try:
# #         response = await llm.bind_tools(mcp_tools).ainvoke(
# #             [{"role": "system", "content": sys}, *state.messages]
# #         )
# #     except Exception as e:
# #         logger.error(f"LLM invocation failed: {e}")
# #         import traceback
# #         traceback.print_exc()
# #         return {"messages": state.messages, "current_tool": None}

# #     response.additional_kwargs["agent_name"] = "Lead Management"

# #     # Track if a tool was called
# #     has_tool_call = (
# #         isinstance(response, AIMessage) and 
# #         hasattr(response, "tool_calls") and 
# #         response.tool_calls
# #     )
    
# #     current_tool = None
# #     if has_tool_call:
# #         tool_call = response.tool_calls[0]
# #         tool_name = tool_call.get("name")
        
# #         # Find the matching tool object
# #         current_tool = next(
# #             (tool for tool in mcp_tools if tool.name == tool_name),
# #             None
# #         )
        
# #         if current_tool:
# #             print(f"🔧 Tool call detected: {tool_name}")
# #         else:
# #             print(f"⚠️ Tool '{tool_name}' not found in available tools")

# #     # Update state
# #     state.current_tool = current_tool
# #     state.current_mcp_server = "Sales" if current_tool else None  # Since we only have Sales server

# #     return {"messages": [response], "current_tool": current_tool}


# # # async def run_tool_node(state: TestDriveState, config: RunnableConfig):
# # #     """Execute the selected MCP tool."""
# # #     # Nothing to run if no current tool or server
# # #     if not state.current_tool or not state.current_mcp_server:
# # #         print("No tool selected, skipping run_tool_node")
# # #         return {"messages": state.messages}

# # #     server_name = state.current_mcp_server
# # #     configuration = Configuration.from_runnable_config(config)
# # #     mcp_servers = configuration.mcp_server_config["mcpServers"]
# # #     server_config = mcp_servers[server_name]

# # #     last_msg = state.messages[-1]
# # #     if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
# # #         print("Last message has no tool_calls, skipping tool execution")
# # #         return {"messages": state.messages}

# # #     tool_call = state.messages[-1].tool_calls[0]

# # #     try:
# # #         tool_output = await mcp.apply(
# # #             server_name,
# # #             server_config,
# # #             mcp.RunTool(tool_call["name"], **tool_call["args"]),
# # #         )
# # #     except Exception as e:
# # #         tool_output = f"Error executing tool: {e}"

# # #     return {"messages": [ToolMessage(content=tool_output, tool_call_id=tool_call["id"])]}
# # async def run_tool_node(state: TestDriveState, runtime: Runtime[Context]):
# #     """Execute the selected MCP tool."""
# #     if not state.current_tool:
# #         print("❌ No tool selected, skipping run_tool_node")
# #         return {"messages": state.messages}

# #     last_msg = state.messages[-1]
# #     if not hasattr(last_msg, "tool_calls") or not last_msg.tool_calls:
# #         print("❌ Last message has no tool_calls, skipping tool execution")
# #         return {"messages": state.messages}

# #     tool_call = last_msg.tool_calls[0]
# #     tool_name = tool_call.get("name")
# #     tool_args = tool_call.get("args", {})
# #     tool_call_id = tool_call.get("id", "")
    
# #     try:
# #         # Get the MCP client and tools
# #         client = await setup_mcp_client(runtime)
# #         mcp_tools = await client.get_tools()
        
# #         # Find the tool by name
# #         tool_to_execute = None
# #         for tool in mcp_tools:
# #             if tool.name == tool_name:
# #                 tool_to_execute = tool
# #                 break
        
# #         if not tool_to_execute:
# #             error_msg = f"❌ Tool '{tool_name}' not found in available MCP tools"
# #             print(error_msg)
# #             return {
# #                 "messages": [
# #                     ToolMessage(
# #                         content=error_msg,
# #                         tool_call_id=tool_call_id
# #                     )
# #                 ]
# #             }

# #         # Execute the tool
# #         print(f"🔧 Executing tool: {tool_name} with args: {tool_args}")
# #         tool_output = await tool_to_execute.ainvoke(tool_args)
# #         print(f"✅ Tool output: {tool_output}")
        
# #         # Convert output to string if it's not already
# #         if not isinstance(tool_output, str):
# #             tool_output = str(tool_output)
            
# #     except Exception as e:
# #         logger.error(f"❌ Error executing tool: {e}")
# #         import traceback
# #         traceback.print_exc()
# #         tool_output = f"❌ Error executing tool '{tool_name}': {str(e)}"

# #     return {
# #         "messages": [
# #             ToolMessage(
# #                 content=tool_output,
# #                 tool_call_id=tool_call_id
# #             )
# #         ]
# #     }


# # async def run_tool_node_wrapper(state: TestDriveState, runtime: Runtime[Context]):
# #     """Wrapper to pass RunnableConfig from runtime to run_tool_node"""
# #     return await run_tool_node(state, runtime.config)


# # # Conditional routing: after lead_tools_node
# # # def route_after_tools(state: TestDriveState):
# # #     if state.current_tool:
# # #         return "run_tool"
# # #     return "lead"  # else go back to lead
# # def route_after_tools(state: TestDriveState):
# #     """Route based on whether we called a tool or not"""
# #     last_msg = state.messages[-1]
    
# #     # If we just called a tool, execute it
# #     if state.current_tool:
# #         return "run_tool"
    
# #     # If the last message is from AI and has content (asking user question),
# #     # we should exit and wait for user response
# #     if isinstance(last_msg, AIMessage) and last_msg.content:
# #         return END  # Exit the loop
    
# #     # Otherwise continue the conversation
# #     return "lead"


# # testdrive_builder = StateGraph(TestDriveState)
# # testdrive_builder.add_node("lead", test_drive_node)
# # testdrive_builder.add_node("tools", lead_tools_node)
# # testdrive_builder.add_node("run_tool", run_tool_node_wrapper)
# # testdrive_builder.add_edge(START, "lead")
# # testdrive_builder.add_edge("lead", "tools") 
# # testdrive_builder.add_conditional_edges("tools", route_after_tools, ["run_tool", "lead"])
# # testdrive_builder.add_edge("run_tool","lead")
# # test_drive_agent = testdrive_builder.compile()







# # # # 4. Create Main Router Agent
# # # def route_to_agent(state: State):
# # #     """Route to appropriate subgraph based on user intent"""
# # #     msg = state.messages[-1]
# # #     # Add routing logic based on message content
# # #     if "service" in msg.content.lower():
# # #         return "service_booking"
# # #     elif "test drive" in msg.content.lower():
# # #         return "test_drive"
# # #     return "store_memory"


# # class IntentClassification(BaseModel):
# #     """
# #     Represents the detected intent behind the user's message.
# #     Used by the LLM to determine which agent or workflow to route the user to.
# #     """

# #     intent: Literal["service_booking", "lead", "general"] = Field(
# #         description=(
# #             "The user's primary intent inferred from their latest message or context. "
# #             "Must be one of the following:\n\n"
# #             "- **service_booking** → The user wants to schedule, confirm, modify, "
# #             "or inquire about a vehicle service or maintenance appointment.\n\n"
# #             "- **lead** → The user expresses interest in purchasing, financing, or learning more "
# #             "about a vehicle or dealership offering. They might ask about car prices, "
# #             "model availability, financing options, trade-ins, or test drives.\n\n"
# #             "- **general** → The message does not clearly fit the above categories, "
# #             "such as greetings, casual chat, or unrelated inquiries."
# #         )
# #     )

# #     confidence: float = Field(
# #         description=(
# #             "A confidence score between 0.0 and 1.0 representing how certain "
# #             "the model is about the classified intent."
# #         ),
# #         ge=0.0,
# #         le=1.0,
# #     )


# # async def handle_general(state: State, runtime: Runtime[Context]):
# #     """Handle general queries directly without calling specialized agents"""
# #     total_msgs = len(state.messages)
# #     user_id = state.user_id
# #     print("Length of messages",len(state.messages))        

# #     system_prompt = f"""You are a helpful assistant for a car dealership.
# #     Here is the conversation so far as summary and fact:
# #     if you need additional information or user speaking about previous conversation, use the retrieve_memory tool to get it as a fact.
# #     System Time: {datetime.now().isoformat()}"""

# #     model = runtime.context.model
# #     llm = utils.load_chat_model(model)
# #     response = await llm.bind_tools([]).ainvoke([
# #         {"role": "system", "content": system_prompt},
# #         *state.messages
# #     ])
# #     response.additional_kwargs["agent_name"] = "general_chat"
# #     return {"messages": [response]}


# # general_builder = StateGraph(GeneralState)
# # general_builder.add_node("general", handle_general)
# # general_builder.add_edge("__start__", "general")
# # # general_builder.add_conditional_edges("general", route_after_store, [END])
# # general_builder.add_edge("general", END)
# # general_agent = general_builder.compile()



# # # --- Corrected Function ---
# # async def route_to_agent(state: State, runtime: Runtime[Context]):
# #     """
# #     Use LLM to classify user intent and route to the correct agent.
# #     Fixes the BlockingError by using asynchronous calls (ainvoke, await).
# #     """
# #     model = runtime.context.model
# #     # Ensure utils.load_chat_model returns an async-compatible LLM
# #     llm = utils.load_chat_model(model)
# #     total_msgs = len(state.messages)
# #     user_id = state.user_id
    
# #     print("Length of messages", len(state.messages))    
# #     intent_classifier = llm.with_structured_output(IntentClassification)

# #     if total_msgs > 11:
# #         start_index = -10 # Get the last 10 messages
# #     else:
# #         start_index = 0 # Get all messages

# #     system_instructions = f"""
# #     You are an AI classifier for a Ford dealership conversation system.
# #     Your task is to identify the user's **primary intent** based on their latest messages in the conversation history and user input.
# #     The user could be interacting with different dealership departments such as service, sales, or general inquiries.
# #     Choose one of the following intents:

# #     1. **lead** → The user expresses interest in purchasing or learning more about vehicles,
# #        pricing, test drives, financing, or dealership offers.  
# #        Example keywords: "buy car", "price of Mustang", "test drive", "finance options",
# #        "new models", "sales inquiry".

# #     2. **general** → The user’s message doesn’t fit the above categories.  
# #        This includes greetings, casual conversation, dealership hours, or unrelated questions.
# #     - Return the classification as a JSON object following the schema.
# #     - If multiple intents appear, select the most dominant or relevant one.
# #     - Assign a confidence score between 0.0 and 1.0 indicating how confident you are.
# #     """ 

# #     classification = await intent_classifier.ainvoke(
# #         [
# #             SystemMessage(content=system_instructions.strip()),
# #             *state.messages[start_index:]
# #         ]
# #     )
# #     print("🧭 Intent Classification:", classification)
# #     # The return value is used by the router in LangGraph
# #     return classification.intent



# # # Build graph
# # main_builder = StateGraph(State, context_schema=Context)
# # main_builder.add_node("general", general_agent)
# # main_builder.add_node("lead", test_drive_agent)
# # main_builder.add_conditional_edges(
# #     "__start__", 
# #     route_to_agent,
# #     ["general","lead"]
# # )
# # main_builder.add_node("store_memory", store_memory)
# # main_builder.add_edge("general", "store_memory")
# # main_builder.add_edge("lead", "store_memory")
# # main_builder.add_edge("store_memory", END)



# # checkpointer = InMemorySaver()
# # graph = main_builder.compile(checkpointer=checkpointer)
# # graph.name = "MemoryAgent"
# # __all__ = ["graph"]
# import asyncio
# import logging
# from datetime import datetime
# from typing import Literal

# from langgraph.graph import END, StateGraph, START
# from langgraph.runtime import Runtime
# from langgraph.checkpoint.memory import InMemorySaver
# from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
# from langchain_core.runnables import RunnableConfig
# from langchain_mcp_adapters.client import MultiServerMCPClient

# from memory_agent import utils
# from memory_agent.context import Context
# from memory_agent.state import State

# logger = logging.getLogger(__name__)

# # --- 1. Helper Functions (Setup) ---

# async def setup_mcp_client(runtime: Runtime[Context]):
#     """Initialize MCP Client if not present."""
#     if getattr(runtime.context, "mcp_client", None) is None:
#         runtime.context.mcp_client = MultiServerMCPClient(
#             {
#                 "Sales": {
#                     "transport": "streamable_http",
#                     "url": "http://localhost:8800/mcp",
#                 },
#                 # Uncomment to add more servers
#                 # "Service": {
#                 #     "transport": "streamable_http",
#                 #     "url": "http://localhost:8900/mcp",
#                 # }
#             }
#         )
#     return runtime.context.mcp_client

# async def initialize_llm(runtime: Runtime[Context]):
#     """Load LLM once and store in runtime.context."""
#     if getattr(runtime.context, "llm", None) is None:
#         runtime.context.llm = utils.load_chat_model(runtime.context.model)
#         print("LLM Loaded once and stored in context.")

# async def store_memory(state: State):
#     """Log the activity before ending the turn."""
#     if state.messages:
#         agent_name = state.messages[-1].additional_kwargs.get('agent_name', 'General Agent')
#         print(f"Current Activity: {agent_name}")
#     return {"messages": state.messages[-1]}

# # --- 2. Node Definitions ---

# async def general_chat_node(state: State, runtime: Runtime[Context]):
#     """
#     The main node. It binds MCP tools to the LLM and processes the user message.
#     """
#     await initialize_llm(runtime)
#     llm = runtime.context.llm
    
#     # 1. Get Tools from MCP
#     client = await setup_mcp_client(runtime)
#     try:
#         mcp_tools = await client.get_tools()
#         print(f"✅ MCP Tools Loaded: {[tool.name for tool in mcp_tools]}")
#     except Exception as e:
#         logger.error(f"Failed to load MCP tools: {e}")
#         mcp_tools = []

#     # 2. Prepare Prompt
#     user_id = getattr(state, "user_id", "Unknown")
    
#     # Simple system prompt for general chat
#     system_msg = (
#         f"You are a helpful assistant for a car dealership.\n"
#         f"User ID: {user_id}\n"
#         f"Current Time: {datetime.now().isoformat()}\n"
#         f"You have access to tools to help answer questions about sales, inventory, etc.\n"
#         f"If the user asks something requiring data, use your tools."
#     )

#     # 3. Call LLM with Tools
#     try:
#         # Bind tools to the model
#         model_with_tools = llm.bind_tools(mcp_tools) if mcp_tools else llm
        
#         response = await model_with_tools.ainvoke(
#             [{"role": "system", "content": system_msg}, *state.messages]
#         )
#     except Exception as e:
#         logger.error(f"LLM invocation failed: {e}")
#         return {"messages": [AIMessage(content="I apologize, but I'm having trouble connecting to my brain right now.")]}

#     response.additional_kwargs["agent_name"] = "General Chat"
    
#     return {"messages": [response]}


# async def tool_execution_node(state: State, runtime: Runtime[Context]):
#     """
#     Executes the tool requested by the LLM in the previous step.
#     """
#     last_msg = state.messages[-1]
    
#     # Validation
#     if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
#         print("❌ No tool calls found in the last message.")
#         return {"messages": state.messages}

#     # Get Client to find the tool implementation
#     client = await setup_mcp_client(runtime)
#     mcp_tools = await client.get_tools()
    
#     tool_outputs = []

#     # Iterate over all tool calls (models might call multiple tools at once)
#     for tool_call in last_msg.tool_calls:
#         tool_name = tool_call.get("name")
#         tool_args = tool_call.get("args", {})
#         tool_call_id = tool_call.get("id")

#         print(f"🔧 Executing Tool: {tool_name} | Args: {tool_args}")

#         # Find the matching tool object from MCP
#         tool_to_execute = next((t for t in mcp_tools if t.name == tool_name), None)

#         if tool_to_execute:
#             try:
#                 # Execute
#                 output = await tool_to_execute.ainvoke(tool_args)
#                 output_str = str(output) # Ensure string format
#                 print(f"✅ Output: {output_str[:100]}...") # Print first 100 chars
#             except Exception as e:
#                 output_str = f"Error executing tool {tool_name}: {str(e)}"
#         else:
#             output_str = f"Error: Tool '{tool_name}' not found available tools."

#         # Create the ToolMessage result
#         tool_outputs.append(
#             ToolMessage(content=output_str, tool_call_id=tool_call_id, name=tool_name)
#         )

#     return {"messages": tool_outputs}


# async def tool_execution_wrapper(state: State, runtime: Runtime[Context]):
#     """Wrapper to maintain signature consistency."""
#     return await tool_execution_node(state, runtime)

# # --- 3. Routing Logic ---

# def should_continue(state: State) -> Literal["tools", "store_memory"]:
#     """
#     Determine if we need to run tools or finish the turn.
#     """
#     last_message = state.messages[-1]
    
#     # If the LLM made a tool call, go to tools node
#     if isinstance(last_message, AIMessage) and last_message.tool_calls:
#         return "tools"
    
#     # Otherwise, we are done
#     return "store_memory"

# # --- 4. Graph Construction ---

# workflow = StateGraph(State, context_schema=Context)

# # Add Nodes
# workflow.add_node("general_chat", general_chat_node)
# workflow.add_node("tools", tool_execution_wrapper)
# workflow.add_node("store_memory", store_memory)

# # Add Edges
# workflow.add_edge(START, "general_chat")

# # Conditional Edge: Chat -> Tools OR Chat -> Memory (End)
# workflow.add_conditional_edges(
#     "general_chat",
#     should_continue,
#     {
#         "tools": "tools",
#         "store_memory": "store_memory"
#     }
# )

# # Edge: Tools -> Chat (Loop back to let LLM interpret tool output)
# workflow.add_edge("tools", "general_chat")

# # Edge: Memory -> End
# workflow.add_edge("store_memory", END)

# # Compile
# checkpointer = InMemorySaver()
# graph = workflow.compile(checkpointer=checkpointer)
# graph.name = "MemoryAgent"

# __all__ = ["graph"]
import asyncio
import logging
from datetime import datetime
from typing import Literal, List, Dict, Any

from langgraph.graph import END, StateGraph, START
from langgraph.runtime import Runtime
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from memory_agent import utils
from memory_agent.context import Context
from memory_agent.state import State
# Ensure prompts are imported if not in context
from memory_agent.prompts import GENERAL_AGENT_PROMPT, TEST_DRIVE_PROMPT, SERVICE_BOOKING_PROMPT

logger = logging.getLogger(__name__)

# --- 1. Configuration & Helper Setup ---

# Map agent names to their specific prompts and allowed tools
AGENT_CONFIGS = {
    "general": {
        "prompt": GENERAL_AGENT_PROMPT,
        "tool_names": []  # General agent has no specific MCP tools, only prompt_switch
    },
    "sales": {
        "prompt": TEST_DRIVE_PROMPT,
        "tool_names": [
            "capture_and_recommend_vehicle", 
            "explain_vehicle_details", 
            "capture_financial_information", 
            "book_appointment_testdrive"
        ]
    },
    "service": {
        "prompt": SERVICE_BOOKING_PROMPT,
        "tool_names": [
            "check_service_availability", 
            "estimate_repair_cost", 
            "book_appointment_service"
        ]
    }
}

# Define the Prompt Switch Tool (Client-side tool)
@tool
def prompt_switch(agent_type: Literal["sales", "service"]) -> str:
    """
    Switch to a specialized agent persona (sales or service) by updating the session prompt and tools.
    Use this ONLY when the user's intent clearly shifts to buying a car (sales) or fixing a car (service).
    """
    # The return value here is less important than the side effect handled in the tool_node
    return f"Switched to {agent_type} agent."

async def setup_mcp_client(runtime: Runtime[Context]):
    """Initialize MCP Client if not present."""
    if getattr(runtime.context, "mcp_client", None) is None:
        runtime.context.mcp_client = MultiServerMCPClient(
            {
                "Sales": {
                    "transport": "streamable_http",
                    "url": "http://localhost:8800/mcp",
                },
                # Add Service server here if it runs on a different port, 
                # otherwise the "Sales" server in your code seems to hold all tools.
            }
        )
    return runtime.context.mcp_client

async def initialize_llm(runtime: Runtime[Context]):
    """Load LLM once and store in runtime.context."""
    if getattr(runtime.context, "llm", None) is None:
        runtime.context.llm = utils.load_chat_model(runtime.context.model)
        print("LLM Loaded once and stored in context.")

async def store_memory(state: State):
    """Log the activity before ending the turn."""
    if state.messages:
        agent_name = state.active_agent.capitalize() + " Agent"
        # Tag the last message with the agent name for the frontend
        state.messages[-1].additional_kwargs['agent_name'] = agent_name
        print(f"Current Activity: {agent_name}")
    return {"messages": state.messages[-1]}

# --- 2. Node Definitions ---

async def agent_node(state: State, runtime: Runtime[Context]):
    """
    The main node. It selects the prompt and tools based on 'active_agent'.
    """
    await initialize_llm(runtime)
    llm = runtime.context.llm
    
    # 1. Determine Current Agent Configuration
    current_agent_type = state.active_agent
    agent_config = AGENT_CONFIGS.get(current_agent_type, AGENT_CONFIGS["general"])
    
    print(f"🤖 Active Agent: {current_agent_type}")

    # 2. Get Tools from MCP
    client = await setup_mcp_client(runtime)
    available_tools = []
    
    try:
        # Fetch all tools from MCP
        all_mcp_tools = await client.get_tools()
        
        # Filter tools based on the active agent's allowed list
        allowed_names = agent_config["tool_names"]
        available_tools = [t for t in all_mcp_tools if t.name in allowed_names]
        
    except Exception as e:
        logger.error(f"Failed to load MCP tools: {e}")
        available_tools = []

    # 3. Add the 'prompt_switch' tool (Always available to General Agent, or everyone)
    # The General agent needs this to hand off. 
    # Specialized agents might not need to switch back, but good to have just in case.
    tools_to_bind = available_tools + [prompt_switch]

    # 4. Prepare Prompt
    user_id = getattr(state, "user_id", "Unknown")
    
    # Get the specific system prompt for this agent
    base_system_prompt = agent_config["prompt"]
    
    system_msg = (
        f"{base_system_prompt}\n\n"
        f"User ID: {user_id}\n"
        f"Current Time: {datetime.now().isoformat()}\n"
    )

    # 5. Call LLM with Tools
    try:
        # Bind tools to the model
        model_with_tools = llm.bind_tools(tools_to_bind)
        
        # We replace the system message dynamically based on state
        messages = [{"role": "system", "content": system_msg}] + state.messages
        
        response = await model_with_tools.ainvoke(messages)
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        return {"messages": [AIMessage(content="I apologize, but I'm having trouble connecting to my brain right now.")]}

    return {"messages": [response]}


async def tool_execution_node(state: State, runtime: Runtime[Context]):
    """
    Executes the tool requested by the LLM. 
    Handles 'prompt_switch' locally to update state.
    Handles other tools via MCP.
    """
    last_msg = state.messages[-1]
    
    # Validation
    if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
        return {"messages": state.messages}

    client = await setup_mcp_client(runtime)
    # We need to fetch tools again to get the runnable objects
    all_mcp_tools = await client.get_tools()
    
    tool_outputs = []
    new_state_updates = {}

    for tool_call in last_msg.tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_call_id = tool_call.get("id")

        print(f"🔧 Executing Tool: {tool_name} | Args: {tool_args}")

        # --- SPECIAL CASE: PROMPT SWITCH ---
        if tool_name == "prompt_switch":
            target_agent = tool_args.get("agent_type")
            if target_agent in AGENT_CONFIGS:
                # UPDATE THE STATE
                new_state_updates["active_agent"] = target_agent
                output_str = f"SYSTEM: Successfully switched context to {target_agent} agent. Proceed with their specific greeting."
                print(f"🔄 Switching Agent to: {target_agent}")
            else:
                output_str = f"Error: Unknown agent type {target_agent}"
        
        # --- STANDARD CASE: MCP TOOLS ---
        else:
            # Find the matching tool object from MCP
            tool_to_execute = next((t for t in all_mcp_tools if t.name == tool_name), None)

            if tool_to_execute:
                try:
                    output = await tool_to_execute.ainvoke(tool_args)
                    output_str = str(output)
                    print(f"✅ Output: {output_str[:100]}...") 
                except Exception as e:
                    output_str = f"Error executing tool {tool_name}: {str(e)}"
            else:
                output_str = f"Error: Tool '{tool_name}' not found."

        # Create the ToolMessage result
        tool_outputs.append(
            ToolMessage(content=output_str, tool_call_id=tool_call_id, name=tool_name)
        )

    # Return messages AND any state updates (like active_agent)
    return {"messages": tool_outputs, **new_state_updates}


async def tool_execution_wrapper(state: State, runtime: Runtime[Context]):
    """Wrapper to maintain signature consistency."""
    return await tool_execution_node(state, runtime)

# --- 3. Routing Logic ---

def should_continue(state: State) -> Literal["tools", "store_memory"]:
    """Determine if we need to run tools or finish the turn."""
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "store_memory"

# --- 4. Graph Construction ---

workflow = StateGraph(State, context_schema=Context)

# Add Nodes
workflow.add_node("agent_node", agent_node)
workflow.add_node("tools", tool_execution_wrapper)
workflow.add_node("store_memory", store_memory)
workflow.add_edge(START, "agent_node")
workflow.add_conditional_edges(
    "agent_node",
    should_continue,
    {
        "tools": "tools",
        "store_memory": "store_memory"
    }
)
workflow.add_edge("tools", "agent_node")
workflow.add_edge("store_memory", END)

# Compile
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
graph.name = "MemoryAgent"

__all__ = ["graph"]