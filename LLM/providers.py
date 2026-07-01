# from abc import ABC, abstractmethod
import asyncio
import itertools
import re
import sys
import time

from openai import OpenAI
from platform import platform
import os
import inspect
import json
from typing import get_origin, get_args

from _types import LLMProvider, Tool
from State import AgentState
from frontend.term_colors import Color
from frontend.tui import Spinner


class OpenAIProvider(LLMProvider):

    def __init__(self, model_id: str, apikey: str, state: AgentState, tool_list: list[Tool] =[], base_url=None):
        self.base_url = base_url
        self.model_id = model_id
        self.state = state
        self.tool_declarations = self.build_tool_declarations(tool_list) if tool_list else []
        if self.base_url:
            self.model = OpenAI(api_key=apikey, base_url=self.base_url)
        else:
            self.model = OpenAI(api_key=apikey)

        # print(json.dumps(self.tool_declarations, indent=2))

    async def call_model(self, instructions: str, conversation: list[dict], print_output: bool = True, tool_use: bool = True):
        try:
            self.state.load_memory()
            # if len(self.state.messages) == 0:
            #     conversation.append(
            #         self.system_message(instructions))
            # if self.state.messages[0]["role"] != "system":
            #     conversation.insert(
            #         0, self.system_message(instructions))


            instructions += f"\n### **Current Working Directory (CWD)**: **`{self.state.get_cwd()}`**"
            instructions+= f"\n### **Current platform (OS)**: **`{platform()}`**"
            conversation.insert(0, self.system_message(instructions))
            # print(json.dumps(conversation, indent=2))

            stream = self.model.chat.completions.create(
                model=self.model_id,
                messages=conversation,
                tools=self.tool_declarations if tool_use else [],
                temperature=0.7,
                stream=True,
            )

            tool_calls = {}
            tool_call_announced = {}
            llm_response = ""
            spinner = Spinner()
            frames = itertools.cycle(spinner.spinners["braile-classic"])
            last_spinner_update = 0
            last_tool = ""
            for chunks in stream:
                if not chunks.choices or len(chunks.choices) == 0:
                    continue
                delta = chunks.choices[0].delta

                if hasattr(delta, 'content') and delta.content:
                    llm_response += delta.content
                    if print_output:
                        print(delta.content, end="", flush=True)
                # print()

                if hasattr(delta, 'tool_calls') and delta.tool_calls:

                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_call_announced:
                            tool_call_announced[idx] = {"status": False, "message": ""}

                        if idx not in tool_calls:
                            tool_calls[idx] = {
                                "id": tc.id,
                                "name": "",
                                "arguments": ""
                            }

                        if tc.function:
                            # print(json.dumps(tool_calls, indent=2))

                            if tc.function.name:
                                tool_calls[idx]["name"] += tc.function.name
                                # print(f"\nCalling tool: {tool_calls[idx]["name"]}")
                            name = tool_calls[idx]["name"]
                            if tc.function.arguments:
                                tool_calls[idx]["arguments"] += tc.function.arguments

                                if tool_call_announced[idx]["status"] and print_output:
                                    now = time.monotonic()
                                    if tool_calls[idx]["arguments"][-1] == "}":
                                        print(f"\r{Color.c("✔", fg = "green")}", end="", flush=True)
                                        # continue  
                                    elif now - last_spinner_update >= 0.1:
                                        print(f"\r{next(frames) if tool_calls[idx]["arguments"][-1] != "}" else Color.c("✔", fg = "green")}", end="", flush=True)
                                        # time.sleep(0.05)
                                        last_spinner_update = now
                                    continue

                                name_to_message = {
                                    "write": "Writing",
                                    "read": "Reading",
                                    "edit": "Editing",
                                    "make_directory": "Creating directory",
                                    "list_directory": "List directroy",
                                    "bash": "Running command:"
                                }
                                m = (re.search(r'"fname"\s*:\s*"([^"]+)"', tool_calls[idx]["arguments"])
                                     or re.search(r'"path"\s*:\s*"([^"]+)"', tool_calls[idx]["arguments"])
                                     or re.search(r'"cmd"\s*:\s*"([^"]+)"', tool_calls[idx]["arguments"])
                                    )
                                if m and print_output:
                                    tool_call_announced[idx]["message"] = f"{name_to_message[name]} {m.group(1)}"
                                    print(f"\n{" " if tool_calls[idx]["arguments"][-1] != "}" else Color.c("✔", fg = "green")}  "+Color.c(tool_call_announced[idx]["message"], fg = "#adadad"), end="", flush=True)
                                    tool_call_announced[idx]["status"] = True
                                    continue
                    
                                # print(tc.function.arguments, end="", flush=True)
            print()
            
            return {
                "response": llm_response,
                "tool_calls": tool_calls,
            }
        except KeyboardInterrupt:
            return {
                "response": "stopped by user",
                "tool_calls": []
            }

    def user_message(self, content):
        return {"role": "user", "content": content}

    def assistant_message(self, content):
        return {"role": "assistant", "content": content}
    
    def system_message(self, content):
        return {"role": "system", "content": content}

    def tool_message(self, tool_id, content):
        return {"role": "tool", "tool_call_id": tool_id, "content": content}

    def build_tool_declarations(self, tools: list[Tool]):
        tool_dclarations = []
        py_to_json = {str: "string", int: "integer",
                          float: "number", bool: "boolean", list: "array", dict: "object"}
        for tool in tools:
            sig = inspect.signature(tool.func)
            props = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param_name == "state":
                    continue
                ann = param.annotation
                # print(ann)
                json_type = py_to_json.get(get_origin(ann), "string")
                props[param_name] = {"type": json_type}
                props[param_name]["description"] = tool.param_descriptions.get(param_name, "")
                if json_type == "array":
                    args = get_args(ann)
                    if args:
                        item_type = py_to_json.get(args[0], "string")
                        props[param_name]["items"] = {"type": item_type}
                if param.default is inspect.Parameter.empty:
                    required.append(param_name)

            newtool = {
                "type": "function",
                "function":{
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": required,
                        "additionalProperties": False
                    }
                }
            
            }


            tool_dclarations.append(newtool)
        return tool_dclarations
