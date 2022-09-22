"""Utility for retrieveing the docstring of a dataclass's attributes
@author: Fabrice Normandin
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class AttributeDocString:
    """Simple dataclass for holding the comments of a given field."""

    comment_above: str = ""
    comment_inline: str = ""
    docstring_below: str = ""


def get_attribute_docstring(
    dataclass: type, field_name: str, accumulate_from_bases: bool = True
) -> AttributeDocString:
    """Returns the docstrings of a dataclass field.
    NOTE: a docstring can either be:
    - An inline comment, starting with <#>
    - A Comment on the preceding line, starting with <#>
    - A docstring on the following line, starting with either <\"\"\"> or <'''>

    Arguments:
        some_dataclass: a dataclass
        field_name: the name of the field.
        accumulate_from_bases: Whether to accumulate the docstring components by looking through the
            base classes. When set to `False`, whenever one of the classes has a definition for the
            field, it is directly returned. Otherwise, we accumulate the parts of the dodc
    Returns:
        AttributeDocString -- an object holding the three possible comments
    """
    created_docstring: AttributeDocString | None = None

    mro = inspect.getmro(dataclass)
    assert mro[0] is dataclass
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
    if not created_docstring:
        raise RuntimeError(
            f"Couldn't find the definition for field '{field_name}' within the dataclass "
            f"{dataclass} or any of its base classes {','.join(map(str, mro[1:]))}."
        )
    return created_docstring


def _get_attribute_docstring(some_dataclass: type, field_name: str) -> AttributeDocString | None:
    """Gets the AttributeDocString of the given field in the given dataclass.
    Doesn't inspect base classes.
    """
    try:
        source = inspect.getsource(some_dataclass)
    except (TypeError, OSError) as e:
        logger.debug(
            UserWarning(
                f"Couldn't retrieve the source code of class {some_dataclass} "
                f"(in order to retrieve the docstring of field {field_name}): {e}"
            )
        )
        return None
    # NOTE: We want to skip the docstring lines.
    # NOTE: Currently, we just remove the __doc__ from the source. It's perhaps a bit crude,
    # but it works.
    if some_dataclass.__doc__ and some_dataclass.__doc__ in source:
        source = source.replace(some_dataclass.__doc__, "", 1)

    code_lines: list[str] = source.splitlines()
    # the first line is the class definition, we skip it.
    start_line_index = 1
    # starting at the second line, there might be the docstring for the class.
    # We want to skip over that until we reach an attribute definition.
    while start_line_index < len(code_lines):
        if _contains_field_definition(code_lines[start_line_index]):
            break
        start_line_index += 1
    # body_lines = code_lines[start_line_index:]

    lines_with_attribute_defs = [
        (index, line) for index, line in enumerate(code_lines) if _contains_field_definition(line)
    ]

    for i, line in lines_with_attribute_defs:
        parts: list[str] = line.split(":", maxsplit=1)
        if parts[0].strip() == field_name:
            # we found the line with the definition of this field.
            comment_above = _get_comment_ending_at_line(code_lines, i - 1)
            comment_inline = _get_inline_comment_at_line(code_lines, i)
            docstring_below = _get_docstring_starting_at_line(code_lines, i + 1)
            complete_docstring = AttributeDocString(comment_above, comment_inline, docstring_below)
            return complete_docstring
    return None


def _contains_field_definition(line: str) -> bool:
    """Returns whether or not a line contains a an dataclass field definition.

    Arguments:
        line_str {str} -- the line content

    Returns:
        bool -- True if there is an attribute definition in the line.

    >>> _contains_field_definition("a: int = 0")
    True
    >>> _contains_field_definition("a: int")
    True
    >>> _contains_field_definition("a: int # comment")
    True
    >>> _contains_field_definition("a: int = 0 # comment")
    True
    >>> _contains_field_definition("class FooBaz(Foo, Baz):")
    False
    >>> _contains_field_definition("a = 4")
    False
    >>> _contains_field_definition("fooooooooobar.append(123)")
    False
    >>> _contains_field_definition("{a: int}")
    False
    >>> _contains_field_definition("        foobaz: int = 123  #: The foobaz property")
    True
    >>> _contains_field_definition("a #:= 3")
    False
    """
    # Get rid of any comments first.
    line, _, _ = line.partition("#")

    if ":" not in line:
        return False

    if "=" in line:
        attribute_and_type, _, _ = line.partition("=")
    else:
        attribute_and_type = line

    field_name, _, type = attribute_and_type.partition(":")
    field_name = field_name.strip()
    if ":" in type:
        # weird annotation or dictionary?
        return False
    if not field_name:
        # Empty attribute name?
        return False
    return field_name.isidentifier()


def _line_contains_definition_for(line: str, field_name: str) -> bool:
    if not _contains_field_definition(line):
        return False
    line = line.strip()
    attribute, _, type_and_value_assignment = line.partition(":")
    return attribute.isidentifier() and attribute == field_name


def _is_empty(line_str: str) -> bool:
    return line_str.strip() == ""


def _is_comment(line_str: str) -> bool:
    return line_str.strip().startswith("#")


def _get_comment_at_line(code_lines: list[str], line: int) -> str:
    """Gets the comment at line `line` in `code_lines`.

    Arguments:
        line {int} -- the index of the line in code_lines

    Returns:
        str -- the comment at the given line. empty string if not present.
    """
    line_str = code_lines[line]
    assert not _contains_field_definition(line_str)
    if "#" not in line_str:
        return ""
    parts = line_str.split("#", maxsplit=1)
    comment = parts[1].strip()
    return comment


def _get_inline_comment_at_line(code_lines: list[str], line: int) -> str:
    """Gets the inline comment at line `line`.

    Arguments:
        line {int} -- the index of the line in code_lines

    Returns:
        str -- the inline comment at the given line, else an empty string.
    """
    assert 0 <= line < len(code_lines)
    assert _contains_field_definition(code_lines[line])
    line_str = code_lines[line]
    parts = line_str.split("#", maxsplit=1)
    if len(parts) != 2:
        return ""
    comment = parts[1].strip()
    return comment


def _get_comment_ending_at_line(code_lines: list[str], line: int) -> str:
    start_line = line
    end_line = line
    # move up the code, one line at a time, while we don't hit the start,
    # an attribute definition, or the end of a docstring.
    while start_line > 0:
        line_str = code_lines[start_line]
        if _contains_field_definition(line_str):
            break  # previous line is an assignment
        if '"""' in line_str or "'''" in line_str:
            break  # previous line has a docstring
        start_line -= 1
    start_line += 1

    lines = []
    for i in range(start_line, end_line + 1):
        # print(f"line {i}: {code_lines[i]}")
        if _is_empty(code_lines[i]):
            continue
        assert not _contains_field_definition(code_lines[i])
        comment = _get_comment_at_line(code_lines, i)
        lines.append(comment)
    return "\n".join(lines).strip()


def _get_docstring_starting_at_line(code_lines: list[str], line: int) -> str:
    i = line
    token: str | None = None
    triple_single = "'''"
    triple_double = '"""'
    # print("finding docstring starting from line", line)

    # if we are looking further down than the end of the code, there is no
    # docstring.
    if line >= len(code_lines):
        return ""
    # the list of lines making up the docstring.
    docstring_contents: list[str] = []

    while i < len(code_lines):
        line_str = code_lines[i]
        # print(f"(docstring) line {line}: {line_str}")

        # we haven't identified the starting line yet.
        if token is None:
            if _is_empty(line_str):
                i += 1
                continue

            elif _contains_field_definition(line_str) or _is_comment(line_str):
                # we haven't reached the start of a docstring yet (since token
                # is None), and we reached a line with an attribute definition,
                # or a comment, hence the docstring is empty.
                return ""

            elif triple_single in line_str and triple_double in line_str:
                # This handles something stupid like:
                # @dataclass
                # class Bob:
                #     a: int
                #     """ hello '''
                #     bob
                #     ''' bye
                #     """
                triple_single_index = line_str.index(triple_single)
                triple_double_index = line_str.index(triple_double)
                if triple_single_index < triple_double_index:
                    token = triple_single
                else:
                    token = triple_double
            elif triple_double in line_str:
                token = triple_double
            elif triple_single in line_str:
                token = triple_single
            else:
                # for i, line in enumerate(code_lines):
                #     print(f"line {i}: <{line}>")
                # print(f"token: <{token}>")
                # print(line_str)
                logger.debug(f"Warning: Unable to parse attribute docstring: {line_str}")
                return ""

            # get the string portion of the line (after a token or possibly
            # between two tokens).
            parts = line_str.split(token, maxsplit=2)
            if len(parts) == 3:
                # This takes care of cases like:
                # @dataclass
                # class Bob:
                #     a: int
                #     """ hello """
                between_tokens = parts[1].strip()
                # print("Between tokens:", between_tokens)
                docstring_contents.append(between_tokens)
                break

            elif len(parts) == 2:
                after_token = parts[1].strip()
                # print("After token:", after_token)
                docstring_contents.append(after_token)
        else:
            # print(f"token is <{token}>")
            if token in line_str:
                # print(f"Line {line} End of a docstring:", line_str)
                before = line_str.split(token, maxsplit=1)[0]
                docstring_contents.append(before.strip())
                break
            else:
                # intermediate line without the token.
                docstring_contents.append(line_str.strip())
        i += 1
    # print("Docstring contents:", docstring_contents)
    return "\n".join(docstring_contents)
