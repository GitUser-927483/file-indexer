import os
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table

console = Console()
last_result = None


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title):
    """Print decorative header using ASCII only"""
    # Center the header text properly
    header_lines = [
        "=" * 74,
        "",
        "                      FILE INDEXER - CLI TOOL",
        "                     Fast * Reliable * Easy to Use",
        "",
        "=" * 74,
    ]
    header = "\n".join(header_lines)
    console.print(Panel(header, border_style="green", padding=(0, 2)))
    console.print(Panel(f"[bold green]{title}[/bold green]", border_style="green", padding=(0, 2)))
    console.print()


def print_menu():
    clear_screen()
    print_header("MAIN MENU")
    
    # Compact menu with tight spacing
    console.print("[cyan]1.[/cyan] Index specific directory")
    console.print("[cyan]2.[/cyan] Index all drives")
    console.print("[cyan]3.[/cyan] Index a specific drive")
    console.print("[cyan]4.[/cyan] View last result")
    console.print("[cyan]5.[/cyan] Exit")
    console.print()
    console.print("[bold cyan]Enter your choice: [/bold cyan]", end="")


def get_drives():
    try:
        from src.indexer import get_windows_drives
        return get_windows_drives()
    except Exception:
        return []


def format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def index_path(paths, output_path, sort_by="path"):
    global last_result
    
    files = []
    total_count = 0
    
    console.print(f"\n[yellow]Starting indexing...[/yellow]")
    console.print(f"Target: {', '.join(paths)}\n")
    
    # Phase 1: Quick scan to count files with spinner
    console.print("[bold]Scanning files...[/bold]")
    
    from src.indexer import index_directory
    
    # Quick pass to count total files
    all_files = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]Counting files...", total=None)
        
        for path in paths:
            try:
                console.print(f"  Scanning: {path}")
                for metadata in index_directory(path):
                    all_files.append(metadata)
                    # Update spinner to show we're still working
                    progress.update(task, description=f"[cyan]Found {len(all_files):,} files...")
            except Exception as e:
                console.print(f"[red]  Error scanning {path}: {e}[/red]")
    
    total_files = len(all_files)
    if total_files == 0:
        console.print("[yellow]No files found to index.[/yellow]")
        try:
            console.input()
        except EOFError:
            pass
        return
    
    console.print(f"[green]Found {total_files:,} files to index[/green]\n")
    
    # Phase 2: Process files with progress bar
    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        BarColumn(bar_width=40),
        TextColumn("[white]{task.fields[status]}"),
        TimeRemainingColumn(),
        console=console,
        auto_refresh=True
    ) as progress:
        
        task = progress.add_task(
            "[white]Processing...",
            total=total_files,
            status="Starting..."
        )
        
        # Process files with progress updates
        for i, metadata in enumerate(all_files, 1):
            files.append(metadata)
            progress.update(task, advance=1, status=f"File {i:,}/{total_files:,}")
        
        progress.update(task, description="[green]Complete!", status="Done")
    
    console.print(f"\n[bold green]Indexing completed![/bold green]")
    console.print(f"Total files indexed: {total_count:,}")
    
    try:
        from src.output import sort_files, create_index_result, save_with_duplicate_check
        console.print("[dim]Sorting results...[/dim]")
        sorted_files = sort_files(files, sort_by)
        result = create_index_result(sorted_files, paths)
        
        # Get base name from output path
        base_name = os.path.splitext(os.path.basename(output_path))[0]
        
        # Save files with duplicate protection to dedicated folder
        console.print("[dim]Saving files...[/dim]")
        saved_files = save_with_duplicate_check(result, base_name, indent=2)
        
        last_result = result
        
        console.print(f"[green]Main index saved to:[/green]")
        console.print(f"    {saved_files['index_file']}")
        console.print(f"[green]Directory structure saved to:[/green]")
        console.print(f"    {saved_files['structure_file']}")
        
    except FileExistsError as e:
        console.print(f"[red]File already exists: {e}[/red]")
        console.print("[yellow]Please try a different filename or wait a moment.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error saving results: {e}[/red]")
    
    console.print("\n[bold]Press Enter to continue...[/bold]")
    try:
        console.input()
    except EOFError:
        pass


def index_specific_directory():
    console.print("\n[bold]Index Specific Directory[/bold]")
    console.print("-" * 50)
    
    path = console.input("Enter directory path: ").strip()
    
    if not path:
        console.print("[yellow]No path entered.[/yellow]")
        try:
            console.input()
        except EOFError:
            pass
        return
    
    if not os.path.exists(path):
        console.print(f"[red]Path does not exist: {path}[/red]")
        try:
            console.input()
        except EOFError:
            pass
        return
    
    output_path = console.input("Output filename (default: index.json): ").strip()
    if not output_path:
        output_path = "index.json"
    
    if not output_path.endswith('.json'):
        output_path += '.json'
    
    index_path([path], output_path)


def index_all_drives():
    drives = get_drives()
    
    if not drives:
        console.print("[yellow]No drives found.[/yellow]")
        try:
            console.input()
        except EOFError:
            pass
        return
    
    console.print(f"\n[bold]Found {len(drives)} drives:[/bold]")
    for drive in drives:
        console.print(f"  • {drive}")
    
    confirm = console.input("\n[yellow]Index all drives? This may take a long time. (y/n): [/yellow]").strip().lower()
    
    if confirm != 'y':
        return
    
    output_path = console.input("Output filename (default: index_all_drives.json): ").strip()
    if not output_path:
        output_path = "index_all_drives.json"
    
    if not output_path.endswith('.json'):
        output_path += '.json'
    
    index_path(drives, output_path)


def index_specific_drive():
    drives = get_drives()
    
    if not drives:
        console.print("[yellow]No drives found.[/yellow]")
        try:
            console.input()
        except EOFError:
            pass
        return
    
    console.print("\n[bold]Available drives:[/bold]")
    for i, drive in enumerate(drives, 1):
        console.print(f"[cyan]{i}. {drive}[/cyan]")
    console.print()
    
    try:
        choice = int(console.input("Select drive number: "))
        if choice < 1 or choice > len(drives):
            console.print("[red]Invalid selection.[/red]")
            try:
                console.input()
            except EOFError:
                pass
            return
        
        selected_drive = drives[choice - 1]
    except ValueError:
        console.print("[red]Invalid input.[/red]")
        try:
            console.input()
        except EOFError:
            pass
        return
    
    output_path = console.input("Output filename (default: index_drive.json): ").strip()
    if not output_path:
        output_path = "index_drive.json"
    
    if not output_path.endswith('.json'):
        output_path += '.json'
    
    index_path([selected_drive], output_path)


def view_last_result():
    global last_result
    
    if last_result is None:
        console.print("[yellow]No previous indexing result available.[/yellow]")
        try:
            console.input()
        except EOFError:
            pass
        return
    
    clear_screen()
    print_header("LAST INDEXING RESULT")
    
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"[green]  Total files: {last_result.summary.total_files:,}[/green]")
    console.print(f"[green]  Total size: {format_size(last_result.summary.total_size)}[/green]")
    console.print(f"[green]  Indexed paths: {', '.join(last_result.summary.indexed_paths)}[/green]")
    console.print(f"[green]  Timestamp: {last_result.summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/green]")
    
    console.print("\n[bold]First 10 files:[/bold]")
    for i, f in enumerate(last_result.files[:10], 1):
        console.print(f"[cyan]{i}. {f.name}[/cyan]")
        console.print(f"   [dim]Path: {f.path}[/dim]")
        console.print(f"   [dim]Size: {format_size(f.size)}[/dim]")
    
    if len(last_result.files) > 10:
        console.print(f"\n[dim]  ... and {len(last_result.files) - 10} more files[/dim]")
    
    try:
        console.input()
    except EOFError:
        pass


def main():
    while True:
        print_menu()
        
        try:
            choice = console.input().strip()
        except EOFError:
            break
        
        if choice == '1':
            index_specific_directory()
        elif choice == '2':
            index_all_drives()
        elif choice == '3':
            index_specific_drive()
        elif choice == '4':
            view_last_result()
        elif choice == '5':
            console.print("\n[bold green]Goodbye![/bold green]")
            break
        else:
            console.print("[yellow]Invalid choice. Please try again.[/yellow]")
            try:
                console.input()
            except EOFError:
                pass


if __name__ == "__main__":
    main()