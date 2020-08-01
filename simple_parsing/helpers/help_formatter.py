import argparse
from ..logging_utils import get_logger
logger = get_logger(__file__)
from ..utils import get_type_arguments, is_optional, is_tuple_or_list, is_tuple, is_union, get_type_name
from typing import Type
from argparse import OPTIONAL, ZERO_OR_MORE, ONE_OR_MORE, REMAINDER, PARSER


class SimpleHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,
                          argparse.MetavarTypeHelpFormatter,
                          argparse.RawDescriptionHelpFormatter):
    """Little shorthand for using some useful HelpFormatters from argparse.
    
    This class inherits from argparse's `ArgumentDefaultHelpFormatter`,
    `MetavarTypeHelpFormatter` and `RawDescriptionHelpFormatter` classes.

    This produces the following resulting actions:
    - adds a "(default: xyz)" for each argument with a default
    - uses the name of the argument type as the metavar. For example, gives
      "-n int" instead of "-n N" in the usage and description of the arguments.
    - Conserves the formatting of the class and argument docstrings, if given.
    """
    
    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)

        if action.nargs is None:
            result = '%s' % get_metavar(1)
        elif action.nargs == OPTIONAL:
            result = '[%s]' % get_metavar(1)
        elif action.nargs == ZERO_OR_MORE:
            result = '[%s [%s ...]]' % get_metavar(2)
        elif action.nargs == ONE_OR_MORE:
            result = '%s [%s ...]' % get_metavar(2)
        elif action.nargs == REMAINDER:
            result = '...'
        elif action.nargs == PARSER:
            result = '%s ...' % get_metavar(1)
        else:
            formats = ['%s' for _ in range(action.nargs)]
            result = ' '.join(formats) % get_metavar(action.nargs)

        # print(f"Result: {result}, nargs: {action.nargs}")
        origin_type = getattr(action.type, "__origin_types__", None)
        # print("origin types: ", origin_type)
        if origin_type is not None:
            t = origin_type[0]
            if is_tuple(t):
                args = get_type_arguments(t)
                # print(f"args: {args}")
                metavars = []
                for arg in args:
                    if arg is Ellipsis:
                        metavars.append(f"[{metavars[-1]}, ...]")
                    else:
                        metavars.append(get_type_name(arg))
                # print(f"Metavars: {metavars}")
                return " ".join(metavars)
        return result
    
    def _get_default_metavar_for_optional(self, action: argparse.Action):
        try:
            return super()._get_default_metavar_for_optional(action)
        except BaseException as e:
            logger.debug(f"Getting metavar for action with dest {action.dest}.")
            metavar = self._get_metavar_for_action(action)
            logger.debug(f"Result metavar: {metavar}")
            return metavar

    def _get_default_metavar_for_positional(self, action: argparse.Action):
        try:
            return super()._get_default_metavar_for_positional(action)
        except BaseException as e:
            logger.debug(f"Getting metavar for action with dest {action.dest}.")
            metavar = self._get_metavar_for_action(action)
            logger.debug(f"Result metavar: {metavar}")
            return metavar

    def _get_metavar_for_action(self, action: argparse.Action) -> str:
        t = action.type
        return self._get_metavar_for_type(t)

    def _get_metavar_for_type(self, t: Type) -> str:
        logger.debug(f"Getting metavar for type {t}.")
        optional = is_optional(t)
        
        if hasattr(t, "__origin_field"):
            field = t.__origin_field
            print(field)
            assert False
            return t.__name__
        
        elif is_union(t):
            type_args = list(get_type_arguments(t))
            
            none_type = type(None)
            while none_type in type_args:  # type: ignore
                type_args.remove(none_type)  # type: ignore
            
            string = "[" if optional else ""
            middle = []
            for t_ in type_args:
                middle.append(self._get_metavar_for_type(t_))
            string += "|".join(middle)
            if optional:
                string += "]"
            return string
        else:
            return str(t)

Formatter = SimpleHelpFormatter
