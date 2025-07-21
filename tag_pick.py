import csv
import questionary
from rich.console import Console
from rich.panel import Panel

console = Console()

def load_words(filename="words.csv"):
    """Loads words from a CSV file."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            return [row[0] for row in reader]
    except FileNotFoundError:
        console.print(f"[bold red]エラー: {filename} が見つかりません。[/bold red]")
        return None

def print_help():
    """Prints the help message inside a panel."""
    help_text = (
        "このツールは、単語リストから対話形式で単語を検索し、\n"
        "必要な単語をピックアップしてリストを作成するためのものです。\n\n"
        "[bold]主な操作:[/bold]\n"
        "- [bold]単語を検索してピックアップする[/bold]:\n"
        "  1. 検索したい単語を入力します。\n"
        "  2. 検索結果がリストで表示されます。\n"
        "  3. [bold]↑↓キー[/bold]で移動し、[bold]スペースキー[/bold]でピックアップする単語を選択(複数可)します。\n"
        "  4. [bold]Enterキー[/bold]で選択を確定します。\n"
        "- [bold]ピックアップリストから削除する[/bold]:\n"
        "  1. 現在のピックアップリストが表示されます。\n"
        "  2. 同様に、[bold]スペースキー[/bold]で削除したい単語を選択し、[bold]Enterキー[/bold]で確定します。"
    )
    console.print(Panel(help_text, title="[bold cyan]ヘルプ[/bold cyan]", border_style="cyan"))

def main():
    """Main function for the interactive CLI app."""
    all_words = load_words()
    if all_words is None:
        return

    picked_words = []

    console.print(Panel("[bold]単語ピックアップツールへようこそ！[/bold]", style="bold blue"))

    while True:
        console.print("\n[bold green]現在のピックアップリスト:[/bold green]")
        if picked_words:
            console.print(", ".join(picked_words))
        else:
            console.print("[dim]（空）[/dim]")

        action = questionary.select(
            "何をしますか？",
            choices=[
                "単語を検索してピックアップする",
                "ピックアップリストから削除する",
                "ヘルプを表示する",
                "終了する",
            ],
        ).ask()

        if action is None or action == "終了する":
            console.print("[bold blue]アプリケーションを終了します。[/bold blue]")
            break

        elif action == "単語を検索してピックアップする":
            search_term = questionary.text("検索語を入力してください:").ask()
            if not search_term:
                continue

            search_results = sorted([w for w in all_words if search_term.lower() in w.lower() and w not in picked_words])

            if not search_results:
                console.print("[yellow]一致する単語は見つかりませんでした。[/yellow]")
                continue

            words_to_add = questionary.checkbox(
                "ピックアップする単語をスペースキーで選択してください（Enterで確定）:",
                choices=search_results,
            ).ask()

            if words_to_add:
                picked_words.extend(words_to_add)
                picked_words = sorted(list(set(picked_words))) # Remove duplicates and sort
                console.print(f"[bold green]✓ {len(words_to_add)}件の単語をピックアップしました。[/bold green]")

        elif action == "ピックアップリストから削除する":
            if not picked_words:
                console.print("[yellow]削除する単語がありません。[/yellow]")
                continue

            words_to_remove = questionary.checkbox(
                "削除する単語をスペースキーで選択してください（Enterで確定）:",
                choices=picked_words,
            ).ask()

            if words_to_remove:
                picked_words = [w for w in picked_words if w not in words_to_remove]
                console.print(f"[bold yellow]✗ {len(words_to_remove)}件の単語を削除しました。[/bold yellow]")

        elif action == "ヘルプを表示する":
            print_help()

if __name__ == "__main__":
    main()
