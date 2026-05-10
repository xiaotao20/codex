---
name: agent-browser
description: Drive a real browser through the locally installed `agent-browser` CLI for navigation, clicking, typing, form filling, screenshots, PDF capture, page text extraction, login/session reuse, and browser-based validation. Use this skill when Codex needs to interact with a website or local dev server in Chrome instead of only reading source files, especially for frontend debugging, QA, reproducing UI bugs, validating rendered output, or collecting browser evidence on Windows/PowerShell.
---

# Agent Browser

Use the local `agent-browser` binary instead of guessing browser state from source code or raw HTML.

## Quick checks

1. Confirm the CLI is available:

```powershell
agent-browser --version
```

2. If launch or connection fails, diagnose before guessing:

```powershell
agent-browser doctor
```

3. If you need the full upstream docs that ship with the installed CLI, load them on demand:

```powershell
agent-browser skills get core --full
```

## Core loop

Prefer the snapshot-and-ref workflow over CSS selectors.

```powershell
agent-browser open <url>
agent-browser snapshot -i
agent-browser click @e3
agent-browser snapshot -i
```

Rules:

- `@eN` refs are valid only for the snapshot that created them.
- Re-run `snapshot -i` after any page change: navigation, modal open or close, form submit, SPA rerender, tab switch, or lazy-loaded content.
- Prefer `wait --load networkidle`, `wait --url`, or `wait --text` over blind sleeps.
- Close the browser when the task is finished:

```powershell
agent-browser close
# or
agent-browser close --all
```

## Interaction order

1. Preferred: `snapshot -i` plus `@eN` refs.
2. Good fallback: `find role`, `find label`, `find text`, `find placeholder`.
3. Last resort: raw CSS selectors.
4. Use `eval` only when extraction or DOM inspection cannot be handled by the built-in commands.

Examples:

```powershell
agent-browser snapshot -i
agent-browser fill @e4 'user@example.com'
agent-browser press Enter

agent-browser find label 'Email' fill 'user@example.com'
agent-browser find role button click --name 'Submit'

agent-browser get text @e7
agent-browser screenshot .\tmp\agent-browser\step-1.png
```

## Common workflows

### Inspect a local dev server

```powershell
agent-browser --headed open http://localhost:3000
agent-browser snapshot -i
```

If the app is React and you need component or render data:

```powershell
agent-browser open --enable react-devtools http://localhost:3000
agent-browser react tree
```

### Reuse login state

Use a real Chrome profile or session persistence instead of pasting credentials into commands.

```powershell
agent-browser --profile Default open https://example.com
agent-browser --session-name my-app open https://app.example.com
```

### Capture evidence

```powershell
agent-browser screenshot .\tmp\agent-browser\page.png
agent-browser screenshot --annotate .\tmp\agent-browser\page-map.png
agent-browser pdf .\tmp\agent-browser\page.pdf
agent-browser console
agent-browser errors
```

### Use multiple tabs or sessions

```powershell
agent-browser tab new https://example.com
agent-browser tab

agent-browser --session admin open https://app.example.com
agent-browser --session user open https://app.example.com
```

## PowerShell notes

- Use single quotes for text with spaces unless you need PowerShell interpolation.
- For JSON arguments, wrap the JSON in single quotes so the inner double quotes stay intact.
- Keep screenshots, downloads, HAR files, and saved auth state outside tracked docs unless the user explicitly wants them committed.
- `agent-browser` supports a project-level `agent-browser.json` file if per-project defaults are needed later.

## Load more detail only when needed

- Windows recipes and local-file examples: [references/powershell-recipes.md](references/powershell-recipes.md)
- Safety, auth-state handling, and trust boundaries: [references/safety-and-state.md](references/safety-and-state.md)
- Version-matched upstream docs from the installed CLI:

```powershell
agent-browser skills get core --full
agent-browser skills get electron
agent-browser skills get dogfood
agent-browser skills get slack
```
