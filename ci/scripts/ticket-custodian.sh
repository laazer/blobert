#!/bin/bash
# ticket-custodian.sh — Atomic ticket state transitions
#
# Manages ticket lifecycle state transitions (backlog → in_progress → done).
# Preserves git history using `git mv`, updates CHECKPOINTS.md index, and commits atomically.
#
# Usage:
#     bash ci/scripts/ticket-custodian.sh move <ticket-path> <destination-folder>
#     bash ci/scripts/ticket-custodian.sh status <ticket-path>
#
# Commands:
#     move TICKET DEST    — Move ticket file to destination folder and update index
#     status TICKET       — Display current location and status
#
# Exit codes:
#     0  — success
#     1  — usage error or ticket not found
#     2  — git operation failed
#     3  — index update failed

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
readonly CHECKPOINTS_INDEX="$REPO_ROOT/project_board/CHECKPOINTS.md"

# Color output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${GREEN}✓${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $*" >&2
}

log_error() {
    echo -e "${RED}✗${NC} $*" >&2
}

# Validate ticket file exists
validate_ticket() {
    local ticket="$1"
    if [[ ! -f "$ticket" ]]; then
        log_error "Ticket not found: $ticket"
        return 1
    fi
}

# Extract ticket ID from path (e.g., 02_complete/01_validation_gate_framework.md → M902-01)
extract_ticket_id() {
    local ticket="$1"
    local filename=$(basename "$ticket" .md)

    # Check if filename starts with a number and underscore (e.g., 01_validation...)
    if [[ $filename =~ ^[0-9]+_(.+)$ ]]; then
        # Extract ticket ID from filename (format: NN_slug)
        # For M902 tickets, the path contains "902_milestone..." so we infer the ID
        local milestone_dir=$(dirname "$ticket")
        if [[ $milestone_dir =~ 902_milestone_902 ]]; then
            local num=$(echo "$filename" | sed 's/^0*\([0-9]*\)_.*/\1/')
            echo "M902-$num"
        else
            echo "$filename"
        fi
    else
        echo "$filename"
    fi
}

# Get folder name from path (e.g., project_board/902_*/01_active/...)
get_current_folder() {
    local ticket="$1"
    local parts=$(echo "$ticket" | tr '/' '\n')

    for part in $parts; do
        # Match folders like: 00_backlog, 01_active, 01_in_progress, 02_complete, 02_done
        if [[ "$part" =~ ^[0-9]+_(backlog|in_progress|active|done|complete)$ ]]; then
            echo "${part#*_}"  # Strip number prefix
            return 0
        fi
        # Also match non-numbered versions for backward compatibility
        if [[ "$part" =~ ^(backlog|in_progress|active|done|complete)$ ]]; then
            echo "$part"
            return 0
        fi
    done
    echo "unknown"
}

# Move ticket file using git mv and update index
move_ticket() {
    local source="$1"
    local dest_folder="$2"

    # Normalize paths
    source="${source#./}"

    validate_ticket "$source" || return 1

    # Determine new path
    local dir=$(dirname "$source")
    local filename=$(basename "$source")
    local parent_dir=$(dirname "$dir")

    # Map friendly folder names to actual folder names
    case "$dest_folder" in
        backlog)     dest_folder="00_backlog" ;;
        in_progress) dest_folder="01_active" ;;
        active)      dest_folder="01_active" ;;
        done)        dest_folder="02_complete" ;;
        complete)    dest_folder="02_complete" ;;
    esac

    local new_path="$parent_dir/$dest_folder/$filename"

    # Ensure destination directory exists
    mkdir -p "$(dirname "$new_path")"

    # Extract info for index update
    local ticket_id=$(extract_ticket_id "$source")
    local current_folder=$(get_current_folder "$source")
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    log_info "Moving: $source → $new_path"

    # Use git mv to preserve history
    if ! git -C "$REPO_ROOT" mv "$source" "$new_path" 2>/dev/null; then
        log_error "git mv failed (file may already be staged or moved)"
        return 2
    fi

    # Update CHECKPOINTS.md index
    if [[ -f "$CHECKPOINTS_INDEX" ]]; then
        # Remove old pointer (grep for line containing the ticket path)
        local old_line=$(grep -F "$source" "$CHECKPOINTS_INDEX" 2>/dev/null || echo "")
        if [[ -n "$old_line" ]]; then
            # Use a temporary file for safe editing
            local temp_index=$(mktemp)
            grep -v -F "$source" "$CHECKPOINTS_INDEX" > "$temp_index" || true
            mv "$temp_index" "$CHECKPOINTS_INDEX"
            log_info "Updated CHECKPOINTS.md: removed old pointer"
        fi

        # Add new pointer in the appropriate section
        local new_line="- [$ticket_id]($new_path) — Moved to $dest_folder on $timestamp"
        echo "$new_line" >> "$CHECKPOINTS_INDEX"
        log_info "Updated CHECKPOINTS.md: added new pointer"
    else
        log_warn "CHECKPOINTS.md not found; skipping index update"
    fi

    # Stage changes
    git -C "$REPO_ROOT" add "$CHECKPOINTS_INDEX" 2>/dev/null || true

    # Commit
    local commit_msg="chore: move $ticket_id from $current_folder to $dest_folder"
    if ! git -C "$REPO_ROOT" commit -m "$commit_msg" 2>/dev/null; then
        log_warn "No changes to commit (file already staged or moved)"
    else
        log_info "Committed: $commit_msg"
    fi

    log_info "Ticket state transition complete"
    return 0
}

# Display ticket status
status_ticket() {
    local ticket="$1"

    validate_ticket "$ticket" || return 1

    local ticket_id=$(extract_ticket_id "$ticket")
    local folder=$(get_current_folder "$ticket")
    local last_modified=$(git -C "$REPO_ROOT" log -1 --format="%aI %s" -- "$ticket" 2>/dev/null || echo "unknown")

    echo "Ticket: $ticket_id"
    echo "Path: $ticket"
    echo "Folder: $folder"
    echo "Last modified: $last_modified"
}

# Main
main() {
    if [[ $# -lt 2 ]]; then
        cat >&2 << 'EOF'
Usage: bash ci/scripts/ticket-custodian.sh <command> <args>

Commands:
  move TICKET DEST   — Move ticket to destination folder (backlog|in_progress|done)
  status TICKET      — Display ticket status

Example:
  bash ci/scripts/ticket-custodian.sh move project_board/902_*/01_active/07_governance_audit_pipeline_and_baseline.md done
  bash ci/scripts/ticket-custodian.sh status project_board/902_*/02_complete/06_per_stage_gate_improvements.md
EOF
        return 1
    fi

    local cmd="$1"
    shift

    case "$cmd" in
        move)
            if [[ $# -ne 2 ]]; then
                log_error "move requires TICKET and DEST arguments"
                return 1
            fi
            move_ticket "$1" "$2"
            ;;
        status)
            if [[ $# -ne 1 ]]; then
                log_error "status requires TICKET argument"
                return 1
            fi
            status_ticket "$1"
            ;;
        *)
            log_error "Unknown command: $cmd"
            return 1
            ;;
    esac
}

main "$@"
