from __future__ import annotations
from typing import TypedDict, List
import os
from pathlib import Path
import json
# from Session import Session
from uuid import uuid4
import yaml



class StateMessage(TypedDict):
    type: str
    msg: str


class AgentState:
    def __init__(self) -> None:
        self.cwd: str = ""
        self.messages: List = []
        self.session_messaegs = []
        self.running: bool = False
        self.session_id = str(uuid4())
        self.project_memory = f".cubix/{self.session_id}.json"

        self.completed_tasks: List[str] = []
        self.plan: str = {"goal": "", "steps": []}
        self.current_execution_mode = "idle"
        self.current_tool_calls = {}
        self.current_action_history = "Current goal: {prompt}\nCurrent action history:\n"
        self.available_providers = {}
        self.available_models = []
        self.available_skills = []
        self.load_skills()
        self.load_config()


# available_models = data["available_models"]

    def set_cwd(self, cwd: str) -> None:
        self.cwd = cwd
        if not os.path.exists(os.path.join(self.cwd, self.project_memory)):
            self.createMemory()
        else:
            self.load_memory()
            print("Memory Loaded Successfully")

    def get_cwd(self) -> str:
        return self.cwd

    def createMemory(self):
        if not os.path.isdir(os.path.join(self.cwd, ".cubix")):
            os.mkdir(os.path.join(self.cwd, ".cubix"))
        with open(os.path.join(self.cwd, self.project_memory), "w") as f:
            json.dump({
                "conversation_history": []
            }, f, indent=2)
        print("Created memory file.")

    def load_memory(self):
        if not self.cwd:
            print("Current working directory (cwd) is not set. Please set the cwd before loading memory.")
            return
        memory_path = os.path.join(self.cwd, self.project_memory)
        if os.path.exists(memory_path):
            with open(memory_path) as f:
                data = json.load(f)
                self.messages = data["conversation_history"]
            # print("Memory laoded succsessfully")
        else:
            self.createMemory()

    def update_moemory(self):
        memory_path = os.path.join(self.cwd, self.project_memory)
        if not os.path.exists(memory_path):
            self.createMemory()
        with open(memory_path, "w") as f:
            json.dump({
                "conversation_history": self.messages
            }, f, indent=2)

    def reset_action_history(self):
        self.current_action_history = "Current goal: {prompt}\nCurrent action history:\n"

    
    def build_task_history(self):
        tast_hist = "\n".join(f"- {task}" for task in self.completed_tasks) + "\n\n" + self.current_action_history
        # print(f"Task history built:\n{tast_hist}\n\n\n\n")
        return tast_hist

    def load_session(self, session_id):
        if os.path.exists(os.path.join(self.get_cwd(), self.project_memory)) and not self.messages:
            os.remove(os.path.join(self.get_cwd(), self.project_memory))
        self.session_id = session_id
        self.project_memory = f".cubix/{self.session_id}.json"
        self.load_memory()
    def new_session(self):
        if not self.messages:
            return
        self.session_id = str(uuid4())
        self.project_memory = f".cubix/{self.session_id}.json"
        self.load_memory()
        self.messages = []

    def load_config(self):
        if not os.path.exists(Path.home() / ".cubix" / "config.json"):
            data = {
                "providers": {
                    "nvidia-nim": {
                        "apikey": "",
                        "base_url": "https://integrate.api.nvidia.com/v1"
                    },
                    "openrouter": {
                        "apikey": "",
                        "base_url": "https://openrouter.ai/api/v1"
                    },
                    "groq": {
                        "apikey": "",
                        "base_url": "https://api.groq.com/openai/v1"
                    }
                },
                "available_models": [
                    "nvidia-nim/z-ai/glm-5.1",
                    "nvidia-nim/deepseek-ai/deepseek-v4-flash",
                    "nvidia-nim/deepseek-ai/deepseek-v4-pro",
                    "nvidia-nim/openai/gpt-oss-120b",
                    "nvidia-nim/nvidia/nemotron-3-ultra-550b-a55b",
                    "groq/llama-3.1-8b-instant",
                    "groq/llama-3.3-70b-versatile",
                    "groq/openai/gpt-oss-120b",
                    "groq/openai/gpt-oss-20b",
                    "groq/whisper-large-v3",
                    "groq/whisper-large-v3-turbo",
                    "groq/compound",
                    "groq/compound-mini",
                    "groq/canopylabs/orpheus-arabic-saudi",
                    "groq/canopylabs/orpheus-v1-english",
                    "groq/meta-llama/llama-4-scout-17b-16e-instruct",
                    "groq/meta-llama/llama-prompt-guard-2-22m",
                    "groq/meta-llama/llama-prompt-guard-2-86m",
                    "groq/openai/gpt-oss-safeguard-20b",
                    "groq/qwen/qwen3-32b",
                    "groq/qwen/qwen3.6-27b"
                ]
            }
            with open(Path.home() / ".cubix" / "config.json", "w") as f:
                json.dump(data, f, indent=2)
            self.available_models = data["available_models"]
            self.available_providers = data["providers"]
        else:
            with open(Path.home() / ".cubix" / "config.json") as f:
                data = dict(json.load(f))
            self.available_models = data["available_models"]
            self.available_providers = data["providers"]
        # print("Session loaded successfully")

    def load_skills(self):
        home = Path.home()
        if not os.path.isdir(home / ".agents") or not os.path.isdir(home / ".agents" / "skills"):
            return

        skill_dir= home / ".agents" / "skills"

        for path in os.listdir(skill_dir):
            skill = skill_dir / path / "SKILL.md"

            with open(skill) as f:
                data = f.read()

                frontmatter = data.split("---", 2)[1]

                skill_matter = yaml.safe_load(frontmatter)

                skill_matter["path"] = str(skill_dir / path)
                self.available_skills.append(skill_matter)

    def cleanUP(self):
        if len(self.messages) > 0:
            self.update_moemory()
        else:
            if os.path.exists(os.path.join(self.cwd, self.project_memory)):
                os.remove(os.path.join(self.cwd, self.project_memory))
        



            




