#!/usr/bin/env bash
# Creo update checker -- compares installed commit SHA vs. upstream main.
# Designed to run as a Claude Code SessionStart hook. Silent on success.
# Prints a single-line warning when an update is available. Never fails.
#
# Environment overrides:
#   CREO_SKILL_DIR   override install dir (default: ~/.claude/skills/creo)
#   CREO_REPO        override repo slug   (default: oyusypenko/creo)
#   CREO_TIMEOUT     curl timeout seconds (default: 3)

set +e  # never fail the session

SKILL_DIR="${CREO_SKILL_DIR:-${HOME}/.claude/skills/creo}"
REPO="${CREO_REPO:-oyusypenko/creo}"
TIMEOUT="${CREO_TIMEOUT:-3}"

# Silent exit if Creo isn't installed.
[ -f "${SKILL_DIR}/.version" ] || exit 0

LOCAL_SHA=$(tr -d '[:space:]' < "${SKILL_DIR}/.version")
[ -n "${LOCAL_SHA}" ] || exit 0
[ "${LOCAL_SHA}" = "unknown" ] && exit 0

# Fetch remote HEAD SHA. Try GitHub API first (no auth, 60 req/hour per IP),
# fall back to git ls-remote if curl fails.
REMOTE_SHA=$(curl -fsSL -m "${TIMEOUT}" \
    "https://api.github.com/repos/${REPO}/commits/main" 2>/dev/null \
    | grep -m1 '"sha"' \
    | cut -d'"' -f4)

if [ -z "${REMOTE_SHA}" ]; then
    REMOTE_SHA=$(git ls-remote "https://github.com/${REPO}" refs/heads/main 2>/dev/null \
        | cut -f1)
fi

# Silent if we couldn't reach GitHub.
[ -n "${REMOTE_SHA}" ] || exit 0

if [ "${LOCAL_SHA}" != "${REMOTE_SHA}" ]; then
    printf '⚠ Creo update available: installed %s → remote %s\n' \
        "${LOCAL_SHA:0:7}" "${REMOTE_SHA:0:7}"
    printf '  Update: curl -fsSL https://raw.githubusercontent.com/%s/main/update.sh | bash\n' \
        "${REPO}"
fi

exit 0
