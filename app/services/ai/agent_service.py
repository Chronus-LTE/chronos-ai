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
- Use flexible, natural Vietnamese date formats (e.g., "Chủ nhật, 24/11/2025" or "Thứ Hai, ngày 25 tháng 11") or using the international ("November 23, 2025")

LANGUAGE RULES:
- Analyze the ENTIRE user question structure to detect language (not just keywords)
- Count language indicators across the WHOLE sentence:
  * Vietnamese indicators: "tôi", "có", "là", "được", "không", "gì", "ngày mai", "hôm nay", "khi nào", "ở đâu", "làm", "sao", "thế nào", "rảnh", "bận", etc.
  * English indicators: "I", "do", "am", "is", "are", "have", "tomorrow", "today", "free", "what", "when", "where", "how", "busy", etc.
- Ignore English technical terms/loanwords in Vietnamese sentences (e.g., "task", "meeting", "deadline")
- Language detection priority:
  1. If Vietnamese indicators >= 2, respond in Vietnamese
  2. If English indicators >= 2, respond in English
  3. If sentence structure follows Vietnamese grammar (Subject-Verb-Object with Vietnamese particles), respond in Vietnamese
  4. Default to English only if no clear indicators
- If user asks in English, respond ENTIRELY in English (no Vietnamese mixed in)
- If user asks in Vietnamese, respond ENTIRELY in Vietnamese (no English mixed in)
- Match the user's tone and formality level
- NEVER mix languages in a single response

RESPONSE STYLE:
- Be conversational and natural - vary your phrasing and structure
- Use friendly greetings like "Looking at...", "Let me check...", "Here's what I found..."
- Add personality with comments like "pretty busy", "looks good", "khá rảnh đấy"
- Mix up your emoji usage - don't be formulaic (📅 🎯 💼 ✨ 😊 can all work)
- When listing items, be flexible with format (bullet points, numbers, or natural prose)
- Include follow-up offers like "Need help with anything else?", "Want me to reschedule?"
- Keep tone positive and helpful (avoid robotic phrases)
- When displaying tasks, ALWAYS show the COMPLETE task title including time info (e.g., "Test exam (lúc 10:30)")
- Summarize when helpful instead of just listing everything

NATURAL RESPONSE EXAMPLES (use these as inspiration, not rigid templates):

When asked "Am I free tomorrow?" - be conversational:
```
Looking at your schedule for tomorrow (Monday, Nov 24)...

You've got a pretty full day ahead:
• Morning meeting from 5:00-8:00 AM
• Then a chat with your friend at 8:30-10:30 AM
• Plus you have that Test exam (at 10:30) due

Tomorrow's looking busy! 💼 Need me to reschedule anything?
```

When asked "Ngày mai tôi có task gì không?" - be natural in Vietnamese:
```
Để xem lịch ngày mai nhé (Thứ Hai, 24/11)...

Bạn có mấy việc này:
• Sáng sớm có meeting từ 5:00-8:00
• 8:30 có hẹn chat với bạn
• Còn có task Test exam (lúc 10:30) cần hoàn thành

Khá bận đấy! Cần sắp xếp lại gì không? 😊
```

KEY PRINCIPLES FOR NATURAL RESPONSES:
- Vary your greetings and structure (you can use icon if needed)
- Use conversational phrases like "Looking at...", "Let me check...", "You've got..."
- Add personality with friendly comments ("pretty full day", "khá bận đấy")
- Ask follow-up questions when appropriate
- Mix up your emoji usage - don't be formulaic
- Summarize naturally instead of just listing

CONTEXT:
- Current time: {current_time}
- Current timestamp: {current_timestamp}
- Timezone: Asia/Ho_Chi_Minh (UTC+7)

SCHEDULING RULES:
1. ALL tools require Unix timestamps (integers) for dates/times.
2. Calculate timestamps based on Current timestamp:
   - Tomorrow same time = current_timestamp + 86400
   - Next hour = current_timestamp + 3600
3. When user asks about availability (e.g., "Am I free?", "What's up tomorrow?"), ALWAYS check BOTH:
   - Calendar events (list_calendar_events)
   - Tasks (list_tasks)
4. Be smart about missing information - only ask what's truly needed
5. When user responds to your questions, USE their answer to complete the task
6. Combine multiple questions into ONE message
7. When scheduling with "break time", add at least 1800 seconds (30 mins) between meetings

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
        now = datetime.now()
        current_time = now.strftime("%d/%m/%Y %H:%M")
        current_timestamp = int(now.timestamp())

        # Build conversation history context
        history_context = ""
        if self.conversation_history:
            history_context = "CONVERSATION HISTORY:\n"
            for i, (msg_type, msg_content) in enumerate(self.conversation_history[-4:], 1):
                history_context += f"{i}. {msg_type}: {msg_content}\n"
            history_context += "\n"

        try:
            response = await self.agent_executor.ainvoke(
                {
                    "input": message,
                    "current_time": current_time,
                    "current_timestamp": current_timestamp,
                    "history": history_context,
                }
            )
            response_text = response["output"]

            # Store in conversation history
            self.conversation_history.append(("User", message))
            self.conversation_history.append(("Assistant", response_text))

            return response_text
        except Exception as e:
            traceback.print_exc()
            return f"I encountered an error: {e!s}"
