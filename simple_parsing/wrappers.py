import dataclasses
import enum
import logging
from typing import *
import argparse

from . import docstring, utils
from .utils import Dataclass, DataclassType



@dataclasses.dataclass
class FieldWrapper(argparse.Action):
    field: dataclasses.Field
    _parent: "DataclassWrapper" = None
    
    _docstring: Optional[docstring.AttributeDocString] = dataclasses.field(init=False, default=None)
    _multiple: bool = dataclasses.field(init=False, default=False)

    _arg_options: Dict[str, Any] = dataclasses.field(init=False, default_factory=dict)
    # the argparse-related options:
    # _option_strings: List[str] = dataclasses.field(init=False, default_factory=list, repr=False)
    # _dest: List[str] = dataclasses.field(init=False, default_factory=list, repr=False)
    # _nargs: Optional[Union[str, int]] = dataclasses.field(init=False, default=None, repr=False)
    # _const: Optional[str] = dataclasses.field(init=False, default=None, repr=False)
    # _default: Optional[Any] = dataclasses.field(init=False, default=None, repr=False)
    # _type: Optional[Any] = dataclasses.field(init=False, default=None, repr=False)
    # _choices: Optional[List[Any]] = dataclasses.field(init=False, default=None, repr=False)
    # _required: bool = dataclasses.field(init=False, default=False, repr=False)
    # _help: Optional[str] = dataclasses.field(init=False, default=None, repr=False)
    # _metavar: Optional[str] = dataclasses.field(init=False, default=None, repr=False)
    
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Any, option_string: Optional[str] = None):
        print(f"Inside the 'call' of wrapper for {self.name}, values are {values}, option_string={option_string}")
        key = self.dest
        value = self.postprocess(values)
        print(f"setting value of {value} in constructor arguments of parent at key {key}")
        parser.constructor_arguments[self.dest] # type: ignore
    
    def postprocess(self, parsed_values: Any) -> Any:
        """TODO: apply any corrections from the 'raw' parsed values to the constructor arguments dict.
        
        Args:
            parsed_values (Any): [description]
        
        Returns:
            Any: [description]
        """
        return parsed_values

    @property
    def multiple(self) -> bool:
        return self._multiple

    @multiple.setter
    def multiple(self, value: bool):
        if self._multiple != value:
            self.arg_options.clear()
        self._multiple = value 
    
    def __key(self):
        return (self.field, self.name)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, FieldWrapper):
            return self.__key() == other.__key()
    
    @property
    def arg_options(self) -> Dict[str, Any]:
        if self._arg_options:
            return self._arg_options
        else:
            self._arg_options = self.get_arg_options()
        return self._arg_options

    @property
    def option_strings(self):
        return [f"--{self.name}"]

    @property
    def dest(self):
        return self.name

    @property
    def nargs(self):
        return self.arg_options.get("nargs")

    @property
    def const(self):
        return self.arg_options.get("const")

    @property
    def default(self):
        return self.arg_options.get("default")        

    @property
    def type(self):
        return self.arg_options.get("type")

    @property
    def choices(self):
        return self.arg_options.get("choices")
    
    @property
    def required(self) -> bool:
        return self.arg_options.get("required")

    @property
    def help(self):
        return None

    @property
    def metavar(self):
        return self.arg_options.get("metavar")

    @property
    def name(self) -> str:
        return self.prefix + self.field.name

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
        elif self.field.default_factory is not dataclasses.MISSING:
            _arg_options["default"] = self.field.default_factory()
        else:
            pass
            # _arg_options["required"] = True

        # if f.default is not dataclasses.MISSING:
        #     _arg_options["default"] = f.default
        # elif f.default_factory is not dataclasses.MISSING: # type: ignore
        #     _arg_options["default"] = f.default_factory() # type: ignore
        # else:
        #     _arg_options["required"] = True

        if enum.Enum in f.type.mro():
            _arg_options["choices"] = list(e.name for e in f.type)
            _arg_options["type"] = str # otherwise we can't parse the enum, as we get a string.
            if "default" in _arg_options:
                default_value = _arg_options["default"]
                # if the default value is the Enum object, we make it a string
                if isinstance(default_value, enum.Enum):
                    _arg_options["default"] = default_value.name
        
        elif utils.is_tuple_or_list(f.type):
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
            if required:
                _arg_options["nargs"] = "+"
            else:
                _arg_options["nargs"] = "*"
                _arg_options["default"] = [_arg_options["default"]]

        return _arg_options


@dataclasses.dataclass
class DataclassWrapper(Generic[Dataclass]):
    dataclass: Type[Dataclass]
    # dest: List[str] = dataclasses.field(default_factory=list)
    destinations: List[str] = dataclasses.field(default_factory=list)
    fields: List[FieldWrapper] = dataclasses.field(init=False, default_factory=list, repr=False)
    _multiple: bool = dataclasses.field(init=False, default=False)
    _required: bool = dataclasses.field(init=False, default=False)
    _prefix: str = dataclasses.field(init=False, default="")
    _children: List["DataclassWrapper"] = dataclasses.field(default_factory=list)
    _parent: Optional["DataclassWrapper"] = None


    def __post_init__(self):
        for field in dataclasses.fields(self.dataclass):
            if dataclasses.is_dataclass(field.type):
                # handle a nested dataclass.
                child_wrapper = DataclassWrapper(field.type)
                child_wrapper.destinations = [f"{d}.{field.name}" for d in self.destinations]
                child_wrapper.prefix = self.prefix
                child_wrapper._parent = self
                self._children.append(child_wrapper)
            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                raise NotImplementedError(f"""\
                Nesting using attributes which are containers of a dataclass isn't supported (yet).
                """)
            else:
                # regular field.
                field_wrapper = FieldWrapper(field)
                try:
                    field_wrapper._docstring = docstring.get_attribute_docstring(self.dataclass, field.name)
                except (SystemExit, Exception) as e:
                    logging.warning("Couldn't find attribute docstring:", e)
                    field_wrapper._docstring = docstring.AttributeDocString()
                self.fields.append(field_wrapper)

    def add_arguments(self, parser: argparse.ArgumentParser):
        names_string = f""" [{', '.join(f"'{dest}'" for dest in self.destinations)}]"""
        group = parser.add_argument_group(
            title=self.dataclass.__qualname__ + names_string,
            description=self.dataclass.__doc__
        )
        for wrapped_field in self.fields:
            for dest in self.destinations:
                
                def make_action(*args, **kwargs) -> argparse.Action:
                    print("args:", args)
                    print("kwargs:", kwargs)
                    return wrapped_field

                group.add_argument(wrapped_field.name, action=make_action, **wrapped_field.arg_options)

    @property
    def prefix(self) -> str:
        return self._prefix
    
    @prefix.setter
    def prefix(self, value: str):
        self._prefix = value
        for wrapped_field in self.fields:
            wrapped_field.prefix = value
        for child_wrapper in self._children:
            child_wrapper.prefix = value

    @property
    def required(self) -> bool:
        return self._required

    @required.setter
    def required(self, value: bool):
        self._required = value
        for wrapped_field in self.fields:
            wrapped_field.required = value
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

    def __iter__(self):
        yield self
        yield from self.descendants

    def merge(self, other: "DataclassWrapper"):
        """Absorb all the relevant attributes from another wrapper.
        
        
        Args:
            other (DataclassWrapper): Another instance to absorb into this one.
        """
        self.destinations.extend(other.destinations)
        self._children.extend(other._children)
        self.multiple = True


    def get_constructor_arguments(self, args: Union[Dict[str, Any], argparse.Namespace], num_instances_to_parse: int = 1) -> List[Dict[str, Any]]:
        """
        Parses the constructor arguments for every instance of the wrapped dataclass from the results of `parser.parse_args()`
        """
        args_dict: Dict[str, Any] = vars(args) if isinstance(args, argparse.Namespace) else args
        constructor_arguments: List[Dict[str, Any]] = []

        logging.debug(self.dataclass, args_dict, num_instances_to_parse)
        logging.debug(f"args: {args}")
        
        if self.multiple:
            assert num_instances_to_parse > 1, "multiple is true but we're expected to instantiate only one instance"
        else:
            assert num_instances_to_parse == 1, f"multiple is false but we're expected to instantiate {num_instances_to_parse} instances"

        for i in range(num_instances_to_parse):
            
            instance_arguments: Dict[str, Union[Any, List]] = {}

            for wrapped_field in self.fields:
                f = wrapped_field.field

                if not f.init:
                    continue

                if wrapped_field.is_dataclass:
                    logging.debug("The wrapped field is a dataclass. continuing, since it will be populated later.")
                    continue

                assert not wrapped_field.is_tuple_or_list_of_dataclasses, "Shouldn't have been allowed"
                assert wrapped_field.name in args_dict, f"{f.name} is not in the arguments dict: {args_dict}"
                
                value = args_dict[wrapped_field.name]
                                
                if self.multiple:
                    assert isinstance(value, list), f"all fields should have gotten a list default value... ({value})"

                    if len(value) == 1:
                        instance_arguments[f.name] = value[0]
                    elif len(value) == num_instances_to_parse:
                        instance_arguments[f.name] = value[i]
                    else:
                        raise utils.InconsistentArgumentError(
                            f"The field '{f.name}' contains {len(value)} values, but either 1 or {num_instances_to_parse} values were expected."
                        )
                else:
                    instance_arguments[f.name] = value
            constructor_arguments.append(instance_arguments)
        return constructor_arguments

    def instantiate_dataclass(self, args_dict: Dict[str, Any]) -> Dataclass:
        """
        Creates an instance of the dataclass using the given dict of constructor arguments, including nested dataclasses if present.
        """
        logging.debug(f"args dict: {args_dict}")
        
        dataclass = self.dataclass
        constructor_args: Dict[str, Any] = {}

        for wrapped_field in self.fields:
            f = wrapped_field.field
            logging.debug(f"arg options: '{wrapped_field.arg_options}'")
            if not wrapped_field.arg_options:
                continue
            value = args_dict[f.name]
           
            assert not wrapped_field.is_tuple_or_list_of_dataclasses, "Shouldn't have attributes that are containers of dataclasses!"
            
            if enum.Enum in f.type.mro():
                constructor_args[f.name] = f.type[value]
            
            elif utils.is_tuple(f.type):
                constructor_args[f.name] = tuple(value)
            
            elif utils.is_list(f.type):
                constructor_args[f.name] = list(value)

            elif f.type is bool:
                value = args_dict[f.name]
                constructor_args[f.name] = value
                default_value = False if f.default is dataclasses.MISSING else f.default
                if value is None:
                    constructor_args[f.name] = not default_value
                elif isinstance(value, bool):
                    constructor_args[f.name] = value
                else:
                    raise RuntimeError(f"bool argument {f.name} isn't bool: {value}")

            else:
                constructor_args[f.name] = value
        logging.debug(f"Constructor arguments for dataclass {dataclass}: {constructor_args}")
        instance: T = dataclass(**constructor_args) #type: ignore
        return instance
