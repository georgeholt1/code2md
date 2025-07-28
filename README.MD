# code2md

Convert code directory structure and contents to markdown format.

## Installation

```bash
pip install .
```

Or for development:

```bash
pre-commit install
pip install -e ".[dev]"
```

## Usage

After installation, you can use `code2md` from the command line:

```bash
# Process current directory
code2md

# Process specific directory
code2md /path/to/project

# Include only specific files
code2md --include-files "main.py,utils.py"

# Exclude specific files
code2md --exclude-files "config.py,secrets.txt"

# Exclude directories
code2md --exclude-dirs "__pycache__,.git,node_modules"

# Exclude file patterns
code2md --exclude-patterns "*.log,*_test_*,*.pyc"

# Custom output filename
code2md --output my_project.md

# Combine multiple options
code2md /path/to/project --exclude-dirs ".git,__pycache__" --exclude-patterns "*.log" --output project_overview.md
```

## Output Format

code2md generates a markdown file with:

1. A tree-style directory structure
2. Contents of each file in code blocks
