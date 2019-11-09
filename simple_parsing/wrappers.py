import dataclasses
import enum
import logging
from typing import *
import argparse
from . import docstring, utils

T = TypeVar("T")
Dataclass = TypeVar("Dataclass")

@dataclasses.dataclass
class FieldWrapper():
    field: dataclasses.Field
    dataclass: dataclasses.InitVar[Type]
    _arg_options: Dict[str, Any] = dataclasses.field(init=False, default_factory=lambda: {})
    _docstring: Optional[docstring.AttributeDocString] = None

    _multiple: bool = dataclasses.field(init=False, default=False)

    def __post_init__(self, dataclass: Type[Dataclass]):
        self._docstring = docstring.get_attribute_docstring(dataclass, self.field.name)

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
        elif dataclasses.is_dataclass(f.type):
            return {}
        elif utils.is_tuple_or_list_of_dataclasses(f.type):
            return {}

        name = f"--{f.name}"
        arg_options: Dict[str, Any] = { 
            "type": f.type,
        }

        if self._docstring is not None:
            if self._docstring.docstring_below:
                arg_options["help"] = self._docstring.docstring_below
            elif self._docstring.comment_above:
                arg_options["help"] = self._docstring.comment_above
            elif self._docstring.comment_inline:
                arg_options["help"] = self._docstring.comment_inline
        
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
    parser: argparse.ArgumentParser
    fields: List[FieldWrapper] = dataclasses.field(init=False, default_factory=list)
    _multiple: bool = dataclasses.field(init=False, default=False)
    
    def __post_init__(self):
        for field in dataclasses.fields(self.dataclass):
            self.fields.append(FieldWrapper(field, self.dataclass))

    @property
    def multiple(self) -> bool:
        return self._multiple

    @multiple.setter
    def multiple(self, value: bool):
        print("Seting multiple to ", value)
        for wrapped_field in self.fields:
            wrapped_field.multiple = value
        self._multiple = value

    def instantiate(self, args: Union[Dict[str, Any], argparse.Namespace], num_instances_to_parse: int = 1) -> List[Dataclass]:
        """Creates instances of the dataclass using results of `parser.parse_args()`"""
        args_dict: Dict[str, Any] = vars(args) if isinstance(args, argparse.Namespace) else args
        instances: List[Dataclass] = []
        dataclass: Type[Dataclass] = self.dataclass

        logging.debug(dataclass, args_dict, num_instances_to_parse)
        logging.debug(f"args: {args}")
        
        if self.multiple:
            assert num_instances_to_parse > 1, "multiple is true but we're expected to instantiate only one instance"
        else:
            assert num_instances_to_parse == 1, "multiple is false but we're expected to instantiate more than one instance"

        for i in range(num_instances_to_parse):
            constructor_arguments: Dict[str, Union[Any, List]] = {}
            for wrapped_field in self.fields:
                f = wrapped_field.field
                if not f.init:
                    continue

                if wrapped_field.is_dataclass:
                    print("The wrapped field is a dataclass. continuing?")
                    continue

                assert not wrapped_field.is_tuple_or_list_of_dataclasses, "Shouldn't have been allowed"
                    
                assert f.name in args_dict, f"{f.name} is not in the arguments dict: {args_dict}"
                
                value = args_dict[f.name]

                if self.multiple:
                    assert isinstance(value, list), f"all fields should have gotten a list default value... ({value})"
                    if len(value) == 1:
                        constructor_arguments[f.name] = value[0]
                    elif len(value) == num_instances_to_parse:
                        constructor_arguments[f.name] = value[i]
                    else:
                        raise utils.InconsistentArgumentError(
                            f"The field '{f.name}' contains {len(value)} values, but either 1 or {num_instances_to_parse} values were expected."
                        )
                else:
                    constructor_arguments[f.name] = value

            instances.append(self._instantiate_dataclass(constructor_arguments))
                    
        return instances

    def _instantiate_dataclass(self, args: Union[Dict[str, Any], argparse.Namespace]) -> Dataclass:
        """Creates an instance of the dataclass using results of `parser.parse_args()`"""
        args_dict = vars(args) if isinstance(args, argparse.Namespace) else args
        print(f"args dict: {args_dict}")
        
        dataclass = self.dataclass
        constructor_args: Dict[str, Any] = {}

        for wrapped_field in self.fields:
            f = wrapped_field.field
            if not f.init:
                continue
            
            if wrapped_field.is_dataclass:
                print("Can't instantiate the child from within the parent, can I?")
                continue
                # child_dataclass = f.type
                # constructor_args[f.name] = self._instantiate_dataclass(f.type, args_dict)
            
            elif utils.is_tuple_or_list_of_dataclasses(f.type):
                raise RuntimeError("Shouldn't have attributes that are containers of dataclasses!")

            elif enum.Enum in f.type.mro():
                constructor_args[f.name] = f.type[args_dict[f.name]]
            
            elif utils.is_tuple(f.type):
                constructor_args[f.name] = tuple(args_dict[f.name])
            
            elif utils.is_list(f.type):
                constructor_args[f.name] = list(args_dict[f.name])

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
                constructor_args[f.name] = args_dict[f.name]

        instance: T = dataclass(**constructor_args) #type: ignore
        return instance


