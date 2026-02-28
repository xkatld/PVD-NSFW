import argparse
import sys
import time
from src.core.collector import VideoCollector
from rich.console import Console


def main():
    console = Console()
    console.print("\n[bold cyan]=== AiwangTT Video Downloader ===[/bold cyan]\n")

    parser = argparse.ArgumentParser(description="AiwangTT Video Downloader", add_help=False)
    parser.add_argument("--id", type=int)
    parser.add_argument("--range", nargs=2, type=int)
    parser.add_argument("--list", nargs="+", type=int)
    parser.add_argument("--keyword", type=str)
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--help", action="store_true")

    args = parser.parse_args()

    if args.help or len(sys.argv) == 1:
        parser.print_help()
        return

    collector = VideoCollector(is_local=args.local)

    try:
        if args.stats:
            total, success = collector.db.get_stats()
            console.print(f"[cyan]总数:[/cyan] {total} | [green]成功:[/green] {success} | [red]失败:[/red] {total - success}")

        if args.keyword:
            collector.search_and_batch_process(args.keyword)
        elif args.id:
            collector.process_video(args.id)
        elif args.range:
            collector.batch_process(args.range[0], args.range[1])
        elif args.list:
            collector.list_process(args.list)

    except KeyboardInterrupt:
        console.print("\n[yellow][!] 用户中断，退出程序...[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
