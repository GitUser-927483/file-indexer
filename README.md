# File Indexer

A powerful file indexing tool that creates searchable JSON databases of file systems.

## Features

- **CLI Interface**: Modern, user-friendly text-based menu with progress bars
- **File Indexing**: Recursively indexes directories and drives with metadata
- **JSON Output**: Saves indexed data in structured JSON format
- **Directory Structure**: Shows complete directory tree of indexed locations
- **Progress Tracking**: Real-time progress bars with file count updates
- **Error Handling**: Safe operations with duplicate file protection

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/file-indexer.git
   cd file_indexer
   ```

2. Install dependencies:
   ```bash
   pip install rich tqdm
   ```

## Usage

### Basic Usage

Run the file indexer:
```bash
python gui.py
```

### Menu Options

1. **Index specific directory** - Index a single folder
2. **Index all drives** - Index all available drives (Windows)
3. **Index a specific drive** - Index a single drive
4. **View last result** - View previous indexing results
5. **Exit** - Exit the program

### CLI Usage

For command-line usage:
```bash
python main.py --help
```

## File Output

Indexed files are saved in the `file_indexer/output/` directory:
- `index.json` - Full indexed data with metadata
- `directory_structure.json` - Directory tree structure

## Configuration

The tool uses the following configuration:
- **Output Directory**: `file_indexer/output/`
- **File Format**: JSON with structured metadata
- **Duplicate Protection**: Warns if file exists, doesn't overwrite

## Development

### Requirements
- Python 3.7+
- rich (for CLI UI)
- tqdm (for progress bars)

### Project Structure
```
file_indexer/
├── gui.py              # CLI interface with rich UI
├── main.py             # Main CLI entry point
├── cli.py              # CLI argument parser
├── indexer.bat         # GUI launcher (now CLI)
├── indexer-cli.bat     # CLI launcher
├── output/             # Output directory for JSON files
├── src/
│   ├── indexer.py      # Core indexing logic
│   ├── metadata.py     # File metadata extraction
│   ├── output.py       # Output generation
│   └── models.py       # Data models
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions, please open an issue on the GitHub repository.