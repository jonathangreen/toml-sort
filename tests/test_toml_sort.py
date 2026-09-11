"""Test the toml_sort module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest
import tomlkit

from toml_sort import TomlSort
from toml_sort.tomlsort import (
    CommentConfiguration,
    FormattingConfiguration,
    SortConfiguration,
    SortOverrideConfiguration,
    clean_toml_text,
)


def test_sort_toml_is_str() -> None:
    """Take a TOML string, sort it, and return the sorted string."""
    sorted_result = TomlSort("[hello]").sorted()
    assert isinstance(sorted_result, str)


@pytest.mark.parametrize(
    "unsorted_fixture,sorted_fixture,args",
    [
        (
            "gradle-version-catalog",
            "gradle-version-catalog",
            {
                "sort_config": SortConfiguration(
                    tables=False,
                ),
            },
        ),
        (
            "dotted-key",
            "dotted-key",
            {
                "sort_config": SortConfiguration(
                    inline_arrays=True, inline_tables=True
                ),
            },
        ),
        (
            "multiline-string",
            "multiline-string",
            {},
        ),
        (
            "utf8-bom",
            "utf8-bom",
            {},
        ),
        (
            "inline",
            "inline",
            {
                "sort_config": SortConfiguration(
                    inline_arrays=True, inline_tables=True
                ),
            },
        ),
        (
            "comment",
            "comment-comments-preserved",
            {"comment_config": CommentConfiguration(header=False, footer=False)},
        ),
        (
            "comment",
            "comment-no-comments",
            {
                "comment_config": CommentConfiguration(
                    header=False,
                    footer=False,
                    block=False,
                    inline=False,
                )
            },
        ),
        (
            "comment",
            "comment-header-footer",
            {
                "sort_config": SortConfiguration(table_keys=False),
                "format_config": FormattingConfiguration(
                    spaces_before_inline_comment=1
                ),
            },
        ),
        (
            "from-toml-lang",
            "from-toml-lang",
            {
                "sort_config": SortConfiguration(table_keys=False),
                "format_config": FormattingConfiguration(
                    spaces_before_inline_comment=1
                ),
            },
        ),
        (
            "from-toml-lang",
            "from-toml-lang-overrides",
            {
                "sort_config": SortConfiguration(
                    inline_arrays=True, inline_tables=True
                ),
                "format_config": FormattingConfiguration(
                    spaces_before_inline_comment=1
                ),
                "sort_config_overrides": {
                    "servers.beta": SortOverrideConfiguration(table_keys=False),
                    "clients.data": SortOverrideConfiguration(inline_arrays=False),
                },
            },
        ),
        (
            "from-toml-lang",
            "from-toml-lang-first",
            {
                "sort_config": SortConfiguration(
                    inline_arrays=True,
                    inline_tables=True,
                    first=["servers", "products"],
                ),
                "format_config": FormattingConfiguration(
                    spaces_before_inline_comment=1
                ),
                "sort_config_overrides": {
                    "database": SortOverrideConfiguration(first=["ports"]),
                    "owner": SortOverrideConfiguration(first=["name", "dob"]),
                    "inline.c": SortOverrideConfiguration(first=["version"]),
                },
            },
        ),
        (
            "pyproject-weird-order",
            "pyproject-weird-order",
            {
                "sort_config": SortConfiguration(table_keys=False),
                "comment_config": CommentConfiguration(block=False),
                "format_config": FormattingConfiguration(
                    spaces_before_inline_comment=1
                ),
            },
        ),
        pytest.param(
            "weird",
            "weird",
            {
                "sort_config": SortConfiguration(table_keys=False),
                "comment_config": CommentConfiguration(
                    block=False,
                ),
                "format_config": FormattingConfiguration(
                    spaces_before_inline_comment=1
                ),
            },
            marks=[pytest.mark.xfail],
        ),
        pytest.param(
            "single-comment",
            "../single-comment",  # Input is the same as the output
            {},
        ),
        pytest.param(
            "empty",
            "empty",
            {},
        ),
    ],
)
def test_tomlsort(
    get_fixture: Callable[[str | List[str]], Path],
    unsorted_fixture: str,
    sorted_fixture: str,
    args: Dict[str, Any],
) -> None:
    """Output of TomlSort.sorted() function matches expected."""
    path_unsorted = get_fixture(unsorted_fixture)
    path_sorted = get_fixture(["sorted", sorted_fixture])

    toml_unsorted_fixture = path_unsorted.read_text()
    toml_sorted_fixture = path_sorted.read_text()

    sort_output = TomlSort(toml_unsorted_fixture, **args).sorted()

    assert sort_output == toml_sorted_fixture
    assert TomlSort(sort_output, **args).sorted() == sort_output


@pytest.mark.parametrize("control", ["\x0c", "\x0b", "\x1f"])
def test_trailing_control_character_is_rejected(control: str) -> None:
    """Control characters at the end of the document reach the parser."""
    with pytest.raises(tomlkit.exceptions.TOMLKitError):
        TomlSort(f"a = 1  # comment{control}\n").sorted()
    with pytest.raises(tomlkit.exceptions.TOMLKitError):
        TomlSort(control).sorted()


def test_line_endings_trimmed_but_bare_cr_survives() -> None:
    """CRLF endings are trimmed like LF ones; a bare CR is left in place."""
    assert TomlSort("b = 1\r\n\r\na = 2\r\n").sorted() == "a = 2\nb = 1\n"
    assert clean_toml_text("a = 1\r\n\r\n") == "\na = 1\n"
    assert clean_toml_text("a = 1\r\n\r") == "\na = 1\r\n\r"
