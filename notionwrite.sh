#!/usr/bin/env bash
#
# Notion terminal writer v3
# Features:
#   • fzf database selector
#   • optional --markdown conversion (pandoc)
#   • gum/whiptail UI input
#   • append to existing page
#

NOTION_TOKEN="secret_xxx_your_token_here"
NOTION_VERSION="2022-06-28"

# --- Helpers ---
usage() {
  echo "Usage: $0 [--markdown]"
  echo "Requires: curl, jq, fzf"
  echo "Optional: gum or whiptail, pandoc"
  exit 1
}

for cmd in curl jq fzf; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "❌ Missing: $cmd"
    exit 1
  }
done

MARKDOWN_MODE=false
[[ "$1" == "--markdown" ]] && MARKDOWN_MODE=true

DB_FILE="$HOME/.notion_databases.json"

if [[ ! -f "$DB_FILE" ]]; then
  echo "❌ Missing database config: $DB_FILE"
  echo "Create it like:"
  echo '[{"name": "Notes", "id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}]'
  exit 1
fi

# --- Select Database ---
DB_CHOICE=$(jq -r '.[] | "\(.name)\t\(.id)"' "$DB_FILE" | fzf --prompt "Select a Notion Database: " --with-nth=1)
DATABASE_ID=$(echo "$DB_CHOICE" | awk '{print $2}')

[[ -z "$DATABASE_ID" ]] && { echo "❌ No database selected"; exit 1; }

# --- Choose Mode ---
MODE=$(printf "Create new page\nAppend to existing page" | fzf --prompt "Choose action: ")

if [[ "$MODE" == "Append to existing page" ]]; then
  echo "Fetching recent pages..."
  PAGE_LIST=$(curl -s -X POST "https://api.notion.com/v1/databases/${DATABASE_ID}/query" \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Notion-Version: ${NOTION_VERSION}" | jq -r '.results[] | "\(.properties.Name.title[0].plain_text)\t\(.id)"' )

  PAGE_CHOICE=$(echo "$PAGE_LIST" | fzf --prompt "Select page to append: " --with-nth=1)
  PAGE_ID=$(echo "$PAGE_CHOICE" | awk '{print $2}')

  if [[ -z "$PAGE_ID" ]]; then
    echo "❌ No page selected."
    exit 1
  fi
fi

# --- UI input ---
if command -v gum >/dev/null 2>&1; then
  if [[ "$MODE" == "Create new page" ]]; then
    TITLE=$(gum input --placeholder "Enter page title")
  fi
  echo "📝 Write your note (Ctrl+D to save):"
  CONTENT=$(gum write)
else
  [[ "$MODE" == "Create new page" ]] && TITLE=$(whiptail --inputbox "Enter page title" 8 60 3>&1 1>&2 2>&3)
  echo "📝 Write your note (Ctrl+D to save):"
  CONTENT=$(cat)
fi

[[ -z "$CONTENT" ]] && { echo "❌ No content."; exit 1; }
[[ -z "$TITLE" ]] && TITLE="Untitled"

# --- Markdown conversion ---
if $MARKDOWN_MODE; then
  if ! command -v pandoc >/dev/null 2>&1; then
    echo "❌ Pandoc required for markdown mode"
    exit 1
  fi
  CONTENT=$(echo "$CONTENT" | pandoc -f markdown -t plain)
fi

CONTENT_JSON=$(echo "$CONTENT" | jq -Rs '.')

# --- Create or Append ---
if [[ "$MODE" == "Create new page" ]]; then
  echo "📄 Creating new page '$TITLE'..."
  response=$(curl -s -X POST "https://api.notion.com/v1/pages" \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Notion-Version: ${NOTION_VERSION}" \
    -d "{
      \"parent\": { \"database_id\": \"${DATABASE_ID}\" },
      \"properties\": {
        \"Name\": {\"title\": [{\"text\": {\"content\": \"${TITLE}\"}}]}
      },
      \"children\": [
        {
          \"object\": \"block\",
          \"type\": \"paragraph\",
          \"paragraph\": {
            \"rich_text\": [
              {\"type\": \"text\", \"text\": {\"content\": ${CONTENT_JSON}}}
            ]
          }
        }
      ]
    }")
else
  echo "➕ Appending to page..."
  response=$(curl -s -X PATCH "https://api.notion.com/v1/blocks/${PAGE_ID}/children" \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Notion-Version: ${NOTION_VERSION}" \
    -d "{
      \"children\": [
        {
          \"object\": \"block\",
          \"type\": \"paragraph\",
          \"paragraph\": {
            \"rich_text\": [
              {\"type\": \"text\", \"text\": {\"content\": ${CONTENT_JSON}}}
            ]
          }
        }
      ]
    }")
fi

echo "$response" | jq .
echo "✅ Done!"