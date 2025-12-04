# """Define the shared values."""

# from __future__ import annotations

# from dataclasses import dataclass

# from langchain_core.messages import AnyMessage
# from langgraph.graph import add_messages
# from typing_extensions import Annotated
# from dataclasses import dataclass, field
# from typing import Annotated, Any
# from uuid import uuid4

# @dataclass(kw_only=True)
# class State:
#     """Main graph state."""

#     messages: Annotated[list[AnyMessage], add_messages] 
#     """The messages in the conversation."""

#     user_name: str = field(default="Vikram")
#     """The user's name."""

#     user_id: str = field(default_factory=lambda: str(uuid4()))
#     """The user's ID."""

#     current_tool: dict[str, Any] = field(default_factory=dict)
#     """Current tool being processed."""
"""Define the shared values."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from uuid import uuid4

@dataclass(kw_only=True)
class State:
    """Main graph state."""

    messages: Annotated[list[AnyMessage], add_messages] 
    """The messages in the conversation."""

    user_name: str = field(default="Vikram")
    """The user's name."""

    user_id: str = field(default_factory=lambda: str(uuid4()))
    """The user's ID."""
    
    active_agent: Literal["general", "sales", "service"] = field(default="general")
    """The current active persona of the bot."""

    current_tool: dict[str, Any] = field(default_factory=dict)
    """Current tool being processed."""

__all__ = ["State"]