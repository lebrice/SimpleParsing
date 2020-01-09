import argparse
import dataclasses
import enum
import logging
from typing import *
from typing import cast

from .. import docstring, utils
from ..utils import Dataclass, DataclassType, T

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class FieldWrapper(Generic[T]):
    field: dataclasses.Field
    parent: Any = dataclasses.field(repr=False)
    _required: Optional[bool] = None
    _docstring: Optional[docstring.AttributeDocString] = None
    _multiple: bool = False
    _defaults: Optional[Union[T,List[T]]] = None
    _help: Optional[str] = None
    # the argparse-related options:
    _arg_options: Dict[str, Any] = dataclasses.field(init=False, default_factory=dict)
    
    def __post_init__(self):
        try:
            self._docstring = docstring.get_attribute_docstring(self.parent.dataclass, self.field.name)
        except (SystemExit, Exception) as e:
            logger.debug(f"Couldn't find attribute docstring: {e}")
            self._docstring = docstring.AttributeDocString()

    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: Any, option_string: Optional[str] = None):
        """Immitates a custom Action, which sets the corresponding value from `values` at the right destination in the `constructor_arguments` of the parser.
        
        # TODO: Could be simplified by removing unused arguments, if we decide that there is no real value in implementing a CustomAction class.

        Args:
            parser (argparse.ArgumentParser): the `simple_parsing.ArgumentParser` used.
            namespace (argparse.Namespace): (unused).
            values (Any): The parsed values for the argument.
            option_string (Optional[str], optional): (unused). Defaults to None.
        """
        from simple_parsing import ArgumentParser
        parser = cast(ArgumentParser, parser)
        
        logger.info(f"__call__ of field for destinations {self.destinations}, Namespace: {namespace}, values: {values}")
        
        if self.multiple:
            values = self.duplicate_if_needed(values)
            logger.debug(f"(replicated the parsed values: '{values}')")
        else:
            values = [values]

        for destination, value in zip(self.destinations, values):
            parent_dest, attribute = utils.split_parent_and_child(destination)
            value = self.postprocess(value)
            logger.debug(f"setting value of {value} in constructor arguments of parent at key '{parent_dest}' and attribute '{attribute}'")
            parser.constructor_arguments[parent_dest][attribute] = value # type: ignore
            logger.info(f"Constructor arguments so far: {parser.constructor_arguments}")
    
    def duplicate_if_needed(self, parsed_values: Any) -> List[Any]:
        """Duplicates the passed argument values if needed, such that each instance gets a value.

        For example, if we expected 3 values for an argument, and a single value was passed,
        then we duplicate it so that each of the three instances get the same value.
        
        Args:
            parsed_values (Any): The parsed value(s)
        
        Raises:
            utils.InconsistentArgumentError: If the number of arguments passed is inconsistent (neither 1 or the number of instances)
        
        Returns:
            List[Any]: The list of parsed values, of the right length.
        """
        num_instances_to_parse = len(self.destinations)
        logger.debug(f"Duplicating raw values. num to parse: {num_instances_to_parse}")
        logger.debug(f"(raw) parsed values: '{parsed_values}'")
        
        assert self.multiple
        assert num_instances_to_parse > 1, "multiple is true but we're expected to instantiate only one instance"
        
        if utils.is_list(self.field.type) and isinstance(parsed_values, tuple):
            parsed_values = list(parsed_values)

        if not self.is_tuple and not self.is_list and isinstance(parsed_values, list):
            nesting_level = utils.get_nesting_level(parsed_values)
            if nesting_level == 2 and len(parsed_values) == 1 and len(parsed_values[0]) == num_instances_to_parse:
                return parsed_values[0]

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

    def postprocess(self, raw_parsed_value: Any) -> Any:
        """Applies any conversions to the 'raw' parsed value before it is used in the constructor of the dataclass.
        
        Args:
            raw_parsed_value (Any): The 'raw' parsed value.
        
        Returns:
            Any: The processed value
        """
        if self.is_enum:
            logger.debug(f"field postprocessing for Enum field '{self.name}' with value: {raw_parsed_value}'")
            if isinstance(raw_parsed_value, str):
                raw_parsed_value = self.field.type[raw_parsed_value]
            return raw_parsed_value

        elif self.is_tuple:
            # argparse always returns lists by default. If the field was of a Tuple type, we just transform the list to a Tuple.
            if not isinstance(raw_parsed_value, tuple):
                return tuple(raw_parsed_value)

        elif self.is_bool:
            if raw_parsed_value is None and self.defaults is not None:
                logger.debug("value is None, returning opposite of default")
                return not self.defaults
            return raw_parsed_value

        elif self.is_list:
            return list(raw_parsed_value)

        elif self.field.type not in utils.builtin_types:
            try:
                # if the field has a weird type, we try to call it directly.
                return self.field.type(raw_parsed_value)
            except Exception as e:
                logger.warning(
                    f"Unable to instantiate the field '{self.name}' of type '{self.field.type}' by using the type as a constructor. "
                    f"Returning the raw parsed value instead ({raw_parsed_value}, of type {type(raw_parsed_value)}). (Caught Exception: {e})"
                )
                return raw_parsed_value

        logger.debug(f"field postprocessing for field of type '{self.field.type}' and with value '{raw_parsed_value}'")
        return raw_parsed_value

       
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
    def option_strings(self) -> List[str]:
        prefix: str = self.parent.prefix
        return [f"--{prefix}{self.name}"]

    @property
    def dest(self) -> str:
        """
        TODO: It doesn't make much sense to use `dest` here, since we ultimately don't care
        where the attribute will be stored in the Namespace, we just want to set a value in
        the constructor arguments in the parser!
        """
        lineage = []
        parent = self.parent
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
    def defaults(self) -> Optional[Union[Any, List[Any]]]:
        # if self._default is not None:
        #     return self._default
        if self.parent.defaults:
            self._defaults = [getattr(default, self.name) for default in self.parent.defaults]
            if not self.multiple and self._defaults:
                self._defaults = self._defaults[0]    
        else:
            self._defaults = utils.default_value(self.field)
        return self._defaults

    @defaults.setter
    def defaults(self, value: Any):
        self._defaults = value

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
        elif self.defaults is None:
            self._required = True
        # elif isinstance(self.defaults, list) and not self.defaults:
        #     self._required = True
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

        assert not dataclasses.is_dataclass(self.field.type), "Shouldn't have created a FieldWrapper for a dataclass in the first place!"
        assert not utils.is_tuple_or_list_of_dataclasses(self.field.type), "Shouldn't have created a FieldWrapper for a list of dataclasses in the first place!"

        _arg_options: Dict[str, Any] = {}
        # TODO: should we explicitly use `str` whenever the type isn't a builtin type? or try to use it as a constructor?
        _arg_options["type"] = self.field.type
        _arg_options["help"] = self.help
        _arg_options["default"] = self.defaults
        _arg_options["required"] = self.required
        _arg_options["dest"] = self.dest
        
        if self.is_enum:
            # we actually parse enums as string, and convert them back to enums in the `process` method.
            _arg_options["choices"] = list(e.name for e in f.type)
            _arg_options["type"] = str 
            # if the default value is an Enum, we convert it to a string.
            if self.defaults:
                enum_to_str = lambda e: e.name if isinstance(e, enum.Enum) else e
                if not self.multiple:                
                    _arg_options["default"] = enum_to_str(self.defaults)
                else:
                    _arg_options["default"] = [enum_to_str(default) for default in self.defaults]
        
        elif self.is_choice:
            _arg_options["choices"] = self.field.metadata["choices"]

        elif self.is_list:
            # Check if typing.List or typing.Tuple was used as an annotation, in which case we can automatically convert items to the desired item type.
            T = utils.get_argparse_type_for_container(self.field.type)
            logger.debug(f"Adding a List attribute '{self.name}' with items of type '{T}'")
            _arg_options["nargs"] = "*"
            _arg_options["type"] = T

            if self.multiple:
                _arg_options["type"] = utils._parse_multiple_containers(self.field.type)
                _arg_options["type"].__name__ = utils.get_type_name(f.type)

        elif self.is_tuple:
            T = utils.get_argparse_type_for_container(self.field.type)
            logging.debug(f"Adding a Tuple attribute '{self.name}' with items of type '{T}'")
            _arg_options["nargs"] = utils.get_container_nargs(f.type)
            _arg_options["type"] = utils._parse_container(f.type)

            if self.multiple:
                type_arguments = utils.get_type_arguments(f.type)
                _arg_options["type"] = utils._parse_multiple_containers(f.type)
                _arg_options["type"].__name__ = utils.get_type_name(f.type)
        
        elif f.type is bool:
            _arg_options["type"] = utils.str2bool
            if self.defaults is not None:
                _arg_options["nargs"] = "?"
            
        if self.multiple:
            if self.required:
                _arg_options["nargs"] = "+"
            else:
                _arg_options["nargs"] = "*"

        return _arg_options

    @property
    def is_list(self):
        return utils.is_list(self.field.type)
    
    @property
    def is_enum(self):
        return utils.is_enum(self.field.type)

    @property
    def is_choice(self):
        return self.field.metadata and "choices" in self.field.metadata

    @property
    def is_tuple(self):
        return utils.is_tuple(self.field.type)
    
    @property
    def is_bool(self):
        return utils.is_bool(self.field.type)
