"""Claude Code History Viewer - browse your prompts from Claude Code sessions."""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from textual import on
from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static
from rich.text import Text


@dataclass
class Prompt:
    index: int
    text: str
    session_id: str
    timestamp: str
    cwd: str
    char_count: int = 0
    highlighted: bool = False

    def __post_init__(self):
        self.char_count = len(self.text)


def parse_sessions(history_dir: Path) -> list[Prompt]:
    """Parse all JSONL session files and extract user prompts."""
    prompts = []
    idx = 0
    for jsonl_file in sorted(history_dir.glob("*.jsonl")):
        session_id = jsonl_file.stem
        with open(jsonl_file) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "user":
                    continue
                msg = obj.get("message", {})
                if msg.get("role") != "user":
                    continue
                content = msg.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            parts.append(block["text"])
                        elif isinstance(block, str):
                            parts.append(block)
                    content = "\n".join(parts)
                if not content.strip():
                    continue
                prompts.append(
                    Prompt(
                        index=idx,
                        text=content.strip(),
                        session_id=session_id[:8],
                        timestamp=obj.get("timestamp", ""),
                        cwd=obj.get("cwd", ""),
                    )
                )
                idx += 1
    return prompts


class PromptItem(ListItem):
    """A single prompt in the list."""

    def __init__(self, prompt: Prompt) -> None:
        super().__init__()
        self.prompt = prompt

    def compose(self):
        preview = self.prompt.text[:120].replace("\n", " ")
        line = Text()
        if self.prompt.highlighted:
            line.append("* ", style="bold yellow")
        else:
            line.append("  ")
        line.append(self.prompt.session_id, style="dim")
        line.append(" ")
        line.append(f"({self.prompt.char_count} chars)", style="cyan")
        line.append("  ")
        line.append(preview)
        yield Static(line)


class HistoryViewer(App):
    CSS = """
    #main {
        height: 1fr;
    }
    #list-pane {
        width: 1fr;
        min-width: 40;
    }
    #preview-pane {
        width: 2fr;
        border-left: solid $accent;
        padding: 1 2;
        overflow-y: auto;
    }
    #preview-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #preview-body {
        width: 100%;
    }
    #filter-bar {
        height: 3;
        padding: 0 1;
    }
    #status {
        height: 1;
        background: $surface;
        padding: 0 1;
        color: $text-muted;
    }
    #search {
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("h", "toggle_highlight", "Toggle Highlight"),
        Binding("o", "show_highlighted_only", "Highlighted Only"),
        Binding("a", "show_all", "Show All"),
        Binding("l", "sort_longest", "Sort by Length"),
        Binding("n", "sort_natural", "Sort by Order"),
        Binding("q", "quit", "Quit"),
    ]

    show_only_highlighted: reactive[bool] = reactive(False)
    sort_by_length: reactive[bool] = reactive(False)

    def __init__(self, prompts: list[Prompt]):
        super().__init__()
        self.all_prompts = prompts
        self.filter_text = ""

    def compose(self):
        yield Header(show_clock=True)
        with Horizontal(id="filter-bar"):
            yield Input(placeholder="Type to filter prompts...", id="search")
        with Horizontal(id="main"):
            with Vertical(id="list-pane"):
                yield ListView(id="prompt-list")
            with Vertical(id="preview-pane"):
                yield Label("Select a prompt to preview", id="preview-title")
                yield Static("", id="preview-body")
        yield Label("", id="status")
        yield Footer()

    def on_mount(self):
        self.title = "Claude Code History Viewer"
        self.rebuild_list()

    def get_visible_prompts(self) -> list[Prompt]:
        prompts = self.all_prompts
        if self.show_only_highlighted:
            prompts = [p for p in prompts if p.highlighted]
        if self.filter_text:
            ft = self.filter_text.lower()
            prompts = [p for p in prompts if ft in p.text.lower()]
        if self.sort_by_length:
            prompts = sorted(prompts, key=lambda p: p.char_count, reverse=True)
        return prompts

    def rebuild_list(self):
        lv = self.query_one("#prompt-list", ListView)
        lv.clear()
        visible = self.get_visible_prompts()
        for p in visible:
            lv.append(PromptItem(p))
        mode = []
        if self.show_only_highlighted:
            mode.append("highlighted only")
        if self.sort_by_length:
            mode.append("sorted by length")
        if self.filter_text:
            mode.append(f'filter: "{self.filter_text}"')
        mode_str = " | ".join(mode) if mode else "all prompts"
        status = Text(f" {len(visible)}/{len(self.all_prompts)} prompts  [{mode_str}]")
        self.query_one("#status", Label).update(status)

    @on(Input.Changed, "#search")
    def on_search_changed(self, event: Input.Changed):
        self.filter_text = event.value
        self.rebuild_list()

    @on(ListView.Selected, "#prompt-list")
    def on_prompt_selected(self, event: ListView.Selected):
        item = event.item
        if isinstance(item, PromptItem):
            self.show_preview(item.prompt)

    @on(ListView.Highlighted, "#prompt-list")
    def on_prompt_highlighted(self, event: ListView.Highlighted):
        item = event.item
        if isinstance(item, PromptItem):
            self.show_preview(item.prompt)

    def show_preview(self, prompt: Prompt):
        star = " [highlighted]" if prompt.highlighted else ""
        title = Text()
        title.append(f"Session {prompt.session_id} | {prompt.char_count} chars{star}")
        self.query_one("#preview-title", Label).update(title)
        self.query_one("#preview-body", Static).update(Text(prompt.text))

    def _get_current_prompt(self) -> Prompt | None:
        lv = self.query_one("#prompt-list", ListView)
        if lv.highlighted_child and isinstance(lv.highlighted_child, PromptItem):
            return lv.highlighted_child.prompt
        return None

    def action_toggle_highlight(self):
        p = self._get_current_prompt()
        if p:
            p.highlighted = not p.highlighted
            self.rebuild_list()
            self.show_preview(p)

    def action_show_highlighted_only(self):
        self.show_only_highlighted = not self.show_only_highlighted
        self.rebuild_list()

    def action_show_all(self):
        self.show_only_highlighted = False
        self.sort_by_length = False
        self.filter_text = ""
        self.query_one("#search", Input).value = ""
        self.rebuild_list()

    def action_sort_longest(self):
        self.sort_by_length = not self.sort_by_length
        self.rebuild_list()

    def action_sort_natural(self):
        self.sort_by_length = False
        self.rebuild_list()


CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def discover_projects() -> list[tuple[str, Path]]:
    """Return (display_name, path) pairs for all projects in ~/.claude/projects/."""
    if not CLAUDE_PROJECTS_DIR.is_dir():
        return []
    projects = []
    username = Path.home().name
    for d in sorted(CLAUDE_PROJECTS_DIR.iterdir()):
        if not d.is_dir() or d.name == "memory":
            continue
        # Mangle: /Users/you/foo/bar -> -Users-you-foo-bar
        # Strip the home-dir prefix; leave the rest as-is to avoid
        # misinterpreting hyphens in real folder names as path separators.
        name = d.name
        prefix = f"-Users-{username}-"
        display = name[len(prefix):] if name.startswith(prefix) else name
        projects.append((display, d))
    return projects


def pick_project_interactive(projects: list[tuple[str, Path]]) -> Path:
    """Print a numbered list and ask the user to pick one."""
    print("Claude Code projects found:\n")
    for i, (name, _) in enumerate(projects, 1):
        print(f"  {i:2}. {name}")
    print()
    while True:
        try:
            raw = input(f"Choose a project [1-{len(projects)}]: ").strip()
            idx = int(raw) - 1
            if 0 <= idx < len(projects):
                return projects[idx][1]
        except (ValueError, EOFError):
            pass
        print(f"Please enter a number between 1 and {len(projects)}.")


def find_project_by_name(name: str, projects: list[tuple[str, Path]]) -> Path | None:
    """Fuzzy-match a project name against the display names."""
    name_lower = name.lower()
    # Exact match first
    for display, path in projects:
        if name_lower == display.lower():
            return path
    # Substring match
    matches = [(display, path) for display, path in projects if name_lower in display.lower()]
    if len(matches) == 1:
        return matches[0][1]
    if len(matches) > 1:
        print(f"Ambiguous project name '{name}'. Matches:")
        for display, _ in matches:
            print(f"  {display}")
        sys.exit(1)
    return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Browse Claude Code session prompts")
    parser.add_argument("directory", nargs="?", help="Path to a session directory")
    parser.add_argument("-p", "--project", help="Project name to look up in ~/.claude/projects/")
    args = parser.parse_args()

    if args.directory:
        history_dir = Path(args.directory)
        if not history_dir.is_dir():
            print(f"Error: {history_dir} is not a directory")
            sys.exit(1)
    elif args.project:
        projects = discover_projects()
        if not projects:
            print(f"No projects found in {CLAUDE_PROJECTS_DIR}")
            sys.exit(1)
        history_dir = find_project_by_name(args.project, projects)
        if history_dir is None:
            print(f"No project matching '{args.project}' found.")
            print("Available projects:")
            for display, _ in projects:
                print(f"  {display}")
            sys.exit(1)
    else:
        projects = discover_projects()
        if not projects:
            print(f"No projects found in {CLAUDE_PROJECTS_DIR}")
            sys.exit(1)
        history_dir = pick_project_interactive(projects)

    prompts = parse_sessions(history_dir)
    if not prompts:
        print("No user prompts found in the history files.")
        sys.exit(1)
    print(f"Loaded {len(prompts)} prompts.")
    app = HistoryViewer(prompts)
    app.run()


if __name__ == "__main__":
    main()
