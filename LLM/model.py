import asyncio

import openai

from .providers import *
import json
from State import AgentState
from _types import Tool
from prompt_toolkit.key_binding import KeyBindings

class Model:
    PROVIDER_MAP = {
        "openai": OpenAIProvider,
        "groq": OpenAIProvider,
        "nvidia-nim": OpenAIProvider,
        "openrouter": OpenAIProvider
    }

    def __init__(self, model_id: str, state: AgentState, instructions: str, tool_list: list[Tool]=[]):

        self.state = state
        self.state.load_memory()
        self.intructions = instructions
        provider, id = model_id.split("/", 1)
        self.model_id = id
        self.provider = provider
        self.tool_list = tool_list
        self.kb = KeyBindings()

        self.provider_class = self.PROVIDER_MAP.get(provider)

        
        if provider in self.state.available_providers:
            try:
                self.model = self.provider_class(
                    model_id=self.model_id, 
                    apikey=self.state.available_providers[provider]["apikey"],
                    base_url=self.state.available_providers[provider]["base_url"],  
                    state=self.state, 
                    tool_list=self.tool_list)
            
                print(f"Model initialized with Provider: {provider} and Model: {self.model_id}")
            except openai.OpenAIError:
                self.model = None
                print(Color.c("Provider unvailable", fg="red"))
                print(f"Please use /login login before using the provider {provider}")
        else:
            self.model = None
            print(Color.c("Provider unvailable", fg="red"))
            print(f"Please use /login login before using the provider {provider}")


    async def run_model(self):
        # self.state.messages.append(self.model.user_message(prompt))
        actionHistory = {
            "role": "system",
            "content": self.state.build_task_history()
        }
        if not self.model:
            print(Color.c("Please check your login and select a model.", fg="yellow"))
            return

        first_user_message_index = self.state.messages.index(next(filter(lambda msg: msg["role"] == "user", self.state.messages)))
        result = await self.model.call_model(self.intructions, self.state.messages + [actionHistory], skills=self.state.available_skills,)
        # if result["response"] == "Sropped By u"
        if result["tool_calls"]:
            self.state.current_execution_mode = "tool"
            self.state.current_tool_calls = result["tool_calls"]
        else:
            self.state.reset_action_history()
            self.state.current_tool_calls = {}
            self.state.current_execution_mode = "idle"
        return result

    def set_model(self, id: str):
        provider, id = id.split("/", 1)
        self.model_id = id
        self.provider = provider
        self.model = self.provider_class(
            model_id=self.model_id, 
            apikey=self.state.available_providers[provider]["apikey"],
            base_url=self.state.available_providers[provider]["base_url"],
            tool_list=self.tool_list,
            state=self.state)
        print(f"Model changed to Provider: {provider} and Model: {self.model_id}")

    async def compact_messages(self, messages):

        old_messages = [self.model.system_message("""Your task is to create a summary of the provided conversation.
            if a summary already exists then add return the updated version
            Required format - Markdown

            Schema:
            ## Facts:

            ## User Proferences:

            ## Decision:

            ## Important Context:
            """)] + messages


        result = await self.model.call_model(
            instructions="",
            conversation=old_messages,
            print_output=False,
            tool_use = False,
            )

        return result
