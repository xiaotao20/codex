# PowerShell Recipes

Use these recipes when working on Windows in a PowerShell session.

## Open a local dev server in a visible browser

```powershell
agent-browser --headed open http://localhost:3000
agent-browser wait --load networkidle
agent-browser snapshot -i
```

## Open the static demo page in this repository

```powershell
$repo = (Get-Location).Path.Replace('\', '/')
$url = "file:///$repo/code/index.html"

agent-browser open $url
agent-browser snapshot -i
```

## Fill the local login form by selector

This avoids depending on translated labels or snapshot ref numbers.

```powershell
$repo = (Get-Location).Path.Replace('\', '/')
$url = "file:///$repo/code/index.html"

agent-browser open $url
agent-browser fill '#email' 'demo@example.com'
agent-browser fill '#password' 'Password123!'
agent-browser click 'button[type="submit"]'
agent-browser wait 1200
agent-browser get text '#form-status'
```

## Save a screenshot and a PDF

```powershell
New-Item -ItemType Directory -Force .\tmp\agent-browser | Out-Null

agent-browser screenshot .\tmp\agent-browser\page.png
agent-browser pdf .\tmp\agent-browser\page.pdf
```

## Reuse a Chrome profile that is already logged in

```powershell
agent-browser --profile Default open https://example.com
agent-browser snapshot -i
```

Use a named session when you want the CLI to auto-save and restore cookies plus local storage:

```powershell
agent-browser --session-name my-app open https://example.com
agent-browser snapshot -i
```

## Connect to a manually started Chrome instance

Start Chrome yourself with remote debugging, then connect:

```powershell
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' --remote-debugging-port=9222
agent-browser --auto-connect snapshot -i
```

## Recover from stale sessions or failed launches

```powershell
agent-browser doctor
agent-browser close --all
```
