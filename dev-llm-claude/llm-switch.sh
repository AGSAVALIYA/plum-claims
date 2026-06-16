#!/usr/bin/env bash

# Usage:
# source llm-switch.sh deepseek
# source llm-switch.sh mimo

ENV_FILE="./dev-llm-claude/.llm.env"

if [[ -f "$ENV_FILE" ]]; then
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "Error: $ENV_FILE not found"
    return 1 2>/dev/null || exit 1
fi

case "$1" in
    deepseek)
        export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
        export ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY"

        export ANTHROPIC_MODEL="deepseek-v4-pro"
        export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro"
        export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro"
        export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"

        export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
        export CLAUDE_CODE_EFFORT_LEVEL="high"
        ;;
        
    mimo)
        export ANTHROPIC_BASE_URL="https://api.xiaomimimo.com/anthropic"
        export ANTHROPIC_AUTH_TOKEN="$MIMO_API_KEY"

        export ANTHROPIC_MODEL="mimo-v2.5-pro"
        export ANTHROPIC_DEFAULT_OPUS_MODEL="mimo-v2.5-pro"
        export ANTHROPIC_DEFAULT_SONNET_MODEL="mimo-v2.5-pro"
        export ANTHROPIC_DEFAULT_HAIKU_MODEL="mimo-v2.5-pro"

        export CLAUDE_CODE_SUBAGENT_MODEL="mimo-v2.5-pro"
        export CLAUDE_CODE_EFFORT_LEVEL="high"
        ;;
        
    *)
        echo "Usage: source llm-switch.sh {deepseek|mimo}"
        return 1 2>/dev/null || exit 1
        ;;
esac

echo "✓ Switched to $1"
echo "Base URL: $ANTHROPIC_BASE_URL"
echo "Model: $ANTHROPIC_MODEL"