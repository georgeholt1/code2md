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
from typing import List, Optional, Set


class Code2MD:
    def __init__(self):
        self.include_files: Optional[List[str]] = None
        self.exclude_files: Set[str] = set()
        self.exclude_dirs: Set[str] = set()
        self.exclude_patterns: List[str] = []
        self.root_dir: Path = Path.cwd()
        self.output_file: str = "code2md_output.md"

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

    def generate_tree_structure(
        self, path: Path, prefix: str = "", is_last: bool = True
    ) -> str:
        """Generate a tree-like directory structure string."""
        if path == self.root_dir:
            tree_str = f"{path.name}/\n"
            entries = []
        else:
            connector = "└── " if is_last else "├── "
            tree_str = f"{prefix}{connector}{path.name}{'/' if path.is_dir() else ''}\n"
            entries = []

        if path.is_dir() and not self.should_exclude_dir(path):
            try:
                all_entries = sorted(
                    path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())
                )

                # Filter entries
                for entry in all_entries:
                    if entry.is_dir():
                        if not self.should_exclude_dir(entry):
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

                    tree_str += self.generate_tree_structure(
                        entry, new_prefix, is_last_entry
                    )

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

        # Collect all files
        all_files = self.collect_files(self.root_dir)

        # Start building markdown
        markdown_content = "Following is a directory tree and file contents.\n\n"
        markdown_content += "```\n"
        markdown_content += tree_structure
        markdown_content += "```\n\n"

        # Add file contents
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
  code2md --include-files "main.py,utils.py" # Include only specific files
  code2md --exclude-files "config.py"       # Exclude specific files
  code2md --exclude-dirs "__pycache__,.git" # Exclude directories
  code2md --exclude-patterns "*.log,*_test_*" # Exclude file patterns
  code2md --output my_project.md             # Custom output filename
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Top-level directory to process (default: current directory)",
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
        "--output",
        default="code2md_output.md",
        help="Output filename (default: code2md_output.md)",
    )

    args = parser.parse_args()

    # Initialize code2md instance
    code2md = Code2MD()

    # Set configuration
    code2md.root_dir = Path(args.directory).resolve()
    code2md.include_files = args.include_files
    code2md.exclude_files = set(args.exclude_files)
    code2md.exclude_dirs = set(args.exclude_dirs)
    code2md.exclude_patterns = args.exclude_patterns
    code2md.output_file = args.output

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
