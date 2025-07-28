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

# Generate only directory tree (no file contents)
code2md --tree-only

# Use YAML config file
code2md --config config.yaml

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

# Generate tree-only overview of a large project
code2md /path/to/large/project --tree-only --output project_structure.md

# Config file with command line overrides
code2md --config myproject.yaml --output different_name.md
```

## Configuration File

You can use a YAML configuration file to specify all options.

Create a `config.yaml` file:

```yaml
# Directory to process (optional, defaults to current directory)
directory: "/path/to/my/project"

# Generate only tree structure without file contents (optional, defaults to false)
tree_only: true

# Files to include (optional, list or comma-separated string)
# If specified, only these files will be included
include_files:
  - "main.py"
  - "utils.py"
  - "config.py"

# Files to exclude (optional, list or comma-separated string)
exclude_files:
  - "secrets.txt"
  - "local_config.py"

# Directories to exclude (optional, list or comma-separated string)
exclude_dirs:
  - "__pycache__"
  - ".git"
  - "node_modules"
  - ".venv"

# File patterns to exclude (optional, list or comma-separated string)
exclude_patterns:
  - "*.log"
  - "*.tmp"
  - "*_test_*"
  - "*.pyc"

# Output filename (optional, defaults to code2md_output.md)
output: "output.md"
```

Alternative format using comma-separated strings:

```yaml
directory: "/path/to/my/project"
tree_only: false
include_files: "main.py,utils.py,config.py"
exclude_files: "secrets.txt,local_config.py"
exclude_dirs: "__pycache__,.git,node_modules,.venv"
exclude_patterns: "*.log,*.tmp,*_test_*,*.pyc"
output: "my_project_documentation.md"
```

Then run:

```bash
code2md --config config.yaml
```

### Configuration Priority

Command line arguments override config file settings:

```bash
# Use config file but override output filename
code2md --config config.yaml --output different_name.md

# Use config file but generate tree-only instead of full content
code2md --config config.yaml --tree-only

# Use config file but add additional exclusions
code2md --config config.yaml --exclude-patterns "*.backup"
```

## Output Format

code2md generates a markdown file with:

1. A tree-style directory structure
2. Contents of each file in code blocks (unless `--tree-only` is used)
