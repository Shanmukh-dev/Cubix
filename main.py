import asyncio
import json

from LLM import Model
from agent_tools import ToolRegistry
from _types import Tool
from State import AgentState
from agent_tools.tools import *
from pathlib import Path
from frontend.tui import *
import threading
import openai
import time


# loading configuration






instructions = """
# Role
 You are an intelligent coding and experienced full-stack developer and a UI/ UX designer agent for creating programs as per the user's query. You MUST use tools to create and read and edit specific files instead of asking for the entire codebase. Generate the entire contents of a file at once.

IMPORTANT: The code generated should always be multi-line fashion.

## Task
Your job is to implement changes directly.
- Read and understand the relevant code before making changes
- Use writeFile to create new files, editFile for targeted modifications
- Use bash to run commands (tests, builds, git operations)
- After making changes, verify the work when possible

## Front Design Rules
- Design and develop all the screens of the user flow for high-paid products with a modern, elegant-looking UI. Have a design-first approach. Always start with a header and footer. The rest of the UI should be functional and professional. If a functionality requires an npm package, use it through a CDN if possible.
- Choose a cohesive color palette and place components to improve UX. Refer to modern UI inspiration from Dribbble and Behance. Keep the design consistent, use gradients, and add micro-animations where appropriate. Add alerts to inform the user in case of errors. Use Google Material icons and Iconify icons where necessary.
- IMPORTANT: ALWAYS USE GOOD DYNAMIC LOOKING LAYOUTS following design principles. DO NOT USE center-card layouts unless there is a strong reason.

## Working Strategy
- When a query is received from the user, first start by analyzing the query to identify the tools terminal commands required and plan their use.
- Once the tools have been decided, decide those that can be called parallely and those that can be called one at a time. Eg.: write file1 and write file2 can be called parallelly.
- Always plan your actions before responding.
- Follow the plan strictly and always try to return multiple functionCalls at once.

## Tool usage
- read:- Description: Reads the specified file path.; Required params: {path: <path of the file>}
- write:- Description: Writes content to the specified file path. Creates the file if it does not exist.; Required params: {path: <path of the file>, content: <the content to be written in the file>}
- edit:- Description: Replaces a target section of a file with new content.; Required params: {path: <path of the file>, target: <the section of the file to be replaced>, patch: <the new content to replace the target>}
- make_directory:- Description: Creates a new directory at the given path if it does not already exist.; Required params: {path: <the path of the directory>}
- list_directory:- Description: Lists all the files and directories at a given path (path of a directory), if the path exists..; Required params: {path: <the path of the directory>}
- bash:- Description: Executes a shell command in the current working directory.; Required params: {cmd: <the command to run>}
- read_skill:- Description: Reads the skills from the skills directory and returns a list of skills.; Required params: {skill_name: <name of the skill>}

## Skill usage
- Skills are pre-defined instruction that help you perform specific tasks.
- You may be provided with a list skills with their names and descriptions of their purpose.
- Use the read_skills tool to read the skills and use them in your response if they are relevant to the user's query.
- Running any commnds listed in a skill requires you to include the `cd <path of the skill> && <command>` in the bash tool.

## Rules
- While usingt the bash tool, execute commands that are completely non-interactive, i.e. the command must execute without waiting any other user input, all the required inputs must be provided in the command itself. Always pass -y, --yes flags wherever necessary. Commands that require user input will hang and fail.
- Always work in the current working directory. the current dierctory is programatically set at the beginning set. do not re-enter it every time.
- DO NOT explore or try to edit .cubix/memory.json. It is the file that provides memory to you and is programatically maintined and updated.
"""

state = AgentState()
# state.set_cwd(r"C:\TSSV\ProgrammingAndCoding\CodingAgents\Cubix\src\test\code")
model = state.available_models[3]


tool_list = [
    Tool(func=read, name="read", description="Reads the specified file path.",
         param_descriptions={"fname": "path of the file"}),
    Tool(func=write, name="write", description="Writes content to the specified file path. Creates the file if it does not exist.",
         param_descriptions={"fname": "path of the file", "content": "the content to be written in the file"}),
    Tool(func=edit, name="edit", description="Replaces a target section of a file with new content.", param_descriptions={
         "fname": "path of the file", "target": "the section of the file to be replaced", "patch": "the new content to replace the target"}),
    Tool(func=make_directory, name="make_directory", description="Creates a new directory at the given path if it does not already exist.",
         param_descriptions={"path": "the path of the directory"}),
    Tool(func=list_directory, name="list_directory", description="Lists all the files and directories at a given path (path of a directory), if the path exists.",
         param_descriptions={"path": "the path of the directory"}),
    Tool(func=bash, name="bash", description="Executes a shell command in the current working directory.",
         param_descriptions={"cmd": "the command to run"}),
    Tool(func=read_skill, name="read_skill", description="Reads the skills from the skills directory and returns a list of skills.",
         param_descriptions={"skill_name": "name of the skill"}),
]


toolRegistry = ToolRegistry(tool_list, state)

ai = Model(model_id=model, state=state,
           instructions=instructions, tool_list=tool_list)

SLASH_COMMANDS = [
    "/model",
    "/get-cwd",
    "/new-session",
    "/load-session",
    "/compact",
    "/login",
    "/clear",
    "/exit",
]

tui = TUI("#252525", "#DFDFDF", "#b625ff", state=state,
          slash_commands=SLASH_COMMANDS, ai=ai)


def is_path_exists(path: str) -> bool:
    return Path(path).exists()


def print_agent_message(msg: str = ""):
    print(f"\n{Color.c("• Cubix:", fg=tui.accent_color)}\n{msg}\n")


def compact():
    old_messages = state.messages[:-19]
    if old_messages:
        summary = asyncio.run(ai.compact_messages(old_messages))
        if summary["resmonse"]:
            state.messages = [ai.model.system_message(
                "# Summary\n"+summary)] + state.messages[-20:]
            state.update_moemory()
    print(f"\r{Color.c("✔", fg="green")} Compacting Complete", flush=True)


def parse_commands(query: str):
    if query.startswith("!"):
        if query.startswith("!cd"):
            parts = query.split(" ", 1)
            cwd = parts[1].strip() if len(parts) > 1 else ""
            if not cwd:
                print_agent_message("Usage: !cd <path> to select a working directory first.")
            elif is_path_exists(cwd):
                state.set_cwd(cwd)
                print_agent_message(f"Cwd set to: {cwd}")
            else:
                print_agent_message("The provided path does not exist.")
        else:
            cmd = query[1:]
            output = bash(state, cmd)
            print_agent_message(output)

    if prompt.startswith("/"):
        # nonlocal model
        global model
        p = prompt[1:]
        if p == "model":
            mod = tui.select_model(
                f"{ai.provider}/{ai.model_id}", state.available_models)
            if mod:
                ai.set_model(mod)
        elif p == "exit":
            return
        elif p == "get-cwd":
            print_agent_message(Color.c(state.get_cwd(), fg="cyan"))
        elif p == "clear":
            tui.init_ui()
        elif p == "compact":
            if len(state.messages) >= 50:
                compact()
            print_agent_message(Color.c("✔ No compaction needed", fg="green"))
        elif p == "login":
            with open("config.json") as f:
                data = dict(json.load(f))
            provider_list = (data["providers"]).keys()
            selected_provider = tui.select_provider(provider_list)
            if selected_provider:
                print_agent_message(f"Provider: {selected_provider}")
                api_key = input("Enter API key: ").strip()
                if api_key:
                    data["providers"][selected_provider]["apikey"] = api_key
                    state.available_providers = data["providers"]
                    with open("config.json", "w") as f:
                        json.dump(data, f, indent=2)
                    # state.load_config()
                    ai.set_model(model)
                    print_agent_message(Color.c("Login successful", fg="green"))
        elif p == "add-model":
            with open("config.json") as f:
                data = dict(json.load(f))
            provider_list = (data["providers"]).keys()
            selected_provider = tui.select_provider(provider_list)
            if selected_provider:
                print_agent_message(f"Provider: {selected_provider}")
                id = input("Enter model-id: ").strip()
                if id:
                    data["available_models"].append(
                        f"{selected_provider}/{id}")
                    with open("config.json", "w") as f:
                        json.dump(data, f, indent=2)
                    state.available_models = data["available_models"]
                    print(
                        Color.c(f"Model {selected_provider}/{id} added successfully.", fg="greeen"))
        elif p == "load-session":
            if not state.get_cwd():
                print_agent_message(Color.c("\nPlease select a directory first.\n", fg="yellow"))
            memory_path = os.path.join(state.get_cwd(), ".cubix")
            session_list = []
            if not os.path.isdir(memory_path):
                print_agent_message(Color.c("\nNo sessioins yet in this project\n", fg="#98c7ff"))
                return
            for session in os.listdir(memory_path):
                with open(os.path.join(memory_path, session)) as f:
                    session_data = json.load(f)
                if not session_data["conversation_history"]:
                    continue
                try:
                    if session_data["conversation_history"]:
                        title = next(
                            filter(lambda msg: msg["role"] == "user", session_data["conversation_history"]))
                    else:
                        title = {"content": "Empty session"}
                except StopIteration:
                    # continue
                    title = {"content": "Empty session"}
                title = title["content"][:max(30, len(title["content"]))]
                session_list.append((session.split(".")[0], title))
            if not session_list:
                return
            selected_session = tui.select_session(session_list)
            if not selected_session:
                return
            state.load_session(session_id=selected_session)
            tui.init_ui()
            for msg in state.messages:
                if msg["role"] == "user":
                    print(">", msg["content"])
                elif msg["role"] == "assistant":
                    print_agent_message(msg["content"])
        elif p == "new-session":
            if not state.get_cwd():
                print_agent_message(Color.c("\nPlease select a directory first.\n", fg="yellow"))
            tui.init_ui()
            state.new_session()


def tool_mode():
    while state.current_tool_calls and state.current_execution_mode == "tool":
        # spinner.show()
        tool_results = asyncio.run(
            toolRegistry.async_tool_executor(state.current_tool_calls))
        for res in tool_results:
            state.messages.append(
                ai.model.tool_message(res["tool_call_id"], res["content"])
            )
            state.update_moemory()

        try:
            tui.hide_cursor()
            result = asyncio.run(ai.run_model())
            tui.show_cursor()
        except KeyboardInterrupt:
            print(Color.c("\nAgent Stopped\n", fg="#FF0000"))
            state.current_execution_mode = "idle"
            state.reset_action_history()
            state.current_tool_calls = {}
            tui.show_cursor()
            break
        if not result:
            break
        llm_response = result["response"]
        tool_calls = result["tool_calls"]
        # tool_call_message = [{"id": tc["id"], "name": tc["name"], "arguments": json.loads(tc["arguments"])} for tc in tool_calls.values()]
        state.messages.append(ai.model.assistant_message(llm_response,tool_calls))
        state.update_moemory()
        # if llm_response:
        # spinner.hide()
    if len(state.messages) >= 50:
        time.sleep(5)
        compact()
    # compact()

# def compact_messages():
#     old_messages = state.messages[:-19]
#     a


if __name__ == "__main__":
    # print(json.dumps(state.available_skills, indent=2))
    while True:

        prompt = tui.multiline_input("> ").strip()

        if prompt == "/exit":
            Color.clear_screen()
            break

        if not prompt:
            continue

        if prompt.startswith("!") or prompt.startswith("/"):
            parse_commands(prompt)
            continue

        if not state.get_cwd():
            print_agent_message(
                Color.c("Please select a working directory using '!cd <directory-path>' to start coding.", fg="yellow")
            )
            continue
        if not ai.model:
            print_agent_message(
                Color.c("Please select a model using '/model' or login using '/login' to start coding.", fg="yellow")
            )
            continue

        state.messages.append(ai.model.user_message(prompt))
        state.update_moemory()
        state.current_action_history = state.current_action_history.format(
            prompt=prompt)

        try:
            print_agent_message()
            tui.hide_cursor()
            result = asyncio.run(ai.run_model())
            tui.show_cursor()
        except openai.AuthenticationError:
            print_agent_message(Color.c("\nAuthentication failed.", fg="red"), "\nUse /login to set api key")
            # print()
            break
        except openai.RateLimitError:
            print_agent_message(Color.c("\nRate limit exceeded. Please try again later.", fg="red"))
            break
        except openai.APITimeoutError:
            print_agent_message(Color.c("\nAPI request timed out. Please try again.", fg="red"))
            break
        except openai.APIError:
            print_agent_message(Color.c("\nAPI error occurred. Please try again.", fg="red"))
            break
        except openai.APIConnectionError:
            print_agent_message(Color.c("\nNetwork error occurred. Please check your connection and try again.", fg="red"))
            break
        except openai.InvalidRequestError:
            print_agent_message(Color.c("\nInvalid request. Please check your input and try again.", fg="red"))
            break
        except openai.APIStatusError as e:
            print_agent_message(Color.c(f"\nAPI status error: {str(e)}. Please try again later.", fg="red"))
            break

        except KeyboardInterrupt:
            print(Color.c("\nAgent Stopped\n", fg="#FF0000"))
            state.current_execution_mode = "idle"
            state.reset_action_history()
            state.current_tool_calls = {}
            tui.show_cursor()
            break
        except Exception as e:
            print_agent_message(Color.c(f"\nAn unexpected error occurred: {str(e)}", fg="red"))
            break


        if not result:
            continue
        llm_response = result["response"]
        tool_calls = result["tool_calls"]
        # tool_call_message = [{"id": tc["id"], "name": tc["name"], "arguments": json.loads(tc["arguments"])} for tc in tool_calls.values()]
        state.messages.append(ai.model.assistant_message(llm_response,tool_calls))
        state.update_moemory()
        # if llm_response:

        if state.current_execution_mode == "tool":
            tool_mode()
            if not state.current_tool_calls:
                state.current_execution_mode = "idle"
                state.current_tool_calls = {}
        else:
            state.current_execution_mode = "idle"

            state.completed_tasks.append(prompt)
            state.reset_action_history()
    # #spinner_thread.join()
        if len(state.messages) >= 50:
            print(f"\rCompacting...", end="", flush=True)
            time.sleep(10)

            compact()
    Color.reset_screen_color()


# Create a web-based visual LLM function declaration and an output scheme creation tool for generating structured output for various LLM providers like Google Gemini, OpenRouter, Groq, Vercel AI SDK, Hugging Face, Nvidia NIM, etc. Using plain HTML, CSS and JS

# Create a well-designed elegant and luxurious landing page for a premium and expensive watch brand called "Time Keepers".

# Build a single-page Notes app inspired by Notion using only HTML, CSS, and JavaScript, featuring a clean minimalist UI with a collapsible sidebar, note list, rich-text editor (bold, italic, headings, lists), auto-save to localStorage, smooth animations, light/dark mode, keyboard shortcuts, responsive layout, rounded corners, subtle shadows, and a modern professional design.


# Build a world-class futuristic "Developer Operating System" portfolio for Vipin Vijay using only HTML5, CSS3, and Vanilla JavaScript (no Next.js, React, TypeScript, Tailwind, or frameworks), while preserving all premium features: OS-style boot sequence ("BOOTING VIPIN OS... Loading Skills... Loading Projects... Loading Experience... Loading Achievements... SYSTEM READY"), smooth scrolling, dynamic cursor glow, custom cursor, page transitions, aurora backgrounds, animated gradient mesh, floating particles, spotlight following mouse, glassmorphism, magnetic buttons, 3D tilt cards, scroll reveal animations, text reveal effects, full-screen hero with 3D particle universe, interactive mouse movement, floating technology icons, VIPIN VIJAY title, Information Technology Student subtitle, rotating roles (Java Developer, Python Developer, Problem Solver, Web Developer, Future Software Engineer), Explore Portfolio / Download Resume / Contact Me buttons, futuristic About dashboard (Name, Chennai India, Available for Opportunities, Java/Python/Web Development summary), animated live counters (Projects Built, Internships, Hackathons, Technologies Learned), 3D Interactive Skill Galaxy with Java, Python, C, HTML, CSS, JavaScript, VS Code, Git, GitHub, Figma, Tableau, OOP, DSA, Problem Solving using floating/glowing/rotating effects reacting to mouse movement, animated Green Intern timeline (Feb 2026–Mar 2026, May 2026–Present), premium project showcase with glassmorphism cards, glow borders, hover expansion, tilt effects, animated previews for E-Commerce Simulator and Street Food Connect including Problem, Approach, Solution, Impact, SIH Internal Hackathon spotlight section highlighting Team Leader and Top 50 achievement with trophy animations, Education section (B.Tech IT 2024–2028, CGPA 7.83) with animated progress indicators, sliding certification cards (Learning Programming with Java, Sep–Oct 2025), automatic GitHub integration from github.com/vipinvijay123 fetching profile, repositories, contribution data, commit activity, and language statistics via GitHub APIs, LinkedIn integration from linkedin.com/in/vipin-vijay-15630033b with recruiter CTA and professional summary, Recruiter Mode toggle that disables heavy animations and displays a concise resume view, futuristic contact terminal with Name, Email, Subject, Message fields and "MESSAGE TRANSMITTED SUCCESSFULLY" response, mobile-first responsive design, accessibility compliance, SEO optimization, Lighthouse score above 95, production-ready architecture with reusable modular components/files, advanced CSS animations and Canvas/WebGL effects where needed, visually comparable to premium experiences from Vercel, Linear, Stripe, Framer, and modern SaaS landing pages.
