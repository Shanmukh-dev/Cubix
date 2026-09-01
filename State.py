from __future__ import annotations
from typing import TypedDict, List
import os
from pathlib import Path
import json
# from Session import Session
from uuid import uuid4
import yaml
import requests


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
        # self.load_project_skills()
        self.load_config()


# available_models = data["available_models"]

    def set_cwd(self, cwd: str) -> None:
        self.cwd = cwd
        if not os.path.exists(os.path.join(self.cwd, self.project_memory)):
            self.createMemory()
        else:
            self.load_memory()
            print("Memory Loaded Successfully")

        self.load_project_skills()

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
        print(f"Task history built:\n{tast_hist}\n\n\n\n")
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
                    },
                    "google-gemini": {
                        "apikey": "",
                        # "base_url": "https://generativelanguage.googleapis.com/v1beta/models"
                    }
                },
            }
            with open(Path.home() / ".cubix" / "config.json", "w") as f:
                json.dump(data, f, indent=2)
            # self.available_models = data["available_models"]
            self.available_providers = data["providers"]
        else:
            with open(Path.home() / ".cubix" / "config.json") as f:
                data = dict(json.load(f))
            # self.available_models = data["available_models"]
            self.available_providers = data["providers"]
        for provider in self.available_providers:
                
            prov = self.available_providers[provider]
            if provider == "google-gemini":
                if prov["apikey"]:
                    res = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params = {"key": prov["apikey"]})
                    data = res.json()
                    model_list = [f"{provider}/{model['name']}" for model in data.get("models", [])]
                    self.available_models.extend(model_list)
                    continue
            if prov["apikey"]:
                res = requests.get(prov["base_url"] + "/models", headers={"Authorization": f"Bearer {prov['apikey']}"})
                model_list = [f"{provider}/{model['id']}" for model in res.json().get("data", [])]
                self.available_models.extend(model_list)
        # print("Session loaded successfully")

    def load_skills(self):
        home = Path.home()
        if not os.path.isdir(home / ".agents") or not os.path.isdir(home / ".agents" / "skills"):
            return

        global_skill_dir = home / ".agents" / "skills"
        for path in os.listdir(global_skill_dir):
            skill = global_skill_dir / path / "SKILL.md"

            with open(skill) as f:
                data = f.read()

                frontmatter = data.split("---", 2)[1]

                skill_matter = yaml.safe_load(frontmatter)

                skill_matter["path"] = str(global_skill_dir / path)
                self.available_skills.append(skill_matter)
        # print(self.available_skills)

    def load_project_skills(self):

        local_skill_dir = os.path.join(self.cwd, ".cubix/skills")
        if not os.path.isdir(local_skill_dir):
            return
        for path in os.listdir(local_skill_dir):
            skill = local_skill_dir / path / "SKILL.md"

            with open(skill) as f:
                data = f.read()

                frontmatter = data.split("---", 2)[1]

                skill_matter = yaml.safe_load(frontmatter)

                skill_matter["path"] = str(local_skill_dir / path)
                self.available_skills.append(skill_matter)

    def cleanUP(self):
        if len(self.messages) > 0:
            self.update_moemory()
        else:
            if os.path.exists(os.path.join(self.cwd, self.project_memory)):
                os.remove(os.path.join(self.cwd, self.project_memory))
        



            




