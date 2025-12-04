import asyncio
import datetime
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph_swarm import create_handoff_tool, create_swarm
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import convert_to_messages
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools



def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)


def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        print(f"Update from subgraph {graph_id}:")
        print("\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label

        print(update_label)
        print("\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")

today= datetime.date.today().strftime("%B %d, %Y")

async def main():
    from langgraph.checkpoint.memory import InMemorySaver

    checkpointer = InMemorySaver()
    # --- Sales Agent Setup ---
    # sales_client = MultiServerMCPClient(
    #     {
    #         "Sales": {
    #             "url": "http://0.0.0.0:8800/mcp",
    #             "transport": "streamable_http",
    #         }
    #     }
    # )
    # sales_tools = await sales_client.get_tools()
    # print(sales_tools)
    sales_agent = create_agent(
        model="google_genai:gemini-2.5-flash",
        tools= [create_handoff_tool(agent_name="service_agent",description="Forwards the conversation to the service agent for service-related queries.")],
        # tools= sales_tools + [create_handoff_tool(agent_name="service_agent",description="Forwards the conversation to the service agent for service-related queries.")],

        
        system_prompt=f"""
            **ROLE:** You are a helpful car sales assistant at oorji automotive dealership.
            **GOAL:** To identify the user's perfect vehicle using my tools.
            **CONTEXT:** The current date is {today}. Use this for date-related contextualization.

            ### **Core Rulebook**
            1.  **TOOLS ARE YOUR ONLY SOURCE:** For any data like inventory, pricing, or features, you **must** use your tools. **Never invent or guess.**
            2.  **SALES ONLY:** If the user asks about service or repairs, you **must** say, "That's a question for our Service Agent," and stop.

            ### **Mandatory Process: The One-Question Flow**
            When a user wants a vehicle recommendation, you must follow this exact conversational process.
            #### **Step 1: Collect Info ONE piece at a time.**
            Politely ask a single question, wait for the response, then ask the next.

            * ✅ **Correct Way (Do this):**
                * **You:** "To start, what kind of vehicle are you looking for? An SUV, sedan, or truck?"
                * **User:** "Probably an SUV."
                * **You:** "Great. And what's your approximate budget for the SUV?"

            * ❌ **Incorrect Way (Never do this):**
                * **You:** "Hi, to help you, I need to know your budget, preferred vehicle type, number of seats, and what features you want."

            #### **Step 2: Summarize and Confirm.**
            After you have a few key details, summarize them for the user to verify.
            * **Example:** "Okay, perfect. So, to confirm: you're looking for a family-friendly SUV with a budget around $40,000. Is that correct?"
            You may only proceed to use your tools *after* the user confirms your summary.
        """,
        name="sales_agent"
    )

    # # --- Service Agent Setup ---
    # service_client = MultiServerMCPClient(
    #     {
    #         "Demo": {
    #             "url": "http://0.0.0.0:8900/mcp",
    #             "transport": "streamable_http",
    #         }
    #     }
    # )
    # service_tools = await service_client.get_tools()
    service_agent = create_agent(
        model="google_genai:gemini-2.5-flash",
        tools= [create_handoff_tool(agent_name="sales_agent",description="Forwards the conversation to the sales agent for sales-related queries.")],
        
        # tools=service_tools + [create_handoff_tool(agent_name="sales_agent",description="Forwards the conversation to the sales agent for sales-related queries.")],
        
        system_prompt=f"""
        **ROLE:** You are an expert service booking assistant at oorji automotive dealership.
        **GOAL:** To quickly and accurately book vehicle service appointments using my tools.
        **CONTEXT:** The current date is {today}. Use this for date-related contextualization.

        ### **Core Rulebook**
        1.  **TOOLS ARE YOUR ONLY SOURCE:** For service availability, pricing, or user vehicle history, you **must** use your tools. **Never invent or assume.**
        2.  **SERVICE ONLY:** If the user asks about buying a car, trade-ins, or financing, you **must** say, "That's a question for our Sales Agent," and stop.

        ### **Mandatory Process: The One-Question Flow**
        When a user wants to book a service, you must follow this exact conversational process.

        #### **Step 1: Collect Info ONE piece at a time.**
        Politely ask a single question, wait for the response, then ask the next.

        * ✅ **Correct Way (Do this):**
            * **You:** "Hello! What service does your vehicle need today?"
            * **User:** "I need an oil change and tire rotation."
            * **You:** "Certainly. Do you have a preferred day or time for that?"

        * ❌ **Incorrect Way (Never do this):**
            * **You:** "To book your appointment, I need to know the service you want, your vehicle model, year, and your preferred date and time."

        #### **Step 2: Summarize and Confirm.**
        After you have the key details, summarize them for the user to verify.
        * **Example:** "Great. Just to confirm: you'd like to book an oil change and tire rotation, preferably for this Friday morning. Is that correct?"
        You may only proceed to use your tools to check availability *after* the user confirms your summary.
        """,
        name="service_agent"
    )

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    # --- workflow for swarm Setup ---
    workflow = create_swarm(
        agents=[sales_agent, service_agent],
        model=llm,
        default_active_agent="sales_agent",
    )
    print(workflow)
    app = workflow.compile(checkpointer=checkpointer)
    print(app)
    return app
    # from IPython.display import display, Image

    # with open("graph1.png", "wb") as f:
    #     f.write(app.get_graph().draw_mermaid_png())
    # # --- User Interaction Loop ---
    # print("Welcome to the automotive dealership assistant! How can we help you today?")
    # while True:
    #     config = {
    #             "configurable": {
    #                 "thread_id": "2",
    #             }
    #         }
    #     user_input = input("User: ")
    #     async for chunk in app.astream({"messages": [{"role": "user", "content": user_input}]},config=config):
    #         pretty_print_messages(chunk)
    #     print("\n")

if __name__ == "__main__":
    asyncio.run(main())