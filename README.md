# Claude Code History Viewer

A simple TUI for browsing all the prompts you've sent during Claude Code sessions.

## Install

```bash
uv sync
```

## Usage

### Interactive project picker (default)

Run with no arguments and it will find all your Claude Code projects in
`~/.claude/projects/` and ask you to choose one:

```bash
uv run python viewer.py
```

```
Claude Code projects found:

   1. ~/Desktop/coding_playground/myapp
   2. ~/Desktop/other-project
   3. ~/work/some-api

Choose a project [1-3]:
```

### By project name

Pass `-p` with a partial project name and it will match against your projects:

```bash
uv run python viewer.py -p myapp
```

### By directory path

Pass a path directly if you know it:

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

Type in the search box at the top to filter prompts by text content.
