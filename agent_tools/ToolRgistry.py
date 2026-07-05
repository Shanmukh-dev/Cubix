import asyncio
import json

from _types import Tool
from State import AgentState

class ToolRegistry:
    def __init__(self, tool_list: list[Tool], state: AgentState):
        self.tool_list = {
            tool.name: tool
            for tool in tool_list
        }
        self.state = state


    async def tool_responses(self, tool_name: str | None, args: str, tool_id):
            if tool_name is None or tool_name not in self.tool_list:
                return {"id": tool_id, "result": f"Unknown tool - {tool_name}"}

            tool = self.tool_list.get(tool_name)
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                return {"id": tool_id, "result": "Invalid json format for arguments"}
            args["state"] = self.state

            res = await tool.execute(args)
            return {"id": tool_id, "result": res}

    async def async_tool_executor(self, tool_calls):
        tool_results = await asyncio.gather(
            *[
                self.tool_responses(tc["name"], tc["arguments"], tc["id"]) for tc in tool_calls.values()
            ]
        )

        return [
            {
                "role": "tool",
                "tool_call_id": res["id"],
                "content": res["result"]
            } for res in tool_results
        ]
