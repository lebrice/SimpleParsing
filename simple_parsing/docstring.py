"""Utility for retrieveing the docstring of a dataclass's attributes
@author: Fabrice Normandin
"""
from __future__ import annotations

import ast
import functools
import inspect
import tokenize
from dataclasses import dataclass
from functools import partial
from logging import getLogger
from textwrap import dedent

import docstring_parser as dp
from docstring_parser.common import Docstring
from typing_extensions import Literal

from simple_parsing.utils import Dataclass

logger = getLogger(__name__)


@dataclass
class AttributeDocString:
    """Simple dataclass for holding the comments of a given field."""

    comment_above: str = ""
    comment_inline: str = ""
    docstring_below: str = ""

    desc_from_cls_docstring: str = ""
    """ The description of this field from the class docstring. """

    @property
    def help_string(self) -> str:
        """Returns the value that will be used for the "--help" string, using the contents of self."""
        return (
            self.docstring_below
            or self.comment_above
            or self.comment_inline
            or self.desc_from_cls_docstring
        )


def get_attribute_docstring(
    dataclass: type, field_name: str, accumulate_from_bases: bool = True
) -> AttributeDocString:
    """Returns the docstrings of a dataclass field.
    NOTE: a docstring can either be:
    - An inline comment, starting with <#>
    - A Comment on the preceding line, starting with <#>
    - A docstring on the following line, starting with either <\"\"\"> or <'''>
    - The description of a field in the classes's docstring.

    Arguments:
        some_dataclass: a dataclass
        field_name: the name of the field.
        accumulate_from_bases: Whether to accumulate the docstring components by looking through the
            base classes. When set to `False`, whenever one of the classes has a definition for the
            field, it is directly returned. Otherwise, we accumulate the parts of the dodc
    Returns:
        AttributeDocString -- an object holding the string descriptions of the field.
    """
    created_docstring: AttributeDocString | None = None

    mro = inspect.getmro(dataclass)
    assert mro[0] is dataclass
    assert mro[-1] is object
    mro = mro[:-1]
    for base_class in mro:
        attribute_docstring = _get_attribute_docstring(base_class, field_name)
        if not attribute_docstring:
            continue
        if not created_docstring:
            created_docstring = attribute_docstring
            if not accumulate_from_bases:
                # We found a definition for that field in that class, so return it directly.
                return created_docstring
        else:
            # Update the fields.
            created_docstring.comment_above = (
                created_docstring.comment_above or attribute_docstring.comment_above
            )
            created_docstring.comment_inline = (
                created_docstring.comment_inline or attribute_docstring.comment_inline
            )
            created_docstring.docstring_below = (
                created_docstring.docstring_below or attribute_docstring.docstring_below
            )
            created_docstring.desc_from_cls_docstring = (
                created_docstring.desc_from_cls_docstring
                or attribute_docstring.desc_from_cls_docstring
            )
    if not created_docstring:
        logger.debug(
            RuntimeWarning(
                f"Couldn't find the definition for field '{field_name}' within the dataclass "
                f"{dataclass} or any of its base classes {','.join(t.__name__ for t in mro[1:])}."
            )
        )
        return AttributeDocString()
    return created_docstring


@functools.lru_cache(2048)
def _get_attribute_docstring(dataclass: type, field_name: str) -> AttributeDocString | None:
    """Gets the AttributeDocString of the given field in the given dataclass.
    Doesn't inspect base classes.
    """
    # Parse docstring to use as help strings
    desc_from_cls_docstring = ""
    cls_docstring = inspect.getdoc(dataclass)
    if cls_docstring:
        docstring: Docstring = dp.parse(cls_docstring)
        for param in docstring.params:
            if param.arg_name == field_name:
                desc_from_cls_docstring = param.description or ""

    results = get_attribute_docstrings(dataclass).get(field_name, None)
    if results:
        results.desc_from_cls_docstring = desc_from_cls_docstring
        return results
    else:
        return None


def scrape_comments(src: str) -> list[tuple[int, int, Literal["COMMENT"], str]]:
    lines = bytes(src, encoding="utf8").splitlines(keepends=True)
    return [
        (*tok.start, "COMMENT", tok.string[1:].strip())
        for tok in tokenize.tokenize(partial(next, iter(lines)))
        if tok.type == tokenize.COMMENT
    ]


class AttributeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.data: list[tuple[int, int, Literal["DOC", "VARIABLE", "OTHER"], str | None]] = []
        self.prefix = None

    def add_data(
        self, node: ast.AST, kind: Literal["DOC", "VARIABLE", "OTHER"], content: str | None
    ):
        self.data.append((node.lineno, node.col_offset, kind, content))

    def visit_body(self, name: str, stmts: list[ast.stmt]):
        old_prefix = self.prefix
        if self.prefix is None:
            self.prefix = ""
        else:
            self.prefix += f"{name}."
        for stmt in stmts:
            if (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            ):
                self.add_data(stmt, "DOC", stmt.value.value)
            else:
                self.visit(stmt)
        self.prefix = old_prefix

    def visit_ClassDef(self, node: ast.ClassDef):
        if self.prefix is not None:
            self.add_data(node, "VARIABLE", f"{self.prefix}{node.name}")
        self.visit_body(node.name, node.body)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.prefix is not None:
            self.add_data(node, "VARIABLE", f"{self.prefix}{node.name}")
        self.visit_body(node.name, node.body)

    def visit_Assign(self, node: ast.Assign):
        self.generic_visit(node, may_assign=True)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.generic_visit(node, may_assign=True)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.add_data(node, "VARIABLE", f"{self.prefix}{node.id}")

    def generic_visit(self, node: ast.AST, may_assign: bool = False):
        if isinstance(node, ast.stmt) and not may_assign:
            self.add_data(node, "OTHER", None)
        super().generic_visit(node)


def scrape_docstrings(src: str):
    visitor = AttributeVisitor()
    visitor.visit(ast.parse(src))
    return visitor.data


def get_attribute_docstrings(cls: type[Dataclass]) -> dict[str, AttributeDocString]:
    docs: dict[str, AttributeDocString] = {}
    current: str | None = None
    current_line: int | None = None
    comments_above = []
    try:
        indented_src = inspect.getsource(cls)
    except (TypeError, OSError) as e:
        logger.debug(
            UserWarning(
                f"Couldn't retrieve the source code of class {cls} "
                f"(in order to retrieve the docstrings of its fields): {e}"
            )
        )
        return {}
    src = dedent(indented_src)
    data = scrape_comments(src) + scrape_docstrings(src)
    for line, _, kind, content in sorted(data):
        if kind == "COMMENT":
            assert content is not None
            if current is not None and current_line == line:
                docs[current].comment_inline = content.strip()
            else:
                comments_above.append(content)
        elif kind == "DOC" and current:
            assert content is not None
            content_lines = content.splitlines()
            if len(content_lines) > 1:
                docs[current].docstring_below = (
                    dedent(content_lines[0]) + "\n" + dedent("\n".join(content_lines[1:]))
                )
            else:
                docs[current].docstring_below = dedent(content.strip())

        elif kind == "VARIABLE":
            assert content is not None
            docs[content] = AttributeDocString(comment_above=dedent("\n".join(comments_above)))
            comments_above = []
            current = content
            current_line = line
        elif kind == "OTHER":
            current = current_line = None
            comments_above = []
    return docs
