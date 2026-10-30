#!/usr/bin/env bash
# Status line for Claude Code. Saves the account's rate-limit data for hooks,
# then prints: model | 5h % | 7d % | context %.
# Install: copy to ~/.claude/usage_statusline.sh, chmod +x, add the statusLine
# entry from settings-snippet.json to ~/.claude/settings.json.
in=$(cat)
state="$HOME/.claude/usage-state.json"

rl=$(jq -c '.rate_limits // empty' <<<"$in" 2>/dev/null)
if [ -n "$rl" ] && [ "$rl" != "null" ]; then
  jq -c --argjson now "$(date +%s)" '. + {updated_at: $now}' <<<"$rl" > "$state.tmp" \
    && mv "$state.tmp" "$state"
fi

model=$(jq -r '.model.display_name // ""' <<<"$in")
fh=$(jq -r '.rate_limits.five_hour.used_percentage // "?" | if type=="number" then floor else . end' <<<"$in")
wk=$(jq -r '.rate_limits.seven_day.used_percentage // "?" | if type=="number" then floor else . end' <<<"$in")
ctx=$(jq -r '.context_window.used_percentage // "?" | if type=="number" then floor else . end' <<<"$in")
printf '%s | 5h %s%% | 7d %s%% | ctx %s%%\n' "$model" "$fh" "$wk" "$ctx"
