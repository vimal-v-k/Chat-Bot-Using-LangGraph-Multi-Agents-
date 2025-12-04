# """Define the runtime context information for the agent."""

# import os
# from dataclasses import dataclass, field, fields
# from typing_extensions import Annotated
# from typing import Optional, Any
# from memory_agent import prompts
# from langchain_mcp_adapters.client import MultiServerMCPClient


# @dataclass(kw_only=True)
# class Context:
#     """Main context class for the memory graph system."""

#     user_id: str = "default"
#     """The ID of the user to remember in the conversation."""

#     model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
#         default="google_genai/gemini-2.5-flash",
#         metadata={
#             "description": "The name of the language model to use for the agent. "
#             "Should be in the form: provider/model-name."
#         },
#     )

#     testdrive_prompt: str = prompts.TEST_DRIVE_PROMPT
#     service_booking_prompt: str = prompts.SERVICE_BOOKING_PROMPT

#     # New field to store the loaded LLM
#     llm: Optional[Any] = None  
#     mcp_client: Optional[MultiServerMCPClient] = None  # Declare it here

#     def __post_init__(self):
#         """Fetch env vars for attributes that were not passed as args."""
#         for f in fields(self):
#             if not f.init:
#                 continue

#             if getattr(self, f.name) == f.default:
#                 setattr(self, f.name, os.environ.get(f.name.upper(), f.default))
"""Define the runtime context information for the agent."""

import os
from dataclasses import dataclass, field, fields
from typing_extensions import Annotated
from typing import Optional, Any
from memory_agent import prompts # Ensure this imports your prompts.py file
from langchain_mcp_adapters.client import MultiServerMCPClient


@dataclass(kw_only=True)
class Context:
    """Main context class for the memory graph system."""

    user_id: str = "default"
    """The ID of the user to remember in the conversation."""

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="google_genai/gemini-2.5-flash",
        metadata={
            "description": "The name of the language model to use for the agent. "
            "Should be in the form: provider/model-name."
        },
    )

    # Prompts
    general_prompt: str = prompts.GENERAL_AGENT_PROMPT
    sales_prompt: str = prompts.TEST_DRIVE_PROMPT
    service_prompt: str = prompts.SERVICE_BOOKING_PROMPT

    # Runtime objects
    llm: Optional[Any] = None  
    mcp_client: Optional[MultiServerMCPClient] = None

    def __post_init__(self):
        """Fetch env vars for attributes that were not passed as args."""
        for f in fields(self):
            if not f.init:
                continue

            if getattr(self, f.name) == f.default:
                setattr(self, f.name, os.environ.get(f.name.upper(), f.default))