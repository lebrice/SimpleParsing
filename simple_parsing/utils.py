"""Utility for retrieveing the docstring of a dataclass
@author: Fabrice Normandin
"""
from dataclasses import dataclass
import inspect
from typing import *

@dataclass
class AttributeDocString():
    """Simple dataclass for holding the comments of a given field.
    """
    comment_above: str = ""
    comment_inline: str = ""
    docstring_below: str = ""


def find_docstring_of_field(some_dataclass: type, field_name: str) -> AttributeDocString:
    """Returns the docstring of a dataclass field.
    NOTE: a docstring can either be: 
        - An inline comment, starting with <#>
        - A Comment on the preceding line, starting with <#>
        - A docstring on the following line, starting with either <\"\"\"> or <'''>
    
    Arguments:
        some_dataclass {type} -- a dataclass
        field_name {str} -- the name of the field.
    
    Returns:
        AttributeDocString -- [description]
    """


    def contains_attribute_definition(line_str: str) -> bool:
        """Returns wether or not a line contains a an class attribute definition (something like `a: int`).
        
        Arguments:
            line_str {str} -- the line content
        
        Returns:
            bool -- True if there is an attribute definition in the line. False if there isn't.
        """
        parts = line_str.split("#", maxsplit=1)
        part_before_potential_comment = parts[0].strip()
        return ":" in part_before_potential_comment

    def is_empty(line_str: int) -> bool:
        return line_str.strip() == ""

    def get_comment_at_line(code_lines: List[str], line: int) -> str:
        """Gets the comment at line `line` in `code_lines`.
        
        Arguments:
            line {int} -- the index of the line in code_lines
        
        Returns:
            str -- the comment at the given line. empty string if not present.
        """
        line_str = code_lines[line]
        assert not contains_attribute_definition(line_str)
        if "#" not in line_str:
            return ""
        parts = line_str.split("#", maxsplit=1)
        comment = parts[1].strip()   
        return comment

    def get_inline_comment_at_line(code_lines: List[str], line: int) -> str:
        """Gets the inline comment at line `line`. 
        
        Arguments:
            line {int} -- the index of the line in code_lines
        
        Returns:
            str -- the inline comment at the given line. empty string if not present.
        """
        assert 0 <= line < len(code_lines)
        assert contains_attribute_definition(code_lines[line])
        line_str = code_lines[line]
        parts = line_str.split("#")
        if len(parts) != 2:
            return ""
        comment = parts[1].strip()
        return comment

    def get_comment_ending_at_line(code_lines: List[str], line: int) -> str:
        result = ""
        start_line = line
        end_line = line

        # print(f"Get comment ending at line {line}")
        # for i, line in enumerate(code_lines):
        #     print(f"line {i}: {line}")

        # move up the code, one line at a time, while we don't hit the start, an attribute definition, or the end of a docstring.
        while start_line > 0:
            line_str = code_lines[start_line]
            if contains_attribute_definition(line_str):
                break # previous line is an assignment
            if '"""' in line_str or "'''" in line_str:
                break # previous line has a docstring
            start_line -= 1
        
        lines = []
        for i in range(start_line+1, end_line):
            # print(f"line {i}: {code_lines[i]}")
            if is_empty(code_lines[i]):
                continue
            assert not contains_attribute_definition(code_lines[i])
            comment = get_comment_at_line(code_lines, i)
            lines.append(comment)
        return "\n".join(lines)


    
    def get_docstring_starting_at_line(code_lines: List[str], line: int) -> str:
        first_line = line
        i = line
        end_line: int
        token: str = None
        triple_single = "'''"
        triple_double = '"""'
        # print("finding docstring starting from line", line)
        
        # if we are looking further down than the end of the code, there is no docstring. 
        if line >= len(code_lines):
            return ""
        # the list of lines making up the docstring.
        docstring_contents: List[str] = []

        while i <= len(code_lines):
            line_str = code_lines[i]
            # print(f"(docstring) line {line}: {line_str}")

            # we haven't identified the starting line yet.
            if token is None:
                if is_empty(line_str):
                    i += 1
                    continue
                # This is the starting line.
                elif contains_attribute_definition(line_str):
                    # we haven't reached the start of a docstring yet (token is None), and we reached a line with an attribute definition, hence the docstring is empty.
                    # print("attribute def, we hit the end")
                    return ""

                elif triple_single in line_str and triple_double in line_str:
                    #* This handles something stupid like:
                    # @dataclass
                    # class Bob:
                    #     a: int
                    #     """ hello '''
                    #     bob
                    #     ''' bye
                    #     """
                    if line_str.index(triple_single) < line_str.index(triple_double):
                        token = triple_single
                    else:
                        token = triple_double
                elif triple_double in line_str:
                    token = triple_double
                elif triple_single in line_str:
                    token = triple_single
                else:
                    raise RuntimeError(f"Line {i} should have been the start of a docstring.")
                
                # get the string portion of the line (after a token or possibly between two tokens).
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
    

    source = inspect.getsource(some_dataclass)
    code_lines: List[str] = source.splitlines()
    # the first line is the class definition, we skip it.
    start_line_index = 1
    # starting at the second line, there might be the docstring for the class. We want to skip over that until we reach an attribute definition.
    while start_line_index < len(code_lines) and not contains_attribute_definition(code_lines[start_line_index]):
        start_line_index += 1


    # for i, line in zip(range(start_line_index, len(code_lines)), code_lines[start_line_index:]):
    #     print(f"line {i}: <{line}>")
    #     print("Is empty:", is_empty(line))
    #     print("Has attribute definition:", contains_attribute_definition(line))

    lines_with_attribute_defs = [(index, line) for index, line in enumerate(code_lines) if contains_attribute_definition(line)]
    
    
    for i, line in lines_with_attribute_defs:
        if ":" in line:
            parts: List[str] = line.split(":", maxsplit=1)
            if parts[0].strip() == field_name:
                # print("FOUND LINE AT INDEX", i)
                comment_above = get_comment_ending_at_line(code_lines, i-1)
                comment_inline = get_inline_comment_at_line(code_lines, i)
                docstring_below = get_docstring_starting_at_line(code_lines, i+1)
                complete_docstring = AttributeDocString(comment_above, comment_inline, docstring_below)
                # print(f"\nComplete docstring for field '{field_name}':", complete_docstring, "\n\n")
                return complete_docstring
                
        