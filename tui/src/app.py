from __future__ import annotations

import os

import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Header, LoadingIndicator, Static

RAG_URL = os.environ.get("RAG_URL", "http://localhost:8000")
LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
LIST_BATCH = 100

STATUS_LOADED = "[green]\u2713[/green]"
STATUS_LOADING = "[yellow]\u27f3[/yellow]"
STATUS_ERROR = "[red]\u2717[/red]"
STATUS_EMPTY = ""

COL_STATUS = "status"
COL_ID = "id"
COL_TITLE = "title"
COL_DIFFICULTY = "difficulty"
COL_TAGS = "tags"

QUESTION_LIST_QUERY = """
query($limit: Int, $skip: Int) {
  problemsetQuestionListV2(limit: $limit, skip: $skip) {
    totalLength
    questions {
      questionFrontendId
      title
      titleSlug
      difficulty
      paidOnly
      topicTags { name }
    }
  }
}
"""


class ProblemLoaderApp(App):
    CSS = """
    DataTable {
        height: 1fr;
    }
    LoadingIndicator {
        height: 3;
    }
    #rag-url {
        height: 1;
        color: $text-disabled;
        padding: 0 1;
    }
    """

    TITLE = "LeetCode Problem Loader"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._problems: list[dict] = []
        self._loaded_slugs: set[str] = set()
        self._loading_slugs: set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield LoadingIndicator()
        yield DataTable(cursor_type="row")
        yield Static(f"RAG: {RAG_URL}", id="rag-url")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Status", key=COL_STATUS, width=8)
        table.add_column("ID", key=COL_ID, width=8)
        table.add_column("Title", key=COL_TITLE)
        table.add_column("Difficulty", key=COL_DIFFICULTY, width=12)
        table.add_column("Tags", key=COL_TAGS, width=40)
        table.display = False
        self._fetch_data()

    @work(exclusive=True, group="fetch")
    async def _fetch_data(self) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            problems = await self._fetch_all_problems(client)
            loaded_slugs = await self._fetch_loaded_slugs(client)

        self._problems = problems
        self._loaded_slugs = set(loaded_slugs)
        self._rebuild_table()

    async def _fetch_all_problems(self, client: httpx.AsyncClient) -> list[dict]:
        try:
            resp = await client.post(
                LEETCODE_GRAPHQL_URL,
                json={"query": QUESTION_LIST_QUERY, "variables": {"skip": 0, "limit": LIST_BATCH}},
                headers={"Content-Type": "application/json", "Referer": "https://leetcode.com"},
            )
            resp.raise_for_status()
            data = resp.json()["data"]["problemsetQuestionListV2"]
            total = data["totalLength"]
            all_questions = list(data["questions"])

            for skip in range(LIST_BATCH, total, LIST_BATCH):
                resp = await client.post(
                    LEETCODE_GRAPHQL_URL,
                    json={"query": QUESTION_LIST_QUERY, "variables": {"skip": skip, "limit": LIST_BATCH}},
                    headers={"Content-Type": "application/json", "Referer": "https://leetcode.com"},
                )
                resp.raise_for_status()
                page = resp.json()["data"]["problemsetQuestionListV2"]
                all_questions.extend(page["questions"])
        except Exception:
            return []

        problems = [
            {
                "id": q["questionFrontendId"],
                "slug": q["titleSlug"],
                "title": q["title"],
                "difficulty": q["difficulty"].capitalize(),
                "tags": ", ".join(t["name"] for t in (q.get("topicTags") or [])),
            }
            for q in all_questions
            if not q.get("paidOnly")
        ]
        problems.sort(key=lambda p: int(p["id"]))
        return problems

    async def _fetch_loaded_slugs(self, client: httpx.AsyncClient) -> list[str]:
        try:
            resp = await client.get(f"{RAG_URL}/problems/slugs")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []

    def _rebuild_table(self) -> None:
        self.query_one(LoadingIndicator).display = False
        table = self.query_one(DataTable)
        table.display = True
        table.clear()

        for problem in self._problems:
            slug = problem["slug"]
            if slug in self._loading_slugs:
                status = STATUS_LOADING
            elif slug in self._loaded_slugs:
                status = STATUS_LOADED
            else:
                status = STATUS_EMPTY
            table.add_row(
                status,
                problem["id"],
                problem["title"],
                problem["difficulty"],
                problem["tags"],
                key=slug,
            )

        self.sub_title = f"{len(self._problems)} problems, {len(self._loaded_slugs)} loaded"
        table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        slug = str(event.row_key.value)

        if slug in self._loaded_slugs or slug in self._loading_slugs:
            return

        self._loading_slugs.add(slug)
        self._update_row_status(slug, STATUS_LOADING)
        self._do_load_problem(slug)

    @work(thread=False)
    async def _do_load_problem(self, slug: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{RAG_URL}/problems/load",
                    json={"slug": slug},
                )
                response.raise_for_status()
            self._loading_slugs.discard(slug)
            self._loaded_slugs.add(slug)
            self._update_row_status(slug, STATUS_LOADED)
            self.sub_title = f"{len(self._problems)} problems, {len(self._loaded_slugs)} loaded"
        except Exception:
            self._loading_slugs.discard(slug)
            self._update_row_status(slug, STATUS_ERROR)

    def _update_row_status(self, slug: str, status: str) -> None:
        table = self.query_one(DataTable)
        table.update_cell(slug, COL_STATUS, status)

    def action_refresh(self) -> None:
        self.query_one(LoadingIndicator).display = True
        self.query_one(DataTable).display = False
        self._fetch_data()

    def action_quit(self) -> None:
        self.exit()


def main():
    app = ProblemLoaderApp()
    app.run()


if __name__ == "__main__":
    main()
