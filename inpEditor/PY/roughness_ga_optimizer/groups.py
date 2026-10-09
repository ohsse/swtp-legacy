from __future__ import annotations

from pathlib import Path

import pandas as pd


def year_to_group(year: int) -> str:
    """Return a coarse install-year group name."""

    if year >= 2020:
        return "Y2020_AFTER"
    if year >= 2010:
        return "Y2010_2019"
    if year >= 2000:
        return "Y2000_2009"
    return "Y_BEFORE_2000"


def load_year_groups(csv_path: str) -> dict[str, list[str]]:
    """
    Load groups from a CSV file.

    Required column:
        pipe_id

    Optional columns:
        install_year
        year_group
    """

    df = pd.read_csv(csv_path, dtype={"pipe_id": str})
    if "pipe_id" not in df.columns:
        raise ValueError("pipe_year_csv must include a pipe_id column.")

    if "year_group" not in df.columns:
        if "install_year" not in df.columns:
            raise ValueError("pipe_year_csv must include year_group or install_year.")
        df["year_group"] = df["install_year"].astype(int).apply(year_to_group)

    groups: dict[str, list[str]] = {}
    for row in df.itertuples(index=False):
        pipe_id = str(getattr(row, "pipe_id")).strip()
        group_name = str(getattr(row, "year_group")).strip()
        if pipe_id and group_name:
            groups.setdefault(group_name, []).append(pipe_id)

    return groups


def load_inp_tag_groups(inp_path: str) -> dict[str, list[str]]:
    """
    Load roughness groups from the INP [TAGS] section.

    Expected rows:
        LINK  pipe_id  group_name

    Example:
        LINK  2013065389  D
    """

    text = _read_inp_text(inp_path)
    lines = text.splitlines()

    in_tags = False
    groups: dict[str, list[str]] = {}
    seen_pipe_ids: set[str] = set()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            in_tags = line.upper() == "[TAGS]"
            continue

        if not in_tags or line.startswith(";"):
            continue

        parts = line.split()
        if len(parts) < 3:
            continue

        object_type, pipe_id, group_name = parts[0].upper(), parts[1], parts[2]
        if object_type != "LINK":
            continue

        if pipe_id in seen_pipe_ids:
            raise ValueError(f"Duplicate pipe tag found in [TAGS]: {pipe_id}")

        seen_pipe_ids.add(pipe_id)
        groups.setdefault(group_name, []).append(pipe_id)

    if not groups:
        raise ValueError(f"No LINK group tags found in INP [TAGS]: {inp_path}")

    return groups


def _read_inp_text(inp_path: str) -> str:
    data = Path(inp_path).read_bytes()
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")
