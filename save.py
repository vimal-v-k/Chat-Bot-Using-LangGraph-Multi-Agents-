import asyncio
import json
import websockets
from updated2 import main, pretty_print_messages
import time
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
from memory_agent.graph import graph
from memory_agent.context import Context
from memory_agent.state import State
from langchain_core.messages import HumanMessage, AIMessage
from memory_agent import utils
from datetime import datetime
from zoneinfo import ZoneInfo


context =Context()


# MongoDB connection
client = MongoClient('mongodb+srv:/ngodb.net/')
db = client['ai_conversations']
users_collection = db['memory_demo']


active_connections = {}


async def create_new_session(user_id):
    """Create a new session for the user"""
    session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{generate_random_string(6)}"
    session_data = {
        "session_id": session_id,
        "created_at": datetime.now().isoformat(),
        "ended_at": None,
        "status": "open",
        "chat_history": [],
        "voice_transcriptions": [],
        "connection_details": {
            "room_url": "",
            "connected_at": datetime.now().isoformat(),
        },
        "session_summary": {}
    }
    
    # Update user document with new session
    result = users_collection.update_one(
        {"user_id": user_id},
        {"$push": {"sessions": session_data}}
    )
    
    return session_id




IST = ZoneInfo("Asia/Kolkata")
async def store_chat_message(user_id, session_id, message_data):
    """Store chat message in the session history"""

    # 1. Make sure the user document exists
    users_collection.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"sessions": []}},
        upsert=True
    )

    # 2. Make sure the session exists (create if missing)
    new_session = {
        "session_id": session_id,
        "created_at": datetime.now(IST).isoformat() + "Z",
        "ended_at": None,
        "status": "open",
        "chat_history": [],
        "voice_transcriptions": [],
        "connection_details": {},
        "session_summary": {}
    }

    users_collection.update_one(
        {
            "user_id": user_id,
            "sessions.session_id": {"$ne": session_id}   # session does NOT exist
        },
        {
            "$push": {"sessions": new_session}
        }
    )

    # 3. Push the new message
    users_collection.update_one(
        {
            "user_id": user_id,
            "sessions.session_id": session_id
        },
        {
            "$push": {"sessions.$.chat_history": message_data}
        }
    )



async def load_existing_transcripts(user_id, session_id):
    """Load existing voice transcripts from MongoDB for this session"""
    user_data = users_collection.find_one({"user_id": user_id})
    if not user_data:
        return []
    
    sessions = user_data.get("sessions", [])
    for session in sessions:
        if session.get("session_id") == session_id:
            return session.get("voice_transcriptions", [])
    
    return []


async def voice_transcript_watcher(user_id, session_id, websocket,compiled_graph,config):
    """
    Background task that watches MongoDB for new voice transcripts
    and pushes them to the WebSocket client in real-time
    """
    print(f"🎤 Started voice transcript watcher for user {user_id}, session {session_id}")
    
    sent_count = 0
    
    try:
        while True:
            await asyncio.sleep(1.5)  # Poll every 1.5 seconds
            
            # Query MongoDB for voice transcripts
            user_data = users_collection.find_one({"user_id": user_id})
            if not user_data:
                continue
            
            # Find the specific session
            current_session = None
            for session in user_data.get("sessions", []):
                if session.get("session_id") == session_id:
                    current_session = session
                    break
            
            if not current_session:
                continue
            
            voice_transcripts = current_session.get("voice_transcriptions", [])
            
            # Check for new transcripts
            if len(voice_transcripts) > sent_count:
                new_transcripts = voice_transcripts[sent_count:]
                current_activity_voice = None
                

                for transcript in new_transcripts:
                    if "role" not in transcript or not transcript["role"]:
                        continue
                    try:
                        message = {
                            "sender": "user" if transcript["role"] == "user" else "bot",
                            "text": transcript["content"],
                            "agent": transcript["agent_name"] if "agent_name" in transcript else "Voice Bot",
                            "role": transcript["role"],
                            "timestamp": transcript.get("timestamp", datetime.now().isoformat()),
                            "source": "voice"
                        }
                        current_activity_voice = transcript["agent_name"] if "agent_name" in transcript else "Voice Bot"
                        
                        # When updating state with async routing functions
                        if transcript["role"] == "user":
                            await compiled_graph.aupdate_state(
                                config=config,
                                values={"messages": [HumanMessage(
                                    content=transcript["content"],
                                    additional_kwargs={"source": "voice", "agent_name": "Voice Bot Agent"}
                                )]},
                                as_node = "store_memory"
                            )
                        else:
                            await compiled_graph.aupdate_state(
                                config=config,
                                values={"messages": [AIMessage(
                                    content=transcript["content"],
                                    additional_kwargs={"source": "voice", "agent_name": "Voice Bot Agent"}
                                )]},
                                as_node = "store_memory"
                            )
                        
                        await websocket.send(json.dumps(message))
                        print(f"📤 Sent voice transcript ({transcript['role']}): {transcript['content'][:50]}...")
                    
                    except Exception as e:
                        print(f"❌ Error sending voice transcript: {e}")
                        return  # Exit if WebSocket closed
                # End of for

                activity_map = {
                    "ServiceBookingAgent": "Service Booking",
                    "TestDriveAgent": "Lead Management"
                }

                current_activity_voice = activity_map.get(current_activity_voice, "General Chat")
                print(f"Current Activity: {current_activity_voice}")
                print(f"new_transcripts: {new_transcripts}")
                print(f"Length of new_transcripts: {len(new_transcripts)}")
                print(f"new_transcripts type: {type(new_transcripts)}")
                
                sent_count = len(voice_transcripts)

    
    except asyncio.CancelledError:
        print(f"🛑 Voice watcher stopped for user {user_id}")
    except Exception as e:
        print(f"❌ Voice watcher error: {e}")


async def register_websocket_connection(user_id, session_id, websocket,compiled_graph,config):
    """Register active WebSocket and start voice watcher"""
    # Cancel any existing watcher for this user
    if user_id in active_connections:
        old_task = active_connections[user_id].get("watcher_task")
        if old_task and not old_task.done():
            old_task.cancel()
    
    # Start new watcher task
    watcher_task = asyncio.create_task(
        voice_transcript_watcher(user_id, session_id, websocket,compiled_graph,config)
    )
    
    active_connections[user_id] = {
        "websocket": websocket,
        "session_id": session_id,
        "watcher_task": watcher_task
    }
    
    print(f"✅ Registered WebSocket for user {user_id}, session {session_id}")
    

async def unregister_websocket_connection(user_id):
    """Unregister WebSocket and stop watcher"""
    if user_id in active_connections:
        conn_data = active_connections[user_id]
        watcher_task = conn_data.get("watcher_task")
        
        if watcher_task and not watcher_task.done():
            watcher_task.cancel()
            try:
                await watcher_task
            except asyncio.CancelledError:
                pass
        
        del active_connections[user_id]
        print(f"❌ Unregistered WebSocket for user {user_id}")


async def handle_client(websocket):
    print("Client connected")
    # app = await main()
    app = graph

    user_id = None
    session_id = None
    
    try:
        # Wait for initial connection message with user_id
        connect_message = await websocket.recv()
        connect_data = json.loads(connect_message)
        user_id = connect_data.get("user_id")
        session_id = connect_data.get("session_id")
        print("This is the session id sent from the front end :")
        print("User id",user_id)
        print("Session id",session_id)
        if not user_id:
            raise ValueError("No user_id provided")
        if not session_id:
            print("Session id is not present (Front End Error)!!!")
            # session_id = await create_new_session(user_id)
            # print(f"Created new session {session_id} for user {user_id}")
        else:
            print(f"Front end session id creation successfull {session_id}!!!")
        
        
        config ={
                "configurable": {
                    "user_id": user_id,
                    "model": "google_genai/gemini-2.5-flash",
                    "testdrive_prompt": "\n\n        You are a highly advanced AI agent named \"Salma\" from ford dealership. Your primary goal is to assist potential customers by understanding their needs, recommending the perfect vehicle, and guiding them through the initial steps of the purchase process, culminating in a scheduled appointment.\n\n        Your personality is **empathetic, polite, knowledgeable, and incredibly human-like**. You are a conversationalist, not an interrogator.\n        You should generate responses only in English.\n\n\n### **Conversation Flow and Tool Logic**\n\n        **1. Initiation (`start_conversation`)**\n        * Begin the conversation by introducing yourself and referencing their interest in a vehicle. For example: \"Hi! I'm an AI assistant from [Company Name]. I see you've shown some interest in purchasing a new vehicle, and I was hoping I could help.\"\n        * Immediately ask for their consent to proceed: \"To find the best car for you, would it be okay if I ask a few quick questions about your preferences?\"\n\n        **2. Vehicle Recommendation (`capture_and_recommend_vehicle`)**\n        * Casually ask questions to understand their needs. **Do not ask all questions at once.** Weave them into the conversation naturally.\n            * *Example Questions*: “To start, could you please share what seating capacity you’re looking for – like 5 seater or 7 seater?”, \"What's your typical daily drive like?\", \"Will this be a family car, or mostly for commuting?\", \"Are there any specific features, like advanced safety, all-wheel drive or great fuel economy, that are important to you?\",\"Do you need towing capacity in your vehicle?\"\n        * Once you have gathered enough information (especially `vehicle_type`), use the `capture_and_recommend_vehicle` tool to suggest a suitable vehicle.\n        * Present the recommendation clearly: \"Based on what you've told me, I think the **[Vehicle Model]** would be a fantastic fit. What do you think?\"\n\n        **3. Vehicle Explanation (`explain_vehicle_details`)**\n        * Once the user shows interest in a specific model, offer more details: \"Excellent choice! Would you like me to tell you a bit more about the **[Vehicle Model]**?\"\n        * If they agree, use the `explain_vehicle_details` tool to provide a concise and engaging overview.\n\n        **4. Financial Information (`capture_financial_information`)**\n        * Transition smoothly: \"Great. To give you a clearer picture of the next steps, I just need to understand a little about your purchasing plan.\"\n        * **Crucial First Step**: You **MUST** first determine the payment method and residency status(resident_type) before asking further financial questions.\n            * Ask: \"Will you be considering a **cash purchase or financing**?\" (`payment_type`)\n            * **If `payment_type` is `Financing`**, then ask: \"And are you a **citizen or a resident**?\"\n        * **Dynamic Questioning**: Based on their answers, ask **ONLY** the relevant questions from the tool.\n            * **If `Financing` + `Citizen`**: You must ask about `employment_entity`, `retirement_age`, `salary_in_account`, `salary_after_social_insurance` one by one.\n            * **If `Financing` + `Resident`**: You must ask about `employment_entity`, `sponsorship_type`, `social_insurance`, `salary_in_appointment_letter` one by one.\n            * **General Questions**: For **ALL** customers (Cash or Finance), you must still ask about `3_months_at_current_job`,`financial_obligations`, `driving_license_validity`, `unpaid_trafic_fines`, and `status_of_simah` one by one. Frame these carefully, e.g., \"Just a couple of standard questions to ensure a smooth registration process...\"\n        * Always ask about a potential `trade_in`. Once they have provided their financial information, use the `capture_financial_information` tool. Should not proceed to booking without using the `capture_financial_information` tool.\n\n        **5. Booking & Follow-ups (Primary Goal)**\n        * Your main objective is to secure an appointment. Proactively suggest it: \"Thank you for all the information. The next best step would be to experience the car firsthand. I can book you in for a **test drive** or a visit to our **showroom**. What works for you?\"\n        * Use the `book_appointment` tool with the required details.        Ask questions! Be spontaneous! \n        {user_info}\n\n        System Time: {time}\n        \n        ",
                    "service_booking_prompt": "You are a sales executive at [Company Name], a car dealership.You are responsible for scheduling appointments for potential customers.            Ask questions! Be spontaneous! \n        {user_info}\n\n        System Time: {time}",
                    "thread_id": session_id
                    }
                }
        
        # Register this WebSocket connection and start voice watcher
        await register_websocket_connection(user_id, session_id, websocket, app, config)

        # Load and send existing voice transcripts
        existing_transcripts = await load_existing_transcripts(user_id, session_id)
        if existing_transcripts:
            print(f"📜 Sending {len(existing_transcripts)} existing voice transcripts")
            for transcript in existing_transcripts:
                message = {
                    "sender": "user" if transcript["role"] == "user" else "bot",
                    "text": transcript["content"],
                    "agent": transcript["agent_name"] if "agent_name" in transcript else "Voice Bot",
                    "role": transcript["role"],
                    "timestamp": transcript.get("timestamp", datetime.now(IST).isoformat()),
                    "source": "voice"
                }
                await websocket.send(json.dumps(message))
        
        async for message in websocket:
            start_time = time.time()
            request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            try:
                print(f"\n[Request {request_id}] Started processing")
                
                # Store user message
                user_message = {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.now(IST).isoformat(),
                    "agent": None
                }
                await store_chat_message(user_id, session_id, user_message)
                
                try:
                    parsed_message = json.loads(message)
                    user_input = parsed_message.get("text", message)
                except json.JSONDecodeError:
                    user_input = message

                async for chunk in app.astream(
                    input={
                            "messages": [
                            {
                                "content": user_input,
                                "type": "human"
                            }
                            ],
                            "user_name": user_id,
                            "user_id": user_id
                        },
                    config=config,
                    context=context,
                    # stream_mode=["debug","messages"]
                ):
                    chunk_time = time.time()
                    

                    for node_name, node_update in chunk.items():
                        messages = node_update.get("messages", [])

                        if messages:
                            last_message = messages[-1] if isinstance(messages, list) else messages
                            if node_name != "store_memory":                                

                                response = {
                                    "sender": "bot",
                                    "text": str(last_message.content),
                                    "agent": node_name,
                                    "role": last_message.type,
                                    "timestamp": datetime.now(IST).isoformat(),
                                    "timing": {
                                        "chunk_time": f"{(time.time() - chunk_time):.2f}s",
                                        "total_time": f"{(time.time() - start_time):.2f}s"
                                    },
                                }
                                
                                # Store assistant message
                                assistant_message = {
                                    "role": "assistant",
                                    "content": str(last_message.content),
                                    "timestamp": datetime.now(IST).isoformat(),
                                    "agent": node_name
                                }
                                await store_chat_message(user_id, session_id, assistant_message)
                                
                                await websocket.send(json.dumps(response))
                            else:
                                pass
                        

            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                print(error_msg)
                error_response = {
                    "sender": "bot",
                    "text": error_msg,
                    "agent": "system",
                    "role": "error",
                }
                await websocket.send(json.dumps(error_response))
    
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
        # Update session end time
        users_collection.update_one(
            {
                "user_id": user_id,
                "sessions.session_id": session_id
            },
            {
                "$set": {
                    "sessions.$.ended_at": datetime.now().isoformat(),
                    "sessions.$.status": "closed"
                }
            }
        )

def generate_random_string(length):
    """Generate random string for session ID"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def start_server():
    server = await websockets.serve(handle_client, "0.0.0.0", 8081)
    print("WebSocket server started on ws://localhost:8081")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_server())
