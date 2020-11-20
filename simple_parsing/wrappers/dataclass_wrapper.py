import argparse
import dataclasses
import enum
from typing import *
from typing import cast
from dataclasses import _MISSING_TYPE, MISSING
from .. import docstring, utils
from ..utils import Dataclass, DataclassType
from .wrapper import Wrapper
from .field_wrapper import FieldWrapper
from ..logging_utils import get_logger

logger = get_logger(__file__)

class DataclassWrapper(Wrapper[Dataclass]):
    def __init__(self,
                 dataclass: Type[Dataclass],
                 name: str,
                 default: Dataclass=None,
                 prefix: str="",
                 parent: "DataclassWrapper"=None,
                 _field: dataclasses.Field=None,
                 ):
        # super().__init__(dataclass, name)
        self.dataclass = dataclass
        self._name = name
        self.default = default

        self.fields: List[FieldWrapper] = []
        self._destinations: List[str] = []
        self._required: bool = False
        self._explicit: bool = False
        self._dest: str = ""
        self._children: List[DataclassWrapper] = []
        self._parent = parent
        # the field of the parent, which contains this child dataclass.
        self._field = _field

        # the default values
        self._defaults: List[Dataclass] = []

        if default:
            self.defaults = [default]

        self.optional: bool = False


        for field in dataclasses.fields(self.dataclass):
            if not field.init:
                continue

            if utils.is_subparser_field(field) or utils.is_choice(field):
                wrapper = FieldWrapper(field, parent=self, prefix=prefix)
                self.fields.append(wrapper)
            
            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                raise NotImplementedError(
                    f"Field {field.name} is of type {field.type}, which isn't "
                    f"supported yet. (container of a dataclass type)"
                )
            
            elif dataclasses.is_dataclass(field.type):
                # handle a nested dataclass attribute
                dataclass, name = field.type, field.name
                child_wrapper = DataclassWrapper(dataclass, name, parent=self, _field=field)
                self._children.append(child_wrapper)

            elif utils.contains_dataclass_type_arg(field.type):
                dataclass = utils.get_dataclass_type_arg(field.type)
                name = field.name
                child_wrapper = DataclassWrapper(dataclass, name, parent=self, _field=field, default=None)
                child_wrapper.required = False
                child_wrapper.optional = True
                self._children.append(child_wrapper)

            else:
                # a normal attribute
                field_wrapper = FieldWrapper(field, parent=self)
                logger.debug(f"wrapped field at {field_wrapper.dest} has a default value of {field_wrapper.default}")
                self.fields.append(field_wrapper)
        
        logger.debug(f"The dataclass at attribute {self.dest} has default values: {self.defaults}")


    def add_arguments(self, parser: argparse.ArgumentParser):
        from ..parsing import ArgumentParser
        parser = cast(ArgumentParser, parser)
        
        group = parser.add_argument_group(title=self.title, description=self.description)

        for wrapped_field in self.fields:
            if not wrapped_field.field.metadata.get("cmd", True):
                logger.debug(f"Skipping field {wrapped_field.name} because it has cmd=False.")
                continue

            if wrapped_field.is_subparser:
                wrapped_field.add_subparsers(parser)
                
            elif wrapped_field.arg_options:
                logger.debug(f"Arg options for field '{wrapped_field.name}': {wrapped_field.arg_options}")
                # TODO: CustomAction isn't very easy to debug, and is not working. Maybe look into that. Simulating it for now.
                group.add_argument(*wrapped_field.option_strings, **wrapped_field.arg_options)
    
    def equivalent_argparse_code(self, leading="group") -> str:
        code = ""
        import textwrap
        code += textwrap.dedent(f"""
        group = parser.add_argument_group(title="{self.title.strip()}", description="{self.description.strip()}")
        """)
        for wrapped_field in self.fields:
            if wrapped_field.is_subparser:
                # TODO:
                raise NotImplementedError("Subparsers equivalent is TODO.")
                code += textwrap.dedent(f"""\
                # add subparsers for each dataclass type in the field.
                subparsers = parser.add_subparsers(
                    title={wrapped_field.name},
                    description={wrapped_field.help},
                    dest={wrapped_field.dest},
                )
                subparsers.required = True

                for subcommand, dataclass_type in {self.subparsers_dict.items()}:
                    subparser = subparsers.add_parser(subcommand)
                    subparser = cast(ArgumentParser, subparser)
                    subparser.add_arguments(dataclass_type, dest=self.dest)
                """)
            elif wrapped_field.arg_options:
                code += textwrap.dedent(wrapped_field.equivalent_argparse_code()) + "\n"
        return code

    
    @property
    def name(self) -> str:
        return self._name

    @property
    def parent(self) -> Optional["DataclassWrapper"]:
        return self._parent

    @property
    def defaults(self) -> List[Dataclass]:
        if self._defaults:
            return self._defaults
        if self._field is None:
            return []
        assert self.parent is not None
        if self.parent.defaults:
            self._defaults = []
            for default in self.parent.defaults:
                if default is None:
                    default = None
                else:
                    default = getattr(default, self.name)
                self._defaults.append(default)
        else:
            default_field_value = utils.default_value(self._field)
            if isinstance(default_field_value, _MISSING_TYPE):
                self._defaults = []
            else:
                self._defaults = [default_field_value]
        return self._defaults

    @defaults.setter
    def defaults(self, value: List[Dataclass]):
        self._defaults = value

    @property
    def title(self) -> str:
        names_string = f""" [{', '.join(f"'{dest}'" for dest in self.destinations)}]"""
        title = self.dataclass.__qualname__ + names_string
        return title

    @property
    def description(self) -> str:
        if self.parent and self._field:    
            doc = docstring.get_attribute_docstring(self.parent.dataclass, self._field.name)            
            if doc is not None:
                if doc.docstring_below:
                    return doc.docstring_below
                elif doc.comment_above:
                    return doc.comment_above
                elif doc.comment_inline:
                    return doc.comment_inline
        return self.dataclass.__doc__ or ""

    # @property
    # def prefix(self) -> str:
    #     return self._prefix
    
    # @prefix.setter
    # def prefix(self, value: str):
    #     self._prefix = value
    #     for child_wrapper in self._children:
    #         child_wrapper.prefix = value

    @property
    def required(self) -> bool:
        return self._required

    @required.setter
    def required(self, value: bool):
        self._required = value
        for field in self.fields:
            field.required = value
        for child_wrapper in self._children:
            child_wrapper.required = value

    @property
    def multiple(self) -> bool:
        return len(self.destinations) > 1

    @property
    def descendants(self):
        for child in self._children:
            yield child
            yield from child.descendants

    @property
    def dest(self):
        lineage = []
        parent = self.parent
        while parent is not None:
            lineage.append(parent.name)
            parent = parent.parent
        lineage = list(reversed(lineage))
        lineage.append(self.name)
        _dest = ".".join(lineage)
        logger.debug(f"getting dest, returning {_dest}")
        return _dest
   

    @property
    def destinations(self) -> List[str]:
        if not self._destinations:
            if self.parent:
                self._destinations = [f"{d}.{self.name}" for d in self.parent.destinations]
            else:
                self._destinations = [self.name]
        return self._destinations

    @destinations.setter
    def destinations(self, value: List[str]):
        self._destinations = value

    def merge(self, other: "DataclassWrapper"):
        """Absorb all the relevant attributes from another wrapper.
        Args:
            other (DataclassWrapper): Another instance to absorb into this one.
        """
        # logger.debug(f"merging \n{self}\n with \n{other}")
        logger.debug(f"self destinations: {self.destinations}")
        logger.debug(f"other destinations: {other.destinations}")
        # assert not set(self.destinations).intersection(set(other.destinations)), "shouldn't have overlap in destinations"
        # self.destinations.extend(other.destinations)
        for dest in other.destinations:
            if dest not in self.destinations:
                self.destinations.append(dest)
        logger.debug(f"destinations after merge: {self.destinations}")
        self.defaults.extend(other.defaults)

        for field_wrapper in self.fields:
            field_wrapper.default = None

        for child, other_child in zip(self._children, other._children):
            child.merge(other_child)
        
