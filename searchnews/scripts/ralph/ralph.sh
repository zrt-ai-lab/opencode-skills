#!/bin/bash
# Ralph Loop 启动脚本 - 仅初始化，不循环

DATE=${1:-$(date +%Y-%m-%d)}
PRD_FILE=".opencode/skills/searchnews/scripts/ralph/prd.json"
PRD_TEMPLATE=".opencode/skills/searchnews/scripts/ralph/prd.template.json"

# 从模板创建/重置 prd.json
if [ -f "$PRD_TEMPLATE" ]; then
    jq --arg date "$DATE" '.date = $date | .sources[].status = "pending" | .is_complete = false' "$PRD_TEMPLATE" > "$PRD_FILE"
    echo "Initialized prd.json for $DATE"
else
    echo "Error: Template not found!"
    exit 1
fi

echo ""
echo "Sources to crawl:"
jq -r '.sources[] | "  [\(.priority // "normal")] \(.name): \(.url)"' "$PRD_FILE"
echo ""
echo "Ready! Agent will now process each source and update prd.json status."
