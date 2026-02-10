"""Core drone coordinator agent using LangChain and OpenAI."""

import os
import json
import re
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

from .prompts import SYSTEM_PROMPT
from .tools import get_agent_tools


class DroneCoordinatorAgent:
    """AI Agent for coordinating drone operations."""
    
    def __init__(
        self,
        pilot_service,
        drone_service,
        mission_service,
        conflict_detector,
        sheets_service,
        google_api_key: str = None
    ):
        """
        Initialize the drone coordinator agent.
        
        Args:
            pilot_service: PilotService instance
            drone_service: DroneService instance
            mission_service: MissionService instance
            conflict_detector: ConflictDetector instance
            sheets_service: SheetsService instance
            openai_api_key: OpenAI API key
        """
        self.pilot_service = pilot_service
        self.drone_service = drone_service
        self.mission_service = mission_service
        self.conflict_detector = conflict_detector
        self.sheets_service = sheets_service
        
        # Get API key
        self.api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key not provided")
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-flash-latest",
            temperature=0,
            google_api_key=self.api_key,
            max_retries=0
        )
        
        # Get tools
        tool_functions = get_agent_tools(
            pilot_service=pilot_service,
            drone_service=drone_service,
            mission_service=mission_service,
            conflict_detector=conflict_detector,
            sheets_service=sheets_service
        )

        self.tool_map = {func.__name__: func for func in tool_functions}
        self.tool_descriptions = [
            f"- {func.__name__}: {func.__doc__.strip().splitlines()[0]}"
            for func in tool_functions
            if func.__doc__
        ]

        # Chat history
        self.chat_history: List[Dict[str, str]] = []
    
    def run(self, user_input: str) -> str:
        """
        Process user input and return agent response.
        
        Args:
            user_input: User's message
        
        Returns:
            Agent's response
        """
        try:
            replacement_intent = any(
                phrase in user_input.lower()
                for phrase in ["replace pilot", "replacement pilot", "reassign", "reassignment", "urgent reassignment"]
            )
            mission_match = re.search(r"\b(?:M|PRJ)\d+\b", user_input, re.IGNORECASE)
            pilot_match = re.search(r"\bP\d+\b", user_input, re.IGNORECASE)
            if replacement_intent and pilot_match and "get_pilot_details" in self.tool_map:
                pilot_id = pilot_match.group(0).upper()
                pilot_result = self.tool_map["get_pilot_details"](pilot_id=pilot_id)
                try:
                    pilot_payload = json.loads(pilot_result)
                except json.JSONDecodeError:
                    pilot_payload = {}

                current_assignment = pilot_payload.get("current_assignment")
                if not current_assignment:
                    return f"Pilot {pilot_id} is not assigned to a mission right now."

                if "find_replacement_pilot" in self.tool_map:
                    tool_result = self.tool_map["find_replacement_pilot"](mission_id=current_assignment)
                    followup = (
                        f"Tool result:\n{tool_result}\n\n"
                        "Provide a concise, user-friendly response."
                    )
                    final_msg = self.llm.invoke(f"{SYSTEM_PROMPT}\n\n{followup}")
                    response = getattr(final_msg, "content", str(final_msg))
                    self.chat_history.append({"role": "user", "content": user_input})
                    self.chat_history.append({"role": "assistant", "content": response})
                    if len(self.chat_history) > 20:
                        self.chat_history = self.chat_history[-20:]
                    return response

            if replacement_intent and not mission_match:
                return "Which mission ID should I use to find a replacement pilot?"
            if replacement_intent and mission_match and "find_replacement_pilot" in self.tool_map:
                mission_id = mission_match.group(0).upper()
                tool_result = self.tool_map["find_replacement_pilot"](mission_id=mission_id)
                followup = (
                    f"Tool result:\n{tool_result}\n\n"
                    "Provide a concise, user-friendly response."
                )
                final_msg = self.llm.invoke(f"{SYSTEM_PROMPT}\n\n{followup}")
                response = getattr(final_msg, "content", str(final_msg))
                self.chat_history.append({"role": "user", "content": user_input})
                self.chat_history.append({"role": "assistant", "content": response})
                if len(self.chat_history) > 20:
                    self.chat_history = self.chat_history[-20:]
                return response

            history_text = "\n".join(
                f"{m['role'].title()}: {m['content']}" for m in self.chat_history
            )
            tool_text = "\n".join(self.tool_descriptions)
            instruction = (
                "You may call tools by responding with JSON only. "
                "Format: {\"tool\": \"name\", \"args\": {}}. "
                "If no tool is needed, respond with {\"final\": \"...\"}."
            )

            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Available tools:\n{tool_text}\n\n"
                f"Conversation so far:\n{history_text}\n\n"
                f"User: {user_input}\n\n"
                f"{instruction}\n"
                "Return JSON only."
            )

            raw = self.llm.invoke(prompt)
            content = getattr(raw, "content", str(raw))

            response = ""
            try:
                payload = json.loads(content)
            except json.JSONDecodeError:
                payload = {"final": content}

            if "tool" in payload:
                tool_name = payload.get("tool")
                args = payload.get("args", {})
                tool_fn = self.tool_map.get(tool_name)
                if not tool_fn:
                    response = f"Unknown tool: {tool_name}"
                else:
                    tool_result = tool_fn(**args)
                    followup = (
                        f"Tool result:\n{tool_result}\n\n"
                        "Provide a concise, user-friendly response."
                    )
                    final_msg = self.llm.invoke(f"{SYSTEM_PROMPT}\n\n{followup}")
                    response = getattr(final_msg, "content", str(final_msg))
            else:
                response = payload.get("final", content)

            self.chat_history.append({"role": "user", "content": user_input})
            self.chat_history.append({"role": "assistant", "content": response})

            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]

            return response
        
        except Exception as e:
            error_text = str(e)
            if "ResourceExhausted" in error_text or "429" in error_text:
                return (
                    "Gemini API quota exceeded for this key. "
                    "Please wait for quota reset or use a different key."
                )
            error_msg = f"I encountered an error: {error_text}"
            print(f"Agent error: {e}")
            return error_msg
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.chat_history = []
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """
        Get formatted chat history.
        
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        return self.chat_history.copy()
