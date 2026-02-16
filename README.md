# Claude Code History Viewer

A simple TUI for browsing all the prompts you've sent during Claude Code sessions.

## Install

```bash
uv sync
```

## Usage

Point it at a directory containing Claude Code `.jsonl` session files:

```bash
uv run python viewer.py ~/.claude/projects/-Users-you-your-project/
```

Claude Code stores session history as JSONL files in `~/.claude/projects/`. Each project gets its own subdirectory with a mangled path name. For example:

```
~/.claude/projects/
  -Users-you-myapp/
    a1b2c3d4-...jsonl
    e5f6a7b8-...jsonl
    memory/
  -Users-you-other-project/
    ...
```

To find your project directories:

```bash
ls ~/.claude/projects/
```

Then pass the one you want:

```bash
uv run python viewer.py ~/.claude/projects/-Users-you-myapp/
```

## Keybindings

| Key | Action |
|-----|--------|
| `h` | Toggle highlight on current prompt |
| `o` | Toggle showing only highlighted prompts |
| `a` | Reset all filters (show all) |
| `l` | Sort by prompt length (longest first) |
| `n` | Sort by natural order |
| `q` | Quit |

Use the search box at the top to filter prompts by text content.
