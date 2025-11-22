"""
AI Agent Service using LangChain and Google Gemini.
"""

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
            temperature=0.7,
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

        template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT CONTEXT:
- Current time is {current_time}.
- This is part of a conversation. Remember what you asked the user previously and use their responses to fill in missing information.

IMPORTANT RULES FOR SCHEDULING:
1. When user mentions relative time like "tomorrow at 5pm", calculate the ISO datetime based on current time.
2. Be SMART about what information is missing:
   - If user provides BOTH event name AND date/time (e.g., "schedule dinner tomorrow"), only ask for missing details (time if not specified, location if relevant).
   - If user is vague (e.g., "schedule something"), ask for ALL missing details: What? When? Where?
   - When user responds to your clarifying questions, ACCEPT their answer and use it to complete the task.
   - Only ask for information that is truly needed - don't be overly strict.
3. Ask for clarification only on information that is genuinely missing or unclear.
4. Combine clarifying questions into ONE message, not multiple separate questions.

{history}

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)

        agent = create_react_agent(self.llm, self.tools, prompt)

        return AgentExecutor(
            agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True
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
            # Create a custom prompt with history
            template_with_history = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT CONTEXT:
- Current time is {current_time}.
- This is part of a conversation. Remember what you asked the user previously and use their responses to fill in missing information.

IMPORTANT RULES FOR SCHEDULING:
1. When user mentions relative time like "tomorrow at 5pm", calculate the ISO datetime based on current time.
2. Be SMART about what information is missing:
   - If user provides BOTH event name AND date/time (e.g., "schedule dinner tomorrow"), only ask for missing details (time if not specified, location if relevant).
   - If user is vague (e.g., "schedule something"), ask for ALL missing details: What? When? Where?
   - When user responds to your clarifying questions, ACCEPT their answer and use it to complete the task.
   - Only ask for information that is truly needed - don't be overly strict.
3. Ask for clarification only on information that is genuinely missing or unclear.
4. Combine clarifying questions into ONE message, not multiple separate questions.

{history}

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

            prompt = PromptTemplate.from_template(template_with_history)
            agent = create_react_agent(self.llm, self.tools, prompt)
            executor = AgentExecutor(
                agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True
            )

            response = await executor.ainvoke(
                {"input": message, "current_time": current_time, "history": history_context}
            )
            response_text = response["output"]

            # Store in conversation history
            self.conversation_history.append(("User", message))
            self.conversation_history.append(("Assistant", response_text))

            return response_text
        except Exception as e:
            return f"I encountered an error: {e!s}"
