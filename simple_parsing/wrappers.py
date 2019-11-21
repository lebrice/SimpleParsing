import dataclasses
import enum
import logging
from typing import *
import argparse

from . import docstring, utils


Dataclass = TypeVar("Dataclass")

class CustomAction(argparse.Action):
    def __init__(self, field: "FieldWrapper"):
        option_strings = f"--{field.name}"
        dest = field.name
        super().__init__(
            option_strings,
            dest,
            nargs=None,
            const=None,
            default=None,
            type=None,
            choices=None,
            required=False,
            help=None,
            metavar=None
        )

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Any, option_string: Optional[str] = None):
        pass


@dataclasses.dataclass
class FieldWrapper():
    field: dataclasses.Field
    prefix: str = ""
    _arg_options: Dict[str, Any] = dataclasses.field(init=False, default_factory=lambda: {})
    _docstring: Optional[docstring.AttributeDocString] = None
    _multiple: bool = dataclasses.field(init=False, default=False)

    # the argparse-related options:

    _option_strings: List[str] = dataclasses.field(init=False, default_factory=list, repr=False)
    _dest: List[str] = dataclasses.field(init=False, default_factory=list, repr=False)
    _nargs: Optional[Union[str, int]] = dataclasses.field(init=False, default=None, repr=False)
    _const: Optional[str] = dataclasses.field(init=False, default=None, repr=False)
    _default: Optional[Any] = dataclasses.field(init=False, default=None, repr=False)
    _type: Optional[Any] = dataclasses.field(init=False, default=None, repr=False)
    _choices: Optional[List[Any]] = dataclasses.field(init=False, default=None, repr=False)
    _required: bool = dataclasses.field(init=False, default=False, repr=False)
    _help: Optional[str] = dataclasses.field(init=False, default=None, repr=False)
    _metavar: Optional[str] = dataclasses.field(init=False, default=None, repr=False)
    
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Any, option_string: Optional[str] = None):
        pass

    @property
    def option_strings(self):
        return [f"--{self.name}"]

    @property
    def dest(self):
        return self._dest

    @property
    def nargs(self):
        return self._nargs

    @property
    def const(self):
        return self._const

    @property
    def default(self):
        return self._default

    @property
    def type(self):
        return self._type

    @property
    def choices(self):
        return self._choices
    
    @property
    def required(self) -> bool:
        if self._required is None:
            self._required = (
                self.field.default is dataclasses.MISSING and 
                self.field.default_factory is dataclasses.MISSING # type: ignore
            )
        return self._required
            
    
    @required.setter
    def required(self, value: bool):
        self._required = value

    @property
    def help(self):
        if self._docstring is not None:
            if self._docstring.docstring_below:
                arg_options["help"] = self._docstring.docstring_below
            elif self._docstring.comment_above:
                arg_options["help"] = self._docstring.comment_above
            elif self._docstring.comment_inline:
                arg_options["help"] = self._docstring.comment_inline
        return self._help

    @property
    def metavar(self):
        return self._metavar

    @property
    def name(self) -> str:
        return self.prefix + self.field.name
    
    
    @property
    def arg_options(self) -> Dict[str, Any]:
        if self._arg_options:
            return self._arg_options
        else:
            self._arg_options = self._get_arg_options()
            return self._arg_options 

    @property
    def is_dataclass(self):
        return dataclasses.is_dataclass(self.field.type)

    @property
    def is_tuple_or_list_of_dataclasses(self):
        return utils.is_tuple_or_list_of_dataclasses(self.field.type)

    @property
    def multiple(self) -> bool:
        return self._multiple

    @multiple.setter
    def multiple(self, value: bool):
        if value != self._multiple:
            self._arg_options.clear()
        self._multiple = value

    def _get_arg_options(self) -> Dict[str, Any]:
        f = self.field
        multiple = self.multiple

        if not f.init:
            return {}
        elif self.is_dataclass:
            return {}
        elif self.is_tuple_or_list_of_dataclasses:
            return {}

        name = self.name
        arg_options: Dict[str, Any] = { 
            "type": f.type,
        }

        
        if f.default is not dataclasses.MISSING:
            arg_options["default"] = f.default
        elif f.default_factory is not dataclasses.MISSING: # type: ignore
            arg_options["default"] = f.default_factory() # type: ignore
        else:
            arg_options["required"] = True

        if enum.Enum in f.type.mro():
            arg_options["choices"] = list(e.name for e in f.type)
            arg_options["type"] = str # otherwise we can't parse the enum, as we get a string.
            if "default" in arg_options:
                default_value = arg_options["default"]
                # if the default value is the Enum object, we make it a string
                if isinstance(default_value, enum.Enum):
                    arg_options["default"] = default_value.name
        
        elif utils.is_tuple_or_list(f.type):
            # Check if typing.List or typing.Tuple was used as an annotation, in which case we can automatically convert items to the desired item type.
            # NOTE: we only support tuples with a single type, for simplicity's sake. 
            T = utils.get_argparse_container_type(f.type)
            arg_options["nargs"] = "*"
            # arg_options["action"] = "append"
            if multiple:
                arg_options["type"] = utils._parse_multiple_containers(f.type)
            else:
                # TODO: Supporting the `--a '1 2 3'`, `--a [1,2,3]`, and `--a 1 2 3` at the same time is syntax is kinda hard, and I'm not sure if it's really necessary.
                # right now, we support --a '1 2 3' '4 5 6' and --a [1,2,3] [4,5,6] only when parsing multiple instances.
                # arg_options["type"] = utils._parse_container(f.type)
                arg_options["type"] = T
        
        elif f.type is bool:
            arg_options["default"] = False if f.default is dataclasses.MISSING else f.default
            arg_options["type"] = utils.str2bool
            arg_options["nargs"] = "*" if multiple else "?"
            if f.default is dataclasses.MISSING:
                arg_options["required"] = True
        
        if multiple:
            required = arg_options.get("required", False)
            if required:
                arg_options["nargs"] = "+"
            else:
                arg_options["nargs"] = "*"
                arg_options["default"] = [arg_options["default"]]

        return arg_options


@dataclasses.dataclass
class DataclassWrapper(Generic[Dataclass]):
    dataclass: Type[Dataclass]
    fields: List[FieldWrapper] = dataclasses.field(init=False, default_factory=list, repr=False)
    _multiple: bool = dataclasses.field(init=False, default=False)
    _required: bool = dataclasses.field(init=False, default=False)
    _prefix: str = dataclasses.field(init=False, default="")
    _children: List["DataclassWrapper"] = dataclasses.field(default_factory=list)
    _parent: Optional["DataclassWrapper"] = None
    _destinations: List[str] = dataclasses.field(default_factory=list)


    def __post_init__(self):
        for field in dataclasses.fields(self.dataclass):
            new_field_wrapper = FieldWrapper(field)
            try:
                new_field_wrapper._docstring = docstring.get_attribute_docstring(self.dataclass, field.name)
            except (SystemExit, Exception) as e:
                logging.warning("Couldn't find attribute docstring:", e)
                new_field_wrapper._docstring = docstring.AttributeDocString()
            self.fields.append(new_field_wrapper)

    @property
    def prefix(self) -> str:
        return self._prefix
    
    @prefix.setter
    def prefix(self, value: str):
        self._prefix = value
        for wrapped_field in self.fields:
            wrapped_field.prefix = value

    @property
    def required(self) -> bool:
        return self._required

    @required.setter
    def required(self, value: bool):
        self._required = value
        for wrapped_field in self.fields:
            wrapped_field.required = value

    @property
    def multiple(self) -> bool:
        return self._multiple

    @multiple.setter
    def multiple(self, value: bool):
        for wrapped_field in self.fields:
            wrapped_field.multiple = value
        self._multiple = value

    @property
    def descendants(self):
        for child in self._children:
            yield child
            yield from child.descendants

    def __iter__(self):
        yield self
        yield from self.descendants

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
