import os
import sys
import time
import gc
import threading
import time as time_module
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table

console = Console()
last_result = None

# Global settings for damage prevention
SETTINGS = {
    "batch_size": 1000,           # Files per batch
    "batch_delay": 0.01,         # Delay between batches (seconds)
    "reduce_priority": True,      # Lower process priority
    "exclude_system_folders": True,# Exclude Windows system folders
    "max_memory_mb": 500,        # Max memory before batch cleanup
    "output_folder": "file_indexer/output",  # Default output folder
}

# System folders to exclude by default
SYSTEM_FOLDERS = {
    "$Recycle.Bin",
    "System Volume Information",
    "Windows",
    "ProgramData",
    "Recovery",
    "Config.Msi",
    "MSOCache",
    "$WinREAgent",
    "Program Files",
    "Program Files (x86)",
}


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def set_low_priority():
    """Reduce process priority to minimize system impact."""
    if os.name == 'nt' and SETTINGS["reduce_priority"]:
        try:
            import ctypes
            PROCESS_SET_INFORMATION = 0x0200
            IDLE_PROCESS_PRIORITY_CLASS = 0x40
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetPriorityClass(handle, IDLE_PROCESS_PRIORITY_CLASS)
        except Exception:
            pass  # Silently fail if not admin


def get_memory_usage():
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0


def check_system_folders(path):
    """Check if path contains system folders to exclude."""
    if not SETTINGS["exclude_system_folders"]:
        return False
    
    path_parts = path.split(os.sep)
    for part in path_parts:
        if part in SYSTEM_FOLDERS:
            return True
    return False


def get_drive_letter(path):
    """Extract drive letter from path."""
    if len(path) >= 2 and path[1] == ':':
        return path[0].upper()
    return None


def check_output_location(paths):
    """Check if output location is on same drive as indexed paths."""
    output_drive = get_drive_letter(SETTINGS["output_folder"])
    if not output_drive:
        return None
    
    indexed_drives = set()
    for path in paths:
        drive = get_drive_letter(path)
        if drive:
            indexed_drives.add(drive)
    
    if output_drive in indexed_drives:
        return output_drive
    return None


def print_menu():
    clear_screen()
    
    # Compact menu with tight spacing
    console.print("[bold cyan]MAIN MENU[/bold cyan]")
    console.print("-" * 40)
    console.print("[cyan]1.[/cyan] Index specific directory")
    console.print("[cyan]2.[/cyan] Index all drives")
    console.print("[cyan]3.[/cyan] Index a specific drive")
    console.print("[cyan]4.[/cyan] View last result")
    console.print("[cyan]5.[/cyan] Settings")
    console.print("[cyan]6.[/cyan] Exit")
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


def show_settings():
    """Display and allow editing of settings."""
    while True:
        clear_screen()
        console.print("[bold cyan]SETTINGS[/bold cyan]")
        console.print("-" * 40)
        console.print(f"[cyan]1.[/cyan] Batch size: {SETTINGS['batch_size']} files")
        console.print(f"[cyan]2.[/cyan] Batch delay: {SETTINGS['batch_delay']*1000:.1f}ms")
        console.print(f"[cyan]3.[/cyan] Reduce process priority: {SETTINGS['reduce_priority']}")
        console.print(f"[cyan]4.[/cyan] Exclude system folders: {SETTINGS['exclude_system_folders']}")
        console.print(f"[cyan]5.[/cyan] Output folder: {SETTINGS['output_folder']}")
        console.print(f"[cyan]6.[/cyan] Back to main menu")
        console.print()
        console.print("[bold cyan]Enter choice to modify: [/bold cyan]", end="")
        
        try:
            choice = console.input().strip()
        except EOFError:
            return
        
        if choice == "1":
            try:
                console.print("\nEnter batch size (100-10000): ", end="")
                new_size = int(console.input().strip())
                if 100 <= new_size <= 10000:
                    SETTINGS["batch_size"] = new_size
            except (ValueError, EOFError):
                pass
        elif choice == "2":
            try:
                console.print("\nEnter delay in ms (0-100): ", end="")
                new_delay = int(console.input().strip())
                if 0 <= new_delay <= 100:
                    SETTINGS["batch_delay"] = new_delay / 1000
            except (ValueError, EOFError):
                pass
        elif choice == "3":
            SETTINGS["reduce_priority"] = not SETTINGS["reduce_priority"]
        elif choice == "4":
            SETTINGS["exclude_system_folders"] = not SETTINGS["exclude_system_folders"]
        elif choice == "5":
            console.print("\nEnter output folder path: ", end="")
            try:
                new_path = console.input().strip()
                if new_path:
                    SETTINGS["output_folder"] = new_path
            except EOFError:
                pass
        elif choice == "6":
            return
        else:
            console.print("\n[yellow]Invalid choice.[/yellow]")
            time.sleep(1)
        
        # Show updated message
        console.print("\n[green]Settings updated![/green]")
        time.sleep(0.5)


def index_path(paths, output_path, sort_by="path"):
    global last_result
    
    # Set low priority for system protection
    set_low_priority()
    
    files = []
    total_count = 0
    
    console.print(f"\n[yellow]Starting indexing...[/yellow]")
    console.print(f"Target: {', '.join(paths)}")
    
    # Check output location warning
    same_drive = check_output_location(paths)
    if same_drive:
        console.print(f"[yellow]Warning: Output will be saved to same drive ({same_drive}:) being indexed.[/yellow]")
        console.print(f"         This may cause additional disk I/O on that drive.")
    
    # Show memory warning
    mem_usage = get_memory_usage()
    if mem_usage > SETTINGS["max_memory_mb"]:
        console.print(f"[yellow]Warning: High memory usage detected ({mem_usage:.0f}MB).[/yellow]")
        console.print(f"         Consider closing other applications for better performance.")
    
    console.print()
    
    # Phase 1: Quick scan to count files
    console.print("[bold]Scanning files...[/bold]")
    
    from src.indexer import index_directory
    
    # Collect ALL files first for consistent results (no filtering during scan)
    all_files = []
    last_update_time = time_module.time()
    update_interval = 1.0  # Update every 1 second
    
    for path in paths:
        try:
            console.print(f"  Scanning: {path}")
            file_count = 0
            for metadata in index_directory(path):
                all_files.append(metadata)
                file_count += 1
                
                # Time-based update to console (every 1 second)
                current_time = time_module.time()
                if current_time - last_update_time >= update_interval:
                    console.print(f"    [cyan]Found {len(all_files):,} files...[/cyan]", end="\r")
                    last_update_time = current_time
        except Exception as e:
            console.print(f"[red]  Error scanning {path}: {e}[/red]")
    
    # Clear the "Found X files" line
    console.print(" " * 50, end="\r")
    
    # Now filter out system folders AFTER scanning is complete for consistent results
    if SETTINGS["exclude_system_folders"]:
        filtered_files = []
        skipped_system = 0
        for metadata in all_files:
            if check_system_folders(metadata.path):
                skipped_system += 1
            else:
                filtered_files.append(metadata)
        all_files = filtered_files
    else:
        skipped_system = 0
    
    if skipped_system > 0:
        console.print(f"[dim]Skipped {skipped_system:,} files in system folders[/dim]")
    
    total_files = len(all_files)
    if total_files == 0:
        console.print("[yellow]No files found to index.[/yellow]")
        try:
            console.input()
        except EOFError:
            pass
        return
    
    console.print(f"[green]Found {total_files:,} files to index[/green]\n")
    
    # Phase 2: Process files with progress bar and batch throttling
    batch_size = SETTINGS["batch_size"]
    batch_delay = SETTINGS["batch_delay"]
    
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
        
        # Process files with progress updates and batch throttling
        for i, metadata in enumerate(all_files, 1):
            files.append(metadata)
            
            # Batch throttling to prevent disk saturation
            if i % batch_size == 0:
                time.sleep(batch_delay)
                # Check memory and cleanup if needed
                if get_memory_usage() > SETTINGS["max_memory_mb"]:
                    gc.collect()
            
            # Update progress
            progress.update(task, advance=1, status=f"File {i:,}/{total_files:,}")
        
        progress.update(task, description="[green]Complete!", status="Done")
    
    # Clear memory
    del all_files
    gc.collect()
    
    console.print(f"\n[bold green]Indexing completed![/bold green]")
    console.print(f"Total files indexed: {len(files):,}")
    
    # Try to save with retry loop for duplicate filenames
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            from src.output import sort_files, create_index_result, save_with_duplicate_check
            console.print("[dim]Sorting results...[/dim]")
            sorted_files = sort_files(files, sort_by)
            result = create_index_result(sorted_files, paths)
            
            # Get base name from output path
            base_name = os.path.splitext(os.path.basename(output_path))[0]
            
            # Save files with duplicate check
            console.print("[dim]Saving files...[/dim]")
            saved_files = save_with_duplicate_check(result, base_name, indent=2, output_dir=SETTINGS["output_folder"])
            
            last_result = result
            
            console.print(f"[green]Main index saved to:[/green]")
            console.print(f"    {saved_files['index_file']}")
            console.print(f"[green]Directory structure saved to:[/green]")
            console.print(f"    {saved_files['structure_file']}")
            break
            
        except FileExistsError as e:
            if attempt < max_attempts - 1:
                console.print(f"[yellow]{e}[/yellow]")
                console.print("[yellow]Please enter a different filename: [/yellow]", end="")
                try:
                    new_name = console.input().strip()
                    if new_name:
                        # Update output_path with new name
                        output_path = new_name
                        if not output_path.endswith('.json'):
                            output_path += '.json'
                        continue  # Retry with new name
                except EOFError:
                    pass
            console.print(f"[red]Operation cancelled. File already exists.[/red]")
            break
        except Exception as e:
            console.print(f"[red]Error saving results: {e}[/red]")
            break
    
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
        console.print(f"  * {drive}")
    
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
        console.print(f"[cyan]{i}.[/cyan] {drive}")
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
    console.print("\n[bold cyan]LAST INDEXING RESULT[/bold cyan]")
    console.print("-" * 40)
    
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"[green]  Total files: {last_result.summary.total_files:,}[/green]")
    console.print(f"[green]  Total size: {format_size(last_result.summary.total_size)}[/green]")
    console.print(f"[green]  Indexed paths: {', '.join(last_result.summary.indexed_paths)}[/green]")
    console.print(f"[green]  Timestamp: {last_result.summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/green]")
    
    console.print("\n[bold]First 10 files:[/bold]")
    for i, f in enumerate(last_result.files[:10], 1):
        console.print(f"[cyan]{i}.[/cyan] {f.name}")
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
            show_settings()
        elif choice == '6':
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
