<p align="center">
  <img src="./assets//images/Cubix poster.png" alt="Description" width="700">
</p>

# Cubix Coding Agent
Cubix is simple coding agent harness with a minimal TUI (Terminal User Interface) built fully with `Python` and `UV`.

## Goal of the project:
The goal behind cubix was to explore how modern coding agents work and to build a custom extendible agent harness.

---

# How to use 

## Installation:
Copy paste the following commands to install Cubix <br>

**Using Curl:** <br>
```
<Curl command>
```

**Using Powershell:** <br>
```
<Powershell command>
```

## Usage

- **Login** - Use the `/login` To set up api key any of your preffered providers from the list.

- **Select working directory** - Run `!cd <your_working_directory_path>` to select a project directory. This can be an empty directory or an existing project.

- **Prompts** - Once the working directory is selected you can start prompting the agent. All the chats stored in a directory called `.cubix` in the project root.

## Shell mode
Shell commands can be executed directly from the agent prompt interface by starting the prompt with a `!`. Eg.: `!npx create-react-app@latest myapp`

## Available commands:
- `/model` - Used to select a model from a list of available models.
- `/get-cwd` - Returns the current working directory path.
- `/new-session` - Starts a new chat session.
- `/load-session` - Used to load a previous chat session
- `/compact` - Used to summarize the current session messages and tool_calls performed. Automatically triggered after a certain threshold number of active messages.
- `/login` - Used to set up api key for a provider from the list of providers
- `/clear` - Clears the terminal.
- `/exit` - Terminates the application.

## Supported providers:
- `Nvidia NIM`
- `Groq`
- `OpenRouter`

The support of the other providers will be expanded as the development continues. 