import argparse
import re
import sys
from pathlib import Path
from typing import Generator

import pandas as pd
import yaml


def walk_markdown_files(root_dir: Path) -> Generator[Path]:
    for dirpath, _, filenames in root_dir.walk():
        for filename in filenames:
            if filename.lower().endswith((".md", ".markdown")):
                yield Path(dirpath, filename)


def extract_title(md_text: str) -> str:
    # Use frontmatter YAML
    match = re.search(
        r"^---$(?P<yaml>.*?)^---$", md_text, flags=re.MULTILINE | re.DOTALL
    )

    if match:
        try:
            frontmatter = yaml.safe_load(match.group("yaml"))
        except yaml.YAMLError:
            # Skip frontmatter if YAML parse fails
            pass

        # Skip frontmatter if "title" key not present
        if "title" in frontmatter:
            return frontmatter["title"]

    # Use first L1 Markdown header
    match = re.search(r"^#\s+(?P<title>.*?)\s+$", md_text, flags=re.MULTILINE)

    if match:
        return match.group("title")

    return None


def make_dataframe(root_dir: Path) -> pd.DataFrame:

    paths = list(walk_markdown_files(root_dir))

    path_series = pd.Series(
        map(lambda p: str(p.relative_to(root_dir)), paths), dtype="string", name="Path"
    )
    title_series = pd.Series(
        map(lambda p: extract_title(p.read_text()), paths), dtype="string", name="Title"
    )

    # Red-Amber-Green assignment: default "R" at start of sprint
    rag_series = pd.Series("R", dtype="string", index=path_series.index, name="R-A-G")

    # Assignee: default empty at start of sprint
    assignee_series = pd.Series(
        pd.NA, dtype="string", index=path_series.index, name="Assignee"
    )

    return pd.concat(
        [path_series, title_series, rag_series, assignee_series], axis="columns"
    )


def main(root_dir: Path, output_csv: Path | None):

    df = make_dataframe(root_dir)

    if output_csv:
        print(f"Writing output CSV to {output_csv}")
    else:
        output_csv = sys.stdout

    df.to_csv(output_csv, index_label="Id")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root_dir",
        type=Path,
        help="Root directory to recursively search for Markdown documents",
    )
    parser.add_argument(
        "output_csv",
        type=Path,
        default=None,
        nargs="?",
        help="Optional path for output to CSV file (if not provided, output to stdout)",
    )
    args = parser.parse_args()

    main(args.root_dir, args.output_csv)
