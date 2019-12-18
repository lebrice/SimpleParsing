#!/usr/bin/python3

import os
from typing import *
import examples
import inspect

def make_example_script_doc(example_name: str):
    before_module = __import__(f"examples.{example_name}_before")
    after_module = __import__(f"examples.{example_name}_after")
    print(before_module.__doc__)
    exit()
    with open(f"examples/{example_name}_before.py") as before_file:
        print(before_file.readlines())

    with open(f"{example_name}.md", "w") as markdown_file:
        print(before_file.readline())
        

make_example_script_doc("basic_example")