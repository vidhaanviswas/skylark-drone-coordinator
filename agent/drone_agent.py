"""Core drone coordinator agent using LangChain and OpenAI."""

import os
from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage

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
        openai_api_key: str = None
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
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            openai_api_key=self.api_key
        )
        
        # Get tools
        tool_functions = get_agent_tools(
            pilot_service=pilot_service,
            drone_service=drone_service,
            mission_service=mission_service,
            conflict_detector=conflict_detector,
            sheets_service=sheets_service
        )
        
        # Convert to LangChain tools
        self.tools = [
            StructuredTool.from_function(func)
            for func in tool_functions
        ]
        
        # Create prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True
        )
        
        # Chat history
        self.chat_history = []
    
    def run(self, user_input: str) -> str:
        """
        Process user input and return agent response.
        
        Args:
            user_input: User's message
        
        Returns:
            Agent's response
        """
        try:
            # Run agent
            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": self.chat_history
            })
            
            # Get response
            response = result.get('output', 'I apologize, but I encountered an error processing your request.')
            
            # Update chat history
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=response))
            
            # Keep last 10 messages to avoid context length issues
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            
            return response
        
        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
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
        formatted_history = []
        for msg in self.chat_history:
            if isinstance(msg, HumanMessage):
                formatted_history.append({'role': 'user', 'content': msg.content})
            elif isinstance(msg, AIMessage):
                formatted_history.append({'role': 'assistant', 'content': msg.content})
        return formatted_history
