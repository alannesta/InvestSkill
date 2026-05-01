# Antigravity Global Instructions

## Handling Claude Code-style Slash Commands (/commands)

The skills and prompts in this repository frequently reference Claude Code-style slash commands (e.g., `/fundamental-analysis AAPL`, `/report-generator --type comprehensive`). Antigravity does not have native support for executing these as literal commands. 

Whenever you encounter a `/command` invocation—either in a skill's workflow example or directly requested by the user—you must interpret it as a directive to manually execute the corresponding skill or analysis framework.

To execute a slash command:
1. **Extract the Name**: Identify the core name of the requested tool (e.g., `fundamental-analysis`).
2. **Locate the Source File**: Look up the corresponding instructions by checking:
   - The `.agents/skills/` directory for specialized skills (e.g., `.agents/skills/report-generator/SKILL.md`).
   - The `prompts/` directory for core analysis frameworks (e.g., `prompts/fundamental-analysis.md`).
3. **Read Instructions**: Use your `view_file` tool to read the markdown file associated with that skill or prompt if you do not already have its context.
4. **Execute**: Follow the instructions within that file to perform the task, making sure to apply any arguments or flags provided in the original `/command` (such as specific tickers or format types).
