import os
from pathlib import Path
from subprocess import PIPE, Popen, STDOUT, DEVNULL
import threading
import time

from State import AgentState



async def is_exists(path: str) -> bool:
    result = Path(path).exists()
    return result


async def write(state: AgentState, fname: str, content: str) -> str:
    if not content:
        state.current_action_history += f"- Write failed: content not provided for file {fname}\n"
        return "ERROR Tool - write: Content not provided"

    try:
        file_path = Path(state.get_cwd()) / fname
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        result = f"File {fname} written successfully"
        state.current_action_history += f"- Wrote to file {fname} successfully\n"
        return result
    except Exception as err:
        error_msg = f"ERROR Tool - write: {err}"
        state.current_action_history += f"- Write error for file {fname}: {err}\n"
        return error_msg


async def read(state: AgentState, fname: str, offset: int | None = None, length: int | None = None) -> str:
    try:
        file_path = Path(state.get_cwd()) / fname
        if not await is_exists(str(file_path)):
            msg = "File Does Not Exist."
            state.current_action_history += f"- Read failed: file {fname} does not exist\n"
            return msg

        if offset is not None:
            data = file_path.read_bytes()
            if offset < 0 or offset > len(data):
                msg = "ERROR Tool - read: Offset out of range"
                state.current_action_history += f"- Read failed: offset out of range for file {fname}\n"
                # print(msg)
                return msg

            end = len(data) if length is None else offset + length
            result = data[offset:end].decode("utf-8", errors="replace")
            output = f"FIle:{file_path}\n{result}"
            state.current_action_history += f"- Read file {fname} successfully\n"
            # print(output)
            return output

        result = file_path.read_text(encoding="utf-8")
        output = f"FIle:{file_path}\n{result}"
        state.current_action_history += f"- Read file {fname} successfully\n"
        return output
    except Exception as err:
        error_msg = f"ERROR Tool - read: {err}"
        state.current_action_history += f"- Read error for file {fname}: {err}\n"
        return error_msg


async def edit(state: AgentState, fname: str, target: str, patch: str) -> str:
    try:
        file_path = Path(state.get_cwd()) / fname
        if not await is_exists(str(file_path)):
            msg = f"File /{fname} does not exist."
            state.current_action_history += f"- Edit failed: file {fname} does not exist\n"
            return msg

        data = file_path.read_text(encoding="utf-8")
        data = data.replace(target, patch)
        file_path.write_text(data, encoding="utf-8")
        result = f"Edited {fname} successfully"
        state.current_action_history += f"- Edited file {fname} successfully\n"
        return result
    except Exception as err:
        error_msg = f"ERROR Tool - patch: {err}"
        state.current_action_history += f"- Edit error for file {fname}: {err}\n"
        return error_msg


def make_directory(state: AgentState, path: str) -> str:
    dir_path = os.path.join(state.get_cwd(), path)
    try:
        if not os.path.exists(str(dir_path)):
            os.mkdir(dir_path)
            result = f"Directory {path} created successfully."
            state.current_action_history += f"- Created directory {path} successfully\n"
            return result
        msg = f"Directory {path} already exists"
        state.current_action_history += f"- Make directory failed: {path} already exists\n"
        return msg
    except Exception as e:
        error = f"ERROR Tool - make_directory: {str(e)}"
        state.current_action_history += f"- Make directory error for {path}: {str(e)}\n"
        return error

def list_directory(state:AgentState, path: str):
    dir_path = os.path.join(state.get_cwd(), path)
    if os.path.exists(dir_path):
        result = "\n".join(os.listdir(dir_path))
        output = f"Directory: {path} \n{result}"
        state.current_action_history += f"- Listed directory {path} successfully\n"
        return output
    else:
        msg = f"Directory {path} does not exist"
        state.current_action_history += f"- List directory failed: {path} does not exist\n"
        return msg


def bash(state: AgentState, cmd: str) -> str:
    try:
        blacklist = ["pwd", "ls -R", "ls -a", "ls", "mkdir "]
        for c in blacklist:
            if c in cmd:
                msg = f"bash output: {cmd} Denied by user from executing"
                state.current_action_history += f"- Bash denied by policy: {cmd}\n"
                return msg

        query = input(f"Bash: {cmd}\nDo you want to execute the following command ? (y/n): ").strip()
        if query.lower() != "y":
            msg = f"bash output: {cmd} Denied by user from executing"
            state.current_action_history += f"- Bash denied by user: {cmd}\n"
            return msg

        silence_timeout = 10.0
        hard_timeout = 600.0
        proc = Popen(
                cmd,
                cwd= state.get_cwd(),
                shell=True,
                stdout=PIPE,
                stderr=STDOUT,    
                stdin= DEVNULL,
                text=True,
                bufsize=1   
            )
        
        output_lines = []
    
        last_output_time = time.monotonic()
        hang_detected = False
        lock = threading.Lock()
    
    
        def reader():
            nonlocal output_lines
            for line in proc.stdout:
                print(line, end = "")
                with lock:
                    output_lines.append(line)
                    last_output_time = time.monotonic()
    
            proc.stdout.close()
    

        def watchdog():
            nonlocal hang_detected
    
            start = time.monotonic()
            while proc.poll is None:
                elapsed = time.monotonic() - start
                with lock:
                    silent_for = time.monotonic() - last_output_time
    
                if silent_for >= silence_timeout:
                    hang_detected = True
                    proc.kill()
                    return
    
                if elapsed >= hard_timeout:
                    hang_detected = True
                    proc.kill()
                    return
    
                time.sleep(0.5)
    
    
        t_reader = threading.Thread(target = reader, daemon=True)
        t_watchdog = threading.Thread(target = watchdog, daemon=True)
    
        t_reader.start()
        t_watchdog.start()
        t_reader.join()
        t_watchdog.join()
        proc.wait()
        print("\n")

        if not hang_detected:
            result = f"Bash - Ran command: {cmd}\noutput:\n " + "".join(output_lines)
            state.current_action_history += f"- Ran bash command: {cmd} successfully\n"
            return result
        else:
            msg = f"ERROR Tool - bash: Tool failed waiting for user or due to timeout. Try passing the necessary (Eg.: -y or --yes) falgs to make the tool non interactive."
            state.current_action_history += f"- Bash error for command {cmd}: timeout or hang detected\n"
            return msg
        # if proc.returncode == 0:
    except Exception as err:
        error_msg = f"ERROR Tool - bash: {err}"
        state.current_action_history += f"- Bash error for command {cmd}: {err}\n"

def read_skill(state: AgentState, skill_name: str) -> str:
    skill = next((s for s in state.available_skills if s["name"] == skill_name), None)
    if not skill:
        msg = f"Skill {skill_name} not found."
        state.current_action_history += f"- Read skill failed: {skill_name} not found\n"
        return msg

    try:
        with open(os.path.join(skill["path"], "SKILL.md"), "r", encoding="utf-8") as f:
            content = f.read()
            result = f"Skill: {skill_name}\nSkill Locaation: {skill["path"]}\n{content}"
            state.current_action_history += f"- Read skill {skill_name} successfully\n"
            return result
    except Exception as err:
        error_msg = f"ERROR Tool - read_skill: {err}"
        state.current_action_history += f"- Read skill error for {skill_name}: {err}\n"
        return error_msg
