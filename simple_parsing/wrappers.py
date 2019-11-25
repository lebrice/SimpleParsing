import dataclasses
import enum
import logging
from typing import *
import argparse

from . import docstring, utils
from .utils import Dataclass, DataclassType

logger = logging.getLogger(__name__)

class CustomAction(argparse.Action):
    # TODO: the CustomAction isn't always called!

    def __init__(self, option_strings, dest, field, **kwargs):
        self.field = field
        logger.debug(f"Creating Custom Action for field {field}")
        super().__init__(option_strings, dest, **self.field.arg_options)

    def __call__(self, parser, namespace, values, option_string=None):
        logger.debug(f"INSIDE CustomAction's __call__: {namespace}, {values}, {option_string}")
        before = parser.constructor_arguments.copy()
        result = self.field(parser, namespace, values, option_string)
        after = parser.constructor_arguments
        # assert before != after, f"before: {before}, after: {after}"
        # setattr(namespace, self.dest, values)

@dataclasses.dataclass
class FieldWrapper(argparse.Action):
    field: dataclasses.Field
    parent: "DataclassWrapper" = dataclasses.field(repr=False)
    _required: Optional[bool] = dataclasses.field(init=False, default=None)
    _docstring: Optional[docstring.AttributeDocString] = dataclasses.field(init=False, default=None)
    _multiple: bool = dataclasses.field(init=False, default=False)
    _default: Any = dataclasses.field(init=False, default=None)
    # the argparse-related options:
    _arg_options: Dict[str, Any] = dataclasses.field(init=False, default_factory=dict)
    
    def __post_init__(self):
        try:
            self._docstring = docstring.get_attribute_docstring(self.parent.dataclass, self.field.name)
        except (SystemExit, Exception) as e:
            logging.warning("Couldn't find attribute docstring:", e)
            self._docstring = docstring.AttributeDocString()

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Any, option_string: Optional[str] = None):
        logger.debug(f"Inside the 'call' of wrapper for {self.name}, values are {values}, option_string={option_string}")
        from simple_parsing import ArgumentParser
        parser: ArgumentParser = parser # type: ignore
        
        logger.debug(f"destinations:", self.destinations)
        values = self.duplicate_if_needed(values)
        logger.debug(f"VALUES IS '{values}'")
        for parent_dest, value in zip(self.destinations, values):
            logger.debug("Before preprocessing the value:", value)
            value = self.postprocess(value)
            logger.debug("After postprocessing the value: ", value)
            logger.debug(f"setting value of {value} in constructor arguments of parent at key '{parent_dest}' and attribute '{self.name}'")
            parser.constructor_arguments[parent_dest][self.name] = value # type: ignore
    
    def duplicate_if_needed(self, parsed_values: Any) -> List[Any]:
        num_instances_to_parse = len(self.destinations)
        logger.debug("field preprocess:", parsed_values, "num to parse:", num_instances_to_parse)
        
        if self.multiple:
            assert num_instances_to_parse > 1, "multiple is true but we're expected to instantiate only one instance"
        else:
            # TODO: if we do anything with list of dataclasses we might need to chanfieldge this.
            assert num_instances_to_parse == 1, f"multiple is false but we're expected to instantiate {num_instances_to_parse} instances"
        
        instance_arguments: List[Any] = []
        # what if the attribute is a list? This might complicate things, no?

        if utils.is_tuple_or_list(self.field.type):
            logger.debug("Duplicating a list...")
            nesting_level = utils.get_nesting_level(parsed_values)
            logger.debug("Nesting level:", nesting_level)
            logger.debug("parsed values: ", parsed_values)

            while nesting_level < 2:
                parsed_values = [parsed_values]
                nesting_level += 1
            if nesting_level != 2:
                logger.debug(f"BEWARE, NESTING LEVEL IS OFF THE CHARTS! (nesting level is {nesting_level})")
            
            if len(parsed_values) == num_instances_to_parse:
                values = parsed_values
            elif len(parsed_values) == 1:
                values = parsed_values * num_instances_to_parse
            # values = [parsed_values]
        else:
            values = parsed_values if isinstance(parsed_values, list) else [parsed_values]
        logger.debug("values as a list:", values)
        if len(values) == num_instances_to_parse:
            return values
        elif len(values) == 1:
            return values * num_instances_to_parse
        else:
            raise utils.InconsistentArgumentError(
                f"The field '{self.name}' contains {len(values)} values, but either 1 or {num_instances_to_parse} values were expected."
            )
        return parsed_values


    def postprocess(self, value: Any) -> Any:
        """TODO: apply any corrections from the 'raw' parsed values to the constructor arguments dict.
        
        Args:
            parsed_values (Any): [description]
        
        Returns:
            Any: [description]
        """
        logger.debug(f"field postprocessing for value '{value}'")
        
        if enum.Enum in self.field.type.mro():
            return self.field.type[value]
        
        elif utils.is_tuple(self.field.type):
            return tuple(value)
        
        elif utils.is_list(self.field.type):
            return list(value)

        elif self.field.type is bool:
            default_value = False if self.field.default is dataclasses.MISSING else self.field.default
            if value is None:
                return not default_value
            elif isinstance(value, bool):
                return value
            else:
                raise RuntimeError(f"bool argument {self.name} isn't bool: {value}")

        else:
            return value

    @property
    def multiple(self) -> bool:
        return self._multiple

    @multiple.setter
    def multiple(self, value: bool):
        if self._multiple != value:
            self.arg_options.clear()
        self._multiple = value 
      
    @property
    def arg_options(self) -> Dict[str, Any]:
        if self._arg_options:
            return self._arg_options
        else:
            self._arg_options = self.get_arg_options()
        return self._arg_options

    @property
    def destinations(self) -> List[str]:
        return self.parent.destinations

    @property
    def option_strings(self):
        prefix: str = self.parent.prefix
        if prefix:
            return [f"--{prefix}{self.name}"]
        return [f"--{self.name}"]

    @property
    def dest(self):
        lineage = []
        parent = self.parent
        while parent is not None:
            lineage.append(parent.attribute_name)
            parent = parent._parent
        lineage = list(reversed(lineage))
        lineage.append(self.name)
        _dest = ".".join(lineage)
        logger.debug("getting dest, returning ", _dest)
        return _dest

    @property
    def nargs(self):
        return self.arg_options.get("nargs")

    @property
    def const(self):
        return self.arg_options.get("const")

    @property
    def default(self):
        if self._default is not None:
            return self._default
        return self.arg_options.get("default")        

    @default.setter
    def default(self, value: Any):
        self._default = value

    @property
    def type(self):
        return self.arg_options.get("type")

    @property
    def choices(self):
        return self.arg_options.get("choices")
    
    @property
    def required(self):
        return (self.parent and self.parent.required) or self.arg_options.get("required")

    @property
    def help(self):
        return None

    @property
    def metavar(self):
        return self.arg_options.get("metavar")

    @property
    def name(self) -> str:
        return self.field.name

    def get_arg_options(self) -> Dict[str, Any]:
        f = self.field
        multiple = self.multiple

        if not f.init:
            return {}

        elif dataclasses.is_dataclass(self.field.type):
            assert False, "Shouldn't have created a FieldWrapper for a dataclass in the first place!"
        elif utils.is_tuple_or_list_of_dataclasses(self.field.type):
            assert False, "Shouldn't have created a FieldWrapper for a list of dataclasses in the first place!"

        _arg_options: Dict[str, Any] = { 
            "type": f.type,
        }

        help_string = None
        if self._docstring is not None:
            if self._docstring.docstring_below:
                help_string = self._docstring.docstring_below
            elif self._docstring.comment_above:
                help_string = self._docstring.comment_above
            elif self._docstring.comment_inline:
                help_string = self._docstring.comment_inline
        _arg_options["help"] = help_string

        if self.field.default is not dataclasses.MISSING:
            _arg_options["default"] = self.field.default
        elif self.field.default_factory is not dataclasses.MISSING: # type: ignore
            _arg_options["default"] = self.field.default_factory() # type: ignore
        else:
            # _arg_options["default"] = argparse.SUPPRESS
            _arg_options["required"] = True

        if enum.Enum in f.type.mro():
            _arg_options["choices"] = list(e.name for e in f.type)
            _arg_options["type"] = str # otherwise we can't parse the enum, as we get a string.
            if "default" in _arg_options:
                default_value = _arg_options["default"]
                # if the default value is the Enum object, we make it a string
                if isinstance(default_value, enum.Enum):
                    _arg_options["default"] = default_value.name
        
        elif utils.is_tuple_or_list(f.type):
            logger.debug("Adding a list attribute")
            # Check if typing.List or typing.Tuple was used as an annotation, in which case we can automatically convert items to the desired item type.
            # NOTE: we only support tuples with a single type, for simplicity's sake. 
            T = utils.get_argparse_container_type(f.type)
            _arg_options["nargs"] = "*"
            # arg_options["action"] = "append"
            if multiple:
                _arg_options["type"] = utils._parse_multiple_containers(f.type)
            else:
                # TODO: Supporting the `--a '1 2 3'`, `--a [1,2,3]`, and `--a 1 2 3` at the same time is syntax is kinda hard, and I'm not sure if it's really necessary.
                # right now, we support --a '1 2 3' '4 5 6' and --a [1,2,3] [4,5,6] only when parsing multiple instances.
                # arg_options["type"] = utils._parse_container(f.type)
                _arg_options["type"] = T
                
        
        elif f.type is bool:
            _arg_options["default"] = False if f.default is dataclasses.MISSING else f.default
            _arg_options["type"] = utils.str2bool
            _arg_options["nargs"] = "*" if multiple else "?"
            if f.default is dataclasses.MISSING:
                _arg_options["required"] = True
        
        if multiple:
            required = _arg_options.get("required", False)
            default = _arg_options.get("default")
            if required:
                _arg_options["nargs"] = "+"
            else:
                _arg_options["nargs"] = "*"
                _arg_options["default"] = [default]

        return _arg_options


@dataclasses.dataclass
class DataclassWrapper(Generic[Dataclass]):
    dataclass: Type[Dataclass]
    attribute_name: str
    fields: List[FieldWrapper] = dataclasses.field(init=False, default_factory=list, repr=False)
    _destinations: List[str] = dataclasses.field(init=False, default_factory=list, repr=False)
    _multiple: bool = dataclasses.field(init=False, default=False)
    _required: bool = dataclasses.field(init=False, default=False)
    _prefix: str = dataclasses.field(init=False, default="")
    _children: List["DataclassWrapper"] = dataclasses.field(default_factory=list, repr=False)
    _parent: Optional["DataclassWrapper"] = dataclasses.field(default=None, repr=False)

    _field: Optional[dataclasses.Field] = dataclasses.field(default=None)
    
    def __post_init__(self):
        self.destinations
        for field in dataclasses.fields(self.dataclass):
            if dataclasses.is_dataclass(field.type):
                # handle a nested dataclass.
                dataclass = field.type
                attribute_name = field.name
                child_wrapper = DataclassWrapper(dataclass, attribute_name, _parent=self)
                child_wrapper._field = field
                # TODO: correctly handle the default value for a Dataclass attribute.
                child_wrapper.prefix = self.prefix                 
                self._children.append(child_wrapper)
                
            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                raise NotImplementedError(f"""\
                Nesting using attributes which are containers of a dataclass isn't supported (yet).
                """)
            else:
                # regular field.
                field_wrapper = FieldWrapper(field, parent=self)
                self.fields.append(field_wrapper)

    def add_arguments(self, parser: argparse.ArgumentParser):
        from .parsing import ArgumentParser
        parser : ArgumentParser = parser # type: ignore
        names_string = f""" [{', '.join(f"'{dest}'" for dest in self.destinations)}]"""
        title = self.dataclass.__qualname__ + names_string
        description = self.dataclass.__doc__

        default_value = None
        if self._field:
            if self._field.default is not dataclasses.MISSING:
                default_value = self._field.default
            elif self._field.default_factory is not dataclasses.MISSING: # type: ignore
                default_value = self._field.default_factory() # type: ignore
            assert self._parent is not None
            doc = docstring.get_attribute_docstring(self._parent.dataclass, self._field.name)
            
            if doc is not None:
                if doc.docstring_below:
                    description = doc.docstring_below
                elif doc.comment_above:
                    description = doc.comment_above
                elif doc.comment_inline:
                    description = doc.comment_inline
        
        group = parser.add_argument_group(
            title=title,
            description=description
        )

        print("The nested dataclass had a default value of ", default_value)
        for wrapped_field in self.fields:
            if wrapped_field.arg_options:
                    
                logger.debug(f"Adding argument for field '{wrapped_field.name}'")
                if default_value is not None:
                    wrapped_field.default = getattr(default_value, wrapped_field.name, wrapped_field.default)
                # TODO: CustomAction isn't very easy to debug, and is not working. Maybe look into that. Simulating it for now.
                # group.add_argument(wrapped_field.option_strings[0], dest=wrapped_field.dest, action=CustomAction, field=wrapped_field, **wrapped_field.arg_options)
                group.add_argument(wrapped_field.option_strings[0], dest=wrapped_field.dest, **wrapped_field.arg_options)

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
        return self._multiple

    @multiple.setter
    def multiple(self, value: bool):
        for wrapped_field in self.fields:
            wrapped_field.multiple = value
        for child_wrapper in self._children:
            child_wrapper.multiple = value
        self._multiple = value

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
        logger.debug("getting dest, returning ", _dest)
        return _dest


    @property
    def destinations(self) -> List[str]:
        # logger.debug(f"getting destinations of {self}")
        # logger.debug(f"self._destinations is {self._destinations}")
        # logger.debug(f"Parent is {self._parent}")
        if not self._destinations:
            if self._parent:
                self._destinations = [f"{d}.{self.attribute_name}" for d in self._parent.destinations]
            else:
                self._destinations = [self.attribute_name]
        # logger.debug(f"returning {self._destinations}")
        return self._destinations

    def merge(self, other: "DataclassWrapper"):
        """Absorb all the relevant attributes from another wrapper.
        Args:
            other (DataclassWrapper): Another instance to absorb into this one.
        """
        logger.debug(f"merging \n{self}\n with \n{other}")
        self.destinations.extend(other.destinations)
        for child, other_child in zip(self.descendants, other.descendants):
            child.merge(other_child)
        self.multiple = True

    def instantiate_dataclass(self, constructor_args: Dict[str, Any]) -> Dataclass:
        """
        Creates an instance of the dataclass using the given dict of constructor arguments, including nested dataclasses if present.
        """
        logger.debug(f"args dict: {constructor_args}")
        
        dataclass = self.dataclass
        print(f"Constructor arguments for dataclass {dataclass}: {constructor_args}")
        instance: T = dataclass(**constructor_args) #type: ignore
        return instance
