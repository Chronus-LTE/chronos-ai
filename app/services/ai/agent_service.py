"""
AI Agent Service using LangChain and Google Gemini.
"""

import traceback
from datetime import datetime

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.services.tools.registry import ToolRegistry


class AIAgentService:
    """AI Agent Service for processing user requests."""

    def __init__(self, user_token: str):
        """
        Initialize AI Agent with user context.

        Args:
            user_token: User's Google OAuth access token
        """
        self.user_token = user_token
        self.conversation_history = []

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
            convert_system_message_to_human=True,
        )
        self.tools = self._setup_tools()
        self.agent_executor = self._setup_agent()

    def _setup_tools(self) -> list[Tool]:
        """Setup tools available to the agent."""
        tools = []
        # Initialize all registered tools
        # In a real scenario, we might want to selectively enable tools based on user permissions
        for tool_name, tool_class in ToolRegistry.get_all_tool_classes().items():
            try:
                tool_instance = tool_class(user_token=self.user_token)
                tools.extend(tool_instance.get_tools())
            except Exception as e:
                print(f"Failed to initialize tool {tool_name}: {e}")

        return tools

    def _setup_agent(self) -> AgentExecutor:
        """Setup the ReAct agent."""

        template = """You are a helpful AI assistant with access to tools. Answer questions and help with tasks.

Available tools:
{tools}

Use this EXACT format for your responses:

Question: the input question you must answer
Thought: think about what to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

CRITICAL FORMATTING RULES:
- ALWAYS start with "Thought:" after seeing a Question
- ALWAYS use "Action:" and "Action Input:" on separate lines
- NEVER skip the "Final Answer:" line
- If you don't need tools, go straight to "Final Answer:"

CONTEXT:
- Current time: {current_time}
- Timezone: Asia/Ho_Chi_Minh (UTC+7)

SCHEDULING RULES:
1. When user mentions relative time (e.g., "tomorrow at 5pm"), calculate ISO datetime from current time
2. Be smart about missing information - only ask what's truly needed
3. When user responds to your questions, USE their answer to complete the task
4. Combine multiple questions into ONE message
5. When scheduling with "break time", add at least 30 minutes between meetings

{history}

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)

        agent = create_react_agent(self.llm, self.tools, prompt)

        def _handle_error(error) -> str:
            """Handle parsing errors gracefully."""
            error_str = str(error)
            if "Could not parse LLM output" in error_str:
                return "I apologize, I had trouble formatting my response. Let me try again: Could you please rephrase your question?"
            return f"I encountered an error: {error_str}"

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=_handle_error,
            max_iterations=10,
            max_execution_time=60,
            early_stopping_method="generate",
        )

    async def process_message(self, message: str) -> str:
        """
        Process a user message and return the response.

        Args:
            message: User's input message

        Returns:
            AI's response
        """
        current_time = datetime.now().isoformat()

        # Build conversation history context
        history_context = ""
        if self.conversation_history:
            history_context = "CONVERSATION HISTORY:\n"
            for i, (msg_type, msg_content) in enumerate(self.conversation_history[-4:], 1):
                history_context += f"{i}. {msg_type}: {msg_content}\n"
            history_context += "\n"

        try:
            response = await self.agent_executor.ainvoke(
                {"input": message, "current_time": current_time, "history": history_context}
            )
            response_text = response["output"]

            # Store in conversation history
            self.conversation_history.append(("User", message))
            self.conversation_history.append(("Assistant", response_text))

            return response_text
        except Exception as e:
            traceback.print_exc()
            return f"I encountered an error: {e!s}"
