Output assets/signup-demo.gif

Set Width 1800
Set Height 400
Set FontSize 20
Set Theme "Dracula"

Hide
Type "export PATH=/usr/local/fake-bin:$PATH"
Enter
Show

Sleep 500ms
Type "curl -s -X POST https://app.toolbelt.ai/api/onboard | jq .mcpUrl"
Enter
Sleep 3s
