import argparse
from ..logging_utils import get_logger
logger = get_logger(__file__)
from ..utils import get_type_arguments, is_optional, is_tuple_or_list, is_tuple, is_union
from typing import Type

i = 0
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
        print(get_metavar)
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
        return result

    def _get_default_metavar_for_optional(self, action: argparse.Action):
        default_metavar = super()._get_default_metavar_for_optional(action)
        try:
            logger.debug(f"Getting metavar for action with dest {action.dest}.")
            metavar = self._get_metavar_for_action(action)
            logger.debug(f"Result metavar: {metavar}")
        except BaseException as e:
            return default_metavar
        else:
            logger.debug(f"Both worked: {default_metavar}, {metavar}")
            return default_metavar

    def _get_default_metavar_for_positional(self, action: argparse.Action):
        default_metavar = super()._get_default_metavar_for_positional(action)
        try:
            logger.debug(f"Getting metavar for action with dest {action.dest}.")
            metavar = self._get_metavar_for_action(action)
            logger.debug(f"Result metavar: {metavar}")
        except BaseException as e:
            return default_metavar
        else:
            logger.debug(f"Both worked: {default_metavar}, {metavar}")
            return default_metavar

    def _get_metavar_for_action(self, action: argparse.Action) -> str:
        t = action.type
        global i
        i += 1
        print(f"called {i} times.")
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
