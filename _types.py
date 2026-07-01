import inspect
from abc import ABC, abstractmethod

class LLMProvider(ABC):

    @abstractmethod
    def user_message(self, content: str) -> dict:
        """Returns a user message dictionary"""
        pass

    @abstractmethod
    def assistant_message(self, content: str) -> dict:
        """Returns a user message dictionary"""
        pass
    @abstractmethod
    def system_message(self, content: str) -> dict:
        """Returns a system message dictionary"""
        pass

    @abstractmethod
    def tool_message(self, tool_id, content: str) -> dict:
        """Returns a tool message dictionary"""
        pass

    @abstractmethod
    def build_tool_declarations(self, tools_list) -> list[dict]:
        """Returns a list of tool declarations in the provider specific format"""
        pass


class Tool:
    def __init__(self, name: str, description: str, func: callable, param_descriptions: dict[str, str] | None = None):
        self.name = name
        self.description = description
        self.func = func
        self.param_descriptions = param_descriptions or {}

    async def execute(self, params):
        try:
            if inspect.iscoroutinefunction(self.func):
                return await self.func(**params)
            else:
                return self.func(**params)
        except Exception as e:
            return f"ERROR executing tool '{self.name}': {str(e)}"
            