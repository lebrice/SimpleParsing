import dataclasses
import enum
import logging
from typing import *
import argparse
import enum
from .. import docstring, utils
from ..utils import Dataclass, DataclassType

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
class FieldWrapper:
    field: dataclasses.Field
    parent: "DataclassWrapper" = dataclasses.field(repr=False)
    _required: Optional[bool] = None
    _docstring: Optional[docstring.AttributeDocString] = None
    _multiple: bool = False
    _default: Any = None
    _help: Optional[str] = None
    # the argparse-related options:
    _arg_options: Dict[str, Any] = dataclasses.field(init=False, default_factory=dict)
    
    def __post_init__(self):
        try:
            self._docstring = docstring.get_attribute_docstring(self.parent.dataclass, self.field.name)
        except (SystemExit, Exception) as e:
            logger.warning("Couldn't find attribute docstring:", e)
            self._docstring = docstring.AttributeDocString()

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Any, option_string: Optional[str] = None):
        logger.debug(f"Inside the 'call' of wrapper for {self.name}, values are {values}, option_string={option_string}")
        from simple_parsing import ArgumentParser
        from typing import cast
        parser: ArgumentParser = parser # type: ignore
        parser = cast(ArgumentParser, parser)

        logger.debug(f"destinations: {self.destinations}")
        if self.multiple:
            values = self.duplicate_if_needed(values)
            logger.debug(f"(replicated the parsed values: '{values}')")
        else:
            values = [values]

        logger.debug(f"destinations: {self.destinations}")
        for destination, value in zip(self.destinations, values):
            parent_dest, attribute = utils.parent_and_child(destination)
            logger.debug(f"Before processing the value: {value}")
            value = self.process(value)
            logger.debug(f"After processing the value: {value}")
            logger.debug(f"setting value of {value} in constructor arguments of parent at key '{parent_dest}' and attribute '{attribute}'")
            parser.constructor_arguments[parent_dest][attribute] = value # type: ignore
    
    def duplicate_if_needed(self, parsed_values: Any) -> List[Any]:
        num_instances_to_parse = len(self.destinations)
        logger.debug(f"Duplicating raw values. num to parse: {num_instances_to_parse}")
        logger.debug(f"(raw) parsed values: '{parsed_values}'")
        
        assert self.multiple
        assert num_instances_to_parse > 1, "multiple is true but we're expected to instantiate only one instance"
        
        if utils.is_list(self.field.type) and isinstance(parsed_values, tuple):
            parsed_values = list(parsed_values)

        if not isinstance(parsed_values, (list, tuple)):
            parsed_values = [parsed_values]

        if len(parsed_values) == num_instances_to_parse:
            return parsed_values
        elif len(parsed_values) == 1:
            return parsed_values * num_instances_to_parse
        else:
            raise utils.InconsistentArgumentError(
                f"The field '{self.name}' contains {len(parsed_values)} values, but either 1 or {num_instances_to_parse} values were expected."
            )
        return parsed_values

    def process(self, value: Any) -> Any:
        """TODO: apply any corrections from the 'raw' parsed values to the constructor arguments dict.
        
        Args:
            parsed_values (Any): [description]
        
        Returns:
            Any: [description]
        """
        if utils.is_enum(self.field.type):
            logger.debug(f"field postprocessing for Enum field '{self.name}' with value '{value}'")
            return self.process_enum(value)
        elif utils.is_tuple(self.field.type):
            # argparse always returns lists by default. If the field was of a Tuple type, we just transform the list to a Tuple.
            if not isinstance(value, tuple):
                return tuple(value)
        elif utils.is_list(self.field.type):
            if not isinstance(value, list):
                return list(value)
        elif utils.is_bool(self.field.type):
            if value is None and self.default is not None:
                print("value is None, returning opposite of default")
                return not self.default
            return value
        # elif utils.is_

        logger.debug(f"field postprocessing for field of unknown type '{self.field.type}' and of value '{value}'")
        return value

    def process_enum(self, value: Union[str, enum.Enum]):
        if isinstance(value, str):
            value = self.field.type[value]
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
        return [parent_dest + "." + self.name for parent_dest in self.parent.destinations]

    @property
    def option_strings(self):
        prefix: str = self.parent.prefix
        if prefix:
            return [f"--{prefix}{self.name}"]
        return [f"--{self.name}"]

    @property
    def dest(self) -> str:
        """
        TODO: It doesn't make much sense to use `dest` here, since we ultimately don't care
        where the attribute will be stored in the Namespace, we just want to set a value in
        the constructor arguments in the parser!
        """
        lineage = []
        parent: Optional[DataclassWrapper] = self.parent
        while parent is not None:
            lineage.append(parent.attribute_name)
            parent = parent._parent
        lineage = list(reversed(lineage))
        lineage.append(self.name)
        _dest = ".".join(lineage)
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
        elif self.field.default is not dataclasses.MISSING:
            return self.field.default
        elif self.field.default_factory is not dataclasses.MISSING: # type: ignore
            return self.field.default_factory() # type: ignore
        return None

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
    def required(self) -> bool:
        if self._required is not None:
            return self._required
        if self.parent and self.parent.required:
            self._required = True
        elif self.default is None:
            self._required = True
        else:
            self._required = False
        return self._required


    @required.setter
    def required(self, value: bool):
        self._required = value

    @property
    def help(self) -> Optional[str]:
        if self._help is not None:
            return self._help
        if self._docstring is not None:
            if self._docstring.docstring_below:
                self._help = self._docstring.docstring_below
            elif self._docstring.comment_above:
                self._help = self._docstring.comment_above
            elif self._docstring.comment_inline:
                self._help = self._docstring.comment_inline
        return self._help

    @help.setter
    def help(self, value: str):
        self._help = value

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

        _arg_options: Dict[str, Any] = {}
        _arg_options["type"] = self.field.type        
        _arg_options["help"] = self.help
        _arg_options["default"] = self.default
        _arg_options["required"] = self.required

        if enum.Enum in f.type.mro():
            _arg_options["choices"] = list(e.name for e in f.type)
            _arg_options["type"] = str # otherwise we can't parse the enum, as we get a string.
            if self.default is not None:
                # if the default value is the Enum object, we make it a string
                if isinstance(self.default, enum.Enum):
                    _arg_options["default"] = self.default.name
        
        elif utils.is_list(f.type):
            # Check if typing.List or typing.Tuple was used as an annotation, in which case we can automatically convert items to the desired item type.
            # NOTE: we only support tuples with a single type, for simplicity's sake. 
            T = utils.get_argparse_type_for_container(self.field.type)
            logging.debug(f"Adding a List attribute '{self.name}' with items of type '{T}'")
            _arg_options["nargs"] = "*"
            _arg_options["type"] = T
            if self.multiple:
                _arg_options["type"] = utils._parse_multiple_containers(self.field.type)
                _arg_options["type"].__name__ = "list_of_lists"
        

        elif utils.is_tuple(f.type):
            # NOTE: we only support tuples with a single type, for simplicity's sake. 
            T = utils.get_argparse_type_for_container(f.type)
            logging.debug(f"Adding a Tuple attribute '{self.name}' with items of type '{T}'")
            _arg_options["nargs"] = "*"
            # arg_options["action"] = "append"
            if multiple:
                _arg_options["type"] = utils._parse_multiple_containers(f.type)
                _arg_options["type"].__name__ = "list_of_lists"
            else:
                # TODO: Supporting the `--a '1 2 3'`, `--a [1,2,3]`, and `--a 1 2 3` at the same time is syntax is kinda hard, and I'm not sure if it's really necessary.
                # right now, we support --a '1 2 3' '4 5 6' and --a [1,2,3] [4,5,6] only when parsing multiple instances.
                # _arg_options["type"] = utils._parse_container(f.type)
                _arg_options["type"] = T
                # _arg_options["type"].__name__ = "container"

                
        elif f.type is bool:
            _arg_options["type"] = utils.str2bool
            if self.default is not None:
                _arg_options["nargs"] = "?"
            


        if multiple:
            required = _arg_options.get("required", False)
            default = _arg_options.get("default")
            if required:
                _arg_options["nargs"] = "+"
            else:
                _arg_options["nargs"] = "*"
                _arg_options["default"] = [default]

        return _arg_options

