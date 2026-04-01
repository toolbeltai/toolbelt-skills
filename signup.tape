Output assets/signup-demo.gif

Set Width 1440
Set Height 320
Set FontSize 16
Set Theme "Dracula"

Hide
Type "curl() { sleep 1 && echo '{\"mcpUrl\": \"https://mcp.toolbelt.ai/t/tb_1234567890/8bf91bad-02df-4137-97ac-69a006bac193/mcp\"}'; }"
Enter
Show

Sleep 500ms
Type "curl -s -X POST https://app.toolbelt.ai/api/onboard | jq .mcpUrl"
Enter
Sleep 3s
