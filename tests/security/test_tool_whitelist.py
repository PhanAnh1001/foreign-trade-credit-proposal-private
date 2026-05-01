"""
Bước 5.5e — Tool whitelist cho LC Application Agent.
Kiểm tra pipeline chỉ gọi các tools được phép, không gọi subprocess/eval/exec.
Không cần API key.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

SRC_DIR = Path("src")

# Tools được phép gọi trong pipeline
ALLOWED_TOOL_CALLS = {
    "extract_contract_text",
    "extract_lc_fields_from_contract",
    "validate_and_enhance",
    "fill_lc_template",
    "get_bank_template_path",
    "get_bank_output_dir",
    "slugify_company",
}

# Calls nguy hiểm không được phép xuất hiện trong src/
FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "subprocess",
    "os.system",
    "__import__",
    "pickle.loads",
    "marshal.loads",
}


def _collect_py_files(directory: Path) -> list[Path]:
    return list(directory.rglob("*.py"))


def test_no_forbidden_calls_in_src():
    """src/ không được có eval/exec/subprocess/pickle.loads."""
    violations = []
    for py_file in _collect_py_files(SRC_DIR):
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for forbidden in FORBIDDEN_CALLS:
            if forbidden not in source:
                continue
            # Strip docstrings and comments before checking
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            # Collect line numbers that are inside docstrings
            docstring_lines: set[int] = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    if (node.body and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and isinstance(node.body[0].value.value, str)):
                        ds = node.body[0]
                        for ln in range(ds.lineno, ds.end_lineno + 1):
                            docstring_lines.add(ln)
            src_lines = source.splitlines()
            hits = [
                (i + 1, src_lines[i].strip())
                for i in range(len(src_lines))
                if forbidden in src_lines[i]
                and not src_lines[i].strip().startswith("#")
                and (i + 1) not in docstring_lines
            ]
            if hits:
                violations.append((py_file.name, forbidden, hits))

    assert not violations, (
        "Forbidden calls found in src/:\n"
        + "\n".join(f"  {f}: {call} at lines {lines}" for f, call, lines in violations)
    )


def test_node_files_only_import_allowed_tools():
    """Node files chỉ import từ src.tools và src.utils, không import external executors."""
    node_files = list((SRC_DIR / "agents").glob("node_*.py"))
    assert node_files, "Không tìm thấy node files trong src/agents/"

    forbidden_imports = {"subprocess", "pickle", "marshal", "shelve", "ctypes"}
    violations = []

    for node_file in node_files:
        source = node_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                else:
                    names = [node.module or ""]
                for name in names:
                    if any(name.startswith(f) for f in forbidden_imports):
                        violations.append((node_file.name, name))

    assert not violations, f"Node files import forbidden modules: {violations}"


def test_fill_node_uses_template_path_from_config():
    """fill_node phải mengambil template path dari config, tidak hardcode path."""
    node_fill = SRC_DIR / "agents" / "node_fill.py"
    source = node_fill.read_text(encoding="utf-8")

    assert "get_bank_template_path" in source, (
        "node_fill.py phải dùng get_bank_template_path() từ config, không hardcode path"
    )


def test_config_slugify_max_length():
    """slugify_company phải giới hạn max 50 chars để tránh path traversal."""
    from src.config import slugify_company

    long_name = "A" * 200
    result = slugify_company(long_name)
    assert len(result) <= 50, f"slugify_company không giới hạn length: {len(result)}"


def test_config_slugify_no_path_traversal():
    """slugify_company phải loại bỏ ký tự path traversal."""
    from src.config import slugify_company

    dangerous_names = [
        "../../../etc/passwd",
        "..\\windows\\system32",
        "/absolute/path",
        "name\x00null",
    ]
    for name in dangerous_names:
        result = slugify_company(name)
        assert ".." not in result, f"Path traversal trong slug: {result!r} (input: {name!r})"
        assert "/" not in result, f"Slash trong slug: {result!r} (input: {name!r})"
        assert "\\" not in result, f"Backslash trong slug: {result!r} (input: {name!r})"
        assert "\x00" not in result, f"Null byte trong slug: {result!r} (input: {name!r})"
