import argparse
import dataclasses
import enum
import logging
from typing import *
from typing import cast

from .. import docstring, utils
from ..utils import Dataclass, DataclassType
from .field_wrapper import FieldWrapper

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class DataclassWrapper(Generic[Dataclass]):
    dataclass: Type[Dataclass]
    attribute_name: str
    default: dataclasses.InitVar[Optional[Dataclass]] = None

    fields: List[FieldWrapper] = dataclasses.field(default_factory=list, repr=False, init=False)
    _destinations: List[str] = dataclasses.field(default_factory=list, init=False)
    _required: bool = False
    _explicit: bool = False
    _prefix: str = ""
    _children: List["DataclassWrapper"] = dataclasses.field(default_factory=list, repr=False)
    _parent: Optional["DataclassWrapper"] = dataclasses.field(default=None, repr=False)

    # the field of the parent, which contains this child dataclass.
    _field: Optional[dataclasses.Field] = None
    # the default values
    _defaults: List[Dataclass] = dataclasses.field(default_factory=list)
    
    def __post_init__(self, default: Dataclass):
        if default:
            self.defaults = [default]

        for field in dataclasses.fields(self.dataclass):
            if dataclasses.is_dataclass(field.type):
                # handle a nested dataclass attribute
                dataclass, attribute_name = field.type, field.name
                child_wrapper = DataclassWrapper(dataclass, attribute_name, _prefix=self._prefix, _parent=self, _field=field)
                self._children.append(child_wrapper)
                
            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                raise NotImplementedError(f"Nesting using attributes which are containers of a dataclass isn't supported (yet).")
            else:
                # a normal attribute
                field_wrapper: FieldWrapper = FieldWrapper(field, parent=self)
                logger.debug(f"wrapped field at {field_wrapper.dest} has a default value of {field_wrapper.default}")
                self.fields.append(field_wrapper)
        
        logger.debug(f"The dataclass at attribute {self.dest} has default values: {self.defaults}")


    def add_arguments(self, parser: argparse.ArgumentParser):
        from ..parsing import ArgumentParser
        parser = cast(ArgumentParser, parser)
        
        group = parser.add_argument_group(title=self.title, description=self.description)

        for wrapped_field in self.fields:
            if wrapped_field.is_subparser:
                wrapped_field.add_subparsers(parser)
                
            elif wrapped_field.arg_options:
                logger.debug(f"Arg options for field '{wrapped_field.name}': {wrapped_field.arg_options}")
                # TODO: CustomAction isn't very easy to debug, and is not working. Maybe look into that. Simulating it for now.
                group.add_argument(*wrapped_field.option_strings, **wrapped_field.arg_options)


    @property
    def defaults(self) -> List[Dataclass]:
        if self._defaults:
            return self._defaults
        if self._field is None:
            return []
        assert self._parent is not None
        if self._parent.defaults:
            self._defaults = [getattr(default, self.attribute_name) for default in self._parent.defaults]
        else:
            default_field_value = utils.default_value(self._field)
            if default_field_value is not None:
                self._defaults = [default_field_value]
            else:
                self._defaults = []
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
    def description(self) -> Optional[str]:
        if self._parent and self._field:    
            doc = docstring.get_attribute_docstring(self._parent.dataclass, self._field.name)            
            if doc is not None:
                if doc.docstring_below:
                    return doc.docstring_below
                elif doc.comment_above:
                    return doc.comment_above
                elif doc.comment_inline:
                    return doc.comment_inline
        return self.dataclass.__doc__

    @property
    def nesting_level(self) -> int:
        level = 0
        parent = self._parent
        while parent is not None:
            parent = parent._parent
            level += 1
        return level

    @property
    def prefix(self) -> str:
        return self._prefix
    
    @prefix.setter
    def prefix(self, value: str):
        self._prefix = value
        for child_wrapper in self._children:
            child_wrapper.prefix = value

    @property
    def required(self) -> bool:
        return self._required

    @required.setter
    def required(self, value: bool):
        self._required = value
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
        parent = self._parent
        while parent is not None:
            lineage.append(parent.attribute_name)
            parent = parent._parent
        lineage = list(reversed(lineage))
        lineage.append(self.attribute_name)
        _dest = ".".join(lineage)
        logger.debug(f"getting dest, returning {_dest}")
        return _dest
           

    @property
    def destinations(self) -> List[str]:
        if not self._destinations:
            if self._parent:
                self._destinations = [f"{d}.{self.attribute_name}" for d in self._parent.destinations]
            else:
                self._destinations = [self.attribute_name]
        return self._destinations

    @destinations.setter
    def destinations(self, value: List[str]):
        self._destinations = value

    @property
    def explicit(self) -> bool:
        """Wether or not all the arguments should have an explicit prefix differentiating them.
        
        Returns:
            bool: Wether or not this wrapper (and all its children, if any) are in explicit mode..
        """
        return self._explicit

    @explicit.setter
    def explicit(self, value: bool):
        if value:
            self._prefix = self.dest + "."
            for child in self._children:
                child.explicit = True
        self._explicit = value

    def merge(self, other: "DataclassWrapper"):
        """Absorb all the relevant attributes from another wrapper.
        Args:
            other (DataclassWrapper): Another instance to absorb into this one.
        """
        # logger.info(f"merging \n{self}\n with \n{other}")
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
        
