from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage, AIMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import TypedDict, List
from core.memory._chat_memory import PostgresChatMemory
from langchain.schema import BaseMessage

class OnboardingState(TypedDict):
    messages: List[BaseMessage]
    current_step: str
    user_data: dict
    voice_call_scheduled: bool
    session_complete: bool

class OnboardingGraph:
    def __init__(self, memory: PostgresChatMemory):
        self.memory = memory
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)
        self.graph = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(OnboardingState)
        
        # Add nodes
        workflow.add_node("greeting", self.greeting_node)
        workflow.add_node("collect_basic_info", self.collect_basic_info_node)
        workflow.add_node("schedule_voice_call", self.schedule_voice_call_node)
        workflow.add_node("final_steps", self.final_steps_node)
        
        # Add edges
        workflow.add_edge("greeting", "collect_basic_info")
        workflow.add_edge("collect_basic_info", "schedule_voice_call")
        workflow.add_edge("schedule_voice_call", "final_steps")
        workflow.add_edge("final_steps", END)
        
        # Set entry point
        workflow.set_entry_point("greeting")
        
        return workflow.compile()
    
    async def greeting_node(self, state: OnboardingState):
        prompt = ChatPromptTemplate.from_template(
            "You are a friendly onboarding assistant. Greet the user and explain the onboarding process. "
            "Mention that we'll collect some basic information and schedule a voice call. "
            "Keep it warm and welcoming."
        )
        
        messages = await self.memory.get_messages()
        response = await self.llm.ainvoke(prompt.format_messages())
        
        await self.memory.add_message("ai", response.content)
        
        return {
            **state,
            "current_step": "greeting",
            "messages": messages + [response]
        }
    
    async def collect_basic_info_node(self, state: OnboardingState):
        # This node handles collecting user information
        user_message = state["messages"][-1] if state["messages"] else None
        
        if isinstance(user_message, HumanMessage):
            # Extract information from user message
            # This is simplified - you'd want more sophisticated extraction
            content = user_message.content.lower()
            
            if any(word in content for word in ["name", "called", "i'm", "i am"]):
                state["user_data"]["name_provided"] = True
            
            if "@" in content:
                state["user_data"]["email_provided"] = True
        
        # Check if we have enough info
        if state["user_data"].get("name_provided") and state["user_data"].get("email_provided"):
            response_text = "Great! I have your basic information. Now let's schedule a voice call to complete your onboarding."
        else:
            needed = []
            if not state["user_data"].get("name_provided"):
                needed.append("your name")
            if not state["user_data"].get("email_provided"):
                needed.append("your email")
            
            response_text = f"I still need {' and '.join(needed)}. Could you please provide that information?"
        
        await self.memory.add_message("ai", response_text)
        
        return {
            **state,
            "current_step": "collect_basic_info"
        }
    
    async def schedule_voice_call_node(self, state: OnboardingState):
        response_text = """
        Perfect! Now I'd like to schedule a voice call with you to complete the onboarding process. 
        This call will take about 10-15 minutes and will help us:
        
        1. Verify your information
        2. Answer any questions you might have
        3. Complete your account setup
        
        When would be a good time for you? Please provide a few time preferences.
        """
        
        await self.memory.add_message("ai", response_text)
        
        return {
            **state,
            "current_step": "schedule_voice_call",
            "voice_call_scheduled": True
        }
    
    async def final_steps_node(self, state: OnboardingState):
        response_text = """
        Excellent! Your onboarding chat is nearly complete. 
        I've scheduled your voice call and saved all your information.
        
        You'll receive a confirmation email shortly with:
        - Your call details
        - What to prepare for the call
        - Next steps
        
        Is there anything else you'd like to know before we finish?
        """
        
        await self.memory.add_message("ai", response_text)
        
        return {
            **state,
            "current_step": "final_steps",
            "session_complete": True
        }