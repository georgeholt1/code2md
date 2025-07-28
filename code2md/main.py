#!/usr/bin/env python3
"""
code2md - Convert code directory structure and contents to markdown

This tool recursively scans a directory and generates a markdown file
containing the directory structure and file contents.
"""

import argparse
import fnmatch
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml


class Code2MD:
    def __init__(self):
        self.include_files: Optional[List[str]] = None
        self.exclude_files: Set[str] = set()
        self.exclude_dirs: Set[str] = set()
        self.exclude_patterns: List[str] = []
        self.root_dir: Path = Path.cwd()
        self.output_file: str = "code2md_output.md"
        self.config_path: Path = None
        self.tree_only: bool = False

    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        self.config_path = config_path
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            return config
        except Exception as e:
            raise ValueError(f"Error loading config file '{config_path}': {str(e)}")

    def apply_config(self, config: Dict[str, Any]) -> None:
        """Apply configuration from loaded config dict."""
        if "directory" in config:
            self.root_dir = Path(config["directory"]).resolve()

        if "include_files" in config:
            include_files = config["include_files"]
            if isinstance(include_files, str):
                self.include_files = [
                    f.strip() for f in include_files.split(",") if f.strip()
                ]
            elif isinstance(include_files, list):
                self.include_files = include_files

        if "exclude_files" in config:
            exclude_files = config["exclude_files"]
            if isinstance(exclude_files, str):
                self.exclude_files = set(
                    f.strip() for f in exclude_files.split(",") if f.strip()
                )
            elif isinstance(exclude_files, list):
                self.exclude_files = set(exclude_files)

        if "exclude_dirs" in config:
            exclude_dirs = config["exclude_dirs"]
            if isinstance(exclude_dirs, str):
                self.exclude_dirs = set(
                    d.strip() for d in exclude_dirs.split(",") if d.strip()
                )
            elif isinstance(exclude_dirs, list):
                self.exclude_dirs = set(exclude_dirs)

        if "exclude_patterns" in config:
            exclude_patterns = config["exclude_patterns"]
            if isinstance(exclude_patterns, str):
                self.exclude_patterns = [
                    p.strip() for p in exclude_patterns.split(",") if p.strip()
                ]
            elif isinstance(exclude_patterns, list):
                self.exclude_patterns = exclude_patterns

        if "output" in config:
            self.output_file = config["output"]

        if "tree_only" in config:
            self.tree_only = config["tree_only"]

    def should_exclude_dir(self, dir_path: Path) -> bool:
        """Check if a directory should be excluded."""

        # Exclude hidden directories
        if dir_path.name.startswith("."):
            return True

        relative_path = str(dir_path.relative_to(self.root_dir))

        # Check if directory is in exclude list
        if relative_path in self.exclude_dirs or dir_path.name in self.exclude_dirs:
            return True

        # Check patterns
        for pattern in self.exclude_patterns:
            # Check both directory name and relative path
            if fnmatch.fnmatch(dir_path.name, pattern) or fnmatch.fnmatch(
                relative_path, pattern
            ):
                return True

            # Also check if any parent path matches the pattern
            if "/" in pattern:
                path_parts = relative_path.split("/")
                for i in range(len(path_parts)):
                    partial_path = "/".join(path_parts[: i + 1])
                    if fnmatch.fnmatch(partial_path, pattern):
                        return True

        return False

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on various criteria."""

        # Exclude hidden files
        if file_path.name.startswith("."):
            return True

        # Always exclude the output filename
        if file_path.name == self.output_file:
            return True

        # Always exclude config file
        if file_path.name == Path(self.config_path).name:
            return True

        rel_path_str = str(file_path.relative_to(self.root_dir))

        # Check if file is in exclude list
        if rel_path_str in self.exclude_files:
            return True

        # Check if file matches exclude patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True

            if fnmatch.fnmatch(rel_path_str, pattern):
                return True

            if "/" in pattern:
                if fnmatch.fnmatch(rel_path_str, pattern):
                    return True

        # If include_files is specified, only include those files
        if self.include_files is not None:
            return rel_path_str not in self.include_files

        return False

    def is_directory_needed_for_included_files(self, dir_path: Path) -> bool:
        """Check if a directory is needed to show path to included files."""
        if self.include_files is None:
            return True

        try:
            relative_dir_path = str(dir_path.relative_to(self.root_dir))
        except ValueError:
            # Path is not relative to root_dir
            return False

        # Check if any included file is within this directory or its subdirectories
        for file_path in self.include_files:
            # Convert included file path to Path object for proper comparison
            included_file_path = Path(file_path)

            # Get all parent directories of the included file
            file_parents = []
            current_parent = included_file_path.parent
            while str(current_parent) != ".":
                file_parents.append(str(current_parent))
                current_parent = current_parent.parent

            # Check if this directory is the root directory and file has parents
            if relative_dir_path == "" and (file_parents or "/" not in file_path):
                return True

            # Check if this directory matches any parent directory of the included file
            if relative_dir_path in file_parents:
                return True

            # Check if this directory exactly matches the file's direct parent
            if (
                relative_dir_path == str(included_file_path.parent)
                and str(included_file_path.parent) != "."
            ):
                return True

        return False

    def generate_tree_structure(
        self, path: Path, prefix: str = "", is_last: bool = True
    ) -> str:
        """Generate a tree-like directory structure string."""
        # Check exclusion first for non-root directories
        if path != self.root_dir:
            if path.is_dir():
                if self.include_files is not None:
                    if not self.is_directory_needed_for_included_files(path):
                        return ""
                elif self.should_exclude_dir(path):
                    return ""

        # Generate the current item's tree representation
        if path == self.root_dir:
            tree_str = f"{path.name}/\n"
        else:
            connector = "└── " if is_last else "├── "
            tree_str = f"{prefix}{connector}{path.name}{'/' if path.is_dir() else ''}\n"

        # Process directory contents
        if path.is_dir():
            try:
                all_entries = sorted(
                    path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())
                )

                entries = []
                # Filter entries
                for entry in all_entries:
                    if entry.is_dir():
                        # Check if directory is needed when include_files is specified
                        if self.include_files is not None:
                            if self.is_directory_needed_for_included_files(entry):
                                entries.append(entry)
                        elif not self.should_exclude_dir(entry):
                            entries.append(entry)
                    else:
                        if not self.should_exclude_file(entry):
                            entries.append(entry)

                # Generate tree for filtered entries
                for i, entry in enumerate(entries):
                    is_last_entry = i == len(entries) - 1

                    if path == self.root_dir:
                        new_prefix = ""
                    else:
                        new_prefix = prefix + ("    " if is_last else "│   ")

                    subtree = self.generate_tree_structure(
                        entry, new_prefix, is_last_entry
                    )
                    tree_str += subtree

            except PermissionError:
                pass

        return tree_str

    def collect_files(self, path: Path) -> List[Path]:
        """Recursively collect all files that should be included."""
        files = []

        if path.is_file():
            if not self.should_exclude_file(path):
                files.append(path)
        elif path.is_dir():
            if not self.should_exclude_dir(path):
                try:
                    for entry in sorted(path.iterdir(), key=lambda x: x.name.lower()):
                        files.extend(self.collect_files(entry))
                except PermissionError:
                    pass

        return files

    def read_file_content(self, file_path: Path) -> str:
        """Read file content, handling binary files gracefully."""
        try:
            # Try to read as text first
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # If it's a binary file, indicate that
            return "[Binary file - content not displayed]"
        except Exception as e:
            return f"[Error reading file: {str(e)}]"

    def generate_markdown(self) -> str:
        """Generate the complete markdown output."""
        # Generate tree structure
        tree_structure = self.generate_tree_structure(self.root_dir)

        # Start building markdown
        markdown_content = "Following is a directory tree"
        if not self.tree_only:
            markdown_content += " and file contents"
        markdown_content += ".\n\n"

        markdown_content += "```\n"
        markdown_content += tree_structure
        markdown_content += "```\n\n"

        # Add file contents only if not tree-only mode
        if not self.tree_only:
            # Collect all files
            all_files = self.collect_files(self.root_dir)

            for file_path in all_files:
                relative_path = file_path.relative_to(self.root_dir)
                content = self.read_file_content(file_path)

                markdown_content += f"{relative_path}\n"
                markdown_content += "```\n"
                markdown_content += content
                markdown_content += "\n```\n\n"

        return markdown_content

    def run(self) -> None:
        """Execute the code2md conversion."""
        try:
            markdown_content = self.generate_markdown()

            # Write output file
            output_path = self.root_dir / self.output_file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            print(f"Successfully generated {output_path}")

        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            return 1

        return 0


def parse_list_argument(value: str) -> List[str]:
    """Parse comma-separated list argument."""
    return [item.strip() for item in value.split(",") if item.strip()]


def main():
    """Main entry point for the command line tool."""
    parser = argparse.ArgumentParser(
        description="Convert code directory structure and contents to markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  code2md                                    # Process current directory
  code2md /path/to/project                   # Process specific directory
  code2md --config config.yaml              # Use YAML config file
  code2md --tree-only                       # Generate only directory tree
  code2md --include-files "main.py,utils.py" # Include only specific files
  code2md --exclude-files "config.py"       # Exclude specific files
  code2md --exclude-dirs "__pycache__,.git" # Exclude directories
  code2md --exclude-patterns "*.log,*_test_*" # Exclude file patterns
  code2md --output my_project.md             # Custom output filename

Config file format (YAML):
  directory: "/path/to/project"              # Optional: directory to process
  tree_only: true                            # Optional: generate only tree structure
  include_files:                             # Optional: files to include (list or comma-separated string)
    - "main.py"
    - "utils.py"
  exclude_files:                             # Optional: files to exclude (list or comma-separated string)
    - "config.py"
  exclude_dirs:                              # Optional: directories to exclude (list or comma-separated string)
    - "__pycache__"
    - ".git"
  exclude_patterns:                          # Optional: patterns to exclude (list or comma-separated string)
    - "*.log"
    - "*_test_*"
  output: "my_project.md"                    # Optional: output filename
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Top-level directory to process (default: current directory)",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML config file (overridden by command line options)",
    )

    parser.add_argument(
        "--include-files",
        type=parse_list_argument,
        help="Comma-separated list of files to include (excludes all others)",
    )

    parser.add_argument(
        "--exclude-files",
        type=parse_list_argument,
        default=[],
        help="Comma-separated list of files to exclude",
    )

    parser.add_argument(
        "--exclude-dirs",
        type=parse_list_argument,
        default=[],
        help="Comma-separated list of directories to exclude",
    )

    parser.add_argument(
        "--exclude-patterns",
        type=parse_list_argument,
        default=[],
        help='Comma-separated list of file patterns to exclude (e.g., "*.log,*_test_*")',
    )

    parser.add_argument(
        "--tree-only",
        action="store_true",
        help="Generate only the directory tree structure (no file contents)",
    )

    parser.add_argument(
        "--output",
        default="code2md_output.md",
        help="Output filename (default: code2md_output.md)",
    )

    args = parser.parse_args()

    # Initialize code2md instance
    code2md = Code2MD()

    # Load config file if specified
    if args.config:
        try:
            config_path = Path(args.config)
            if not config_path.exists():
                print(
                    f"Error: Config file '{args.config}' does not exist",
                    file=sys.stderr,
                )
                return 1

            config = code2md.load_config(config_path)
            code2md.apply_config(config)

        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            return 1

    # Apply command line arguments (these override config file settings)
    if args.directory != ".":
        code2md.root_dir = Path(args.directory).resolve()
    elif not hasattr(code2md, "root_dir") or code2md.root_dir == Path.cwd():
        code2md.root_dir = Path(args.directory).resolve()

    if args.include_files is not None:
        code2md.include_files = args.include_files
    if args.exclude_files:
        code2md.exclude_files.update(args.exclude_files)
    if args.exclude_dirs:
        code2md.exclude_dirs.update(args.exclude_dirs)
    if args.exclude_patterns:
        code2md.exclude_patterns.extend(args.exclude_patterns)
    if args.output != "code2md_output.md":
        code2md.output_file = args.output
    if args.tree_only:
        code2md.tree_only = True

    # Validate directory
    if not code2md.root_dir.exists():
        print(f"Error: Directory '{args.directory}' does not exist", file=sys.stderr)
        return 1

    if not code2md.root_dir.is_dir():
        print(f"Error: '{args.directory}' is not a directory", file=sys.stderr)
        return 1

    # Run the conversion
    return code2md.run()


if __name__ == "__main__":
    sys.exit(main())
