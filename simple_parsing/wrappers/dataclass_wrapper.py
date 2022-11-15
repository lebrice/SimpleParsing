from __future__ import annotations

import argparse
import dataclasses
import sys
from dataclasses import MISSING
from logging import getLogger
from typing import cast

from .. import docstring, utils
from ..utils import Dataclass
from .field_wrapper import FieldWrapper
from .wrapper import Wrapper

logger = getLogger(__name__)


class DataclassWrapper(Wrapper[Dataclass]):
    def __init__(
        self,
        dataclass: type[Dataclass],
        name: str,
        default: Dataclass | dict = None,
        prefix: str = "",
        parent: DataclassWrapper | None = None,
        _field: dataclasses.Field | None = None,
        field_wrapper_class: type[FieldWrapper] = FieldWrapper,
    ):
        # super().__init__(dataclass, name)
        self.dataclass = dataclass
        self._name = name
        self._default = default
        self.prefix = prefix

        self.fields: list[FieldWrapper] = []
        self._destinations: list[str] = []
        self._required: bool = False
        self._explicit: bool = False
        self._dest: str = ""
        self._children: list[DataclassWrapper] = []
        self._parent = parent
        # the field of the parent, which contains this child dataclass.
        self._field = _field

        # the default values
        self._defaults: list[Dataclass] = []

        if default:
            self.defaults = [default]
        self.optional: bool = False

        # NOTE: `dataclasses.fields` method retrieves only `dataclasses._FIELD`
        # NOTE: but we also want to know about `dataclasses._FIELD_INITVAR`
        # NOTE: therefore we partly copy-paste its implementation
        if sys.version_info[:2] < (3, 8):
            # Before 3.8 `InitVar[tp] is InitVar` so it's impossible to retrieve field type
            # therefore we should skip it just to be fully backward compatible
            dataclass_fields = dataclasses.fields(self.dataclass)
        else:
            try:
                dataclass_fields_map = getattr(self.dataclass, dataclasses._FIELDS)
            except AttributeError:
                raise TypeError("must be called with a dataclass type or instance")
            dataclass_fields = tuple(
                field
                for field in dataclass_fields_map.values()
                if field._field_type in (dataclasses._FIELD, dataclasses._FIELD_INITVAR)
            )

        for field in dataclass_fields:
            if not field.init or field.metadata.get("cmd", True) is False:
                # Don't add arguments for these fields.
                continue
            field_default = getattr(default, field.name, None)
            if isinstance(field.type, str):
                # NOTE: Here we'd like to convert the fields type to an actual type, in case the
                # `from __future__ import annotations` feature is used.
                from simple_parsing.annotation_utils.get_field_annotations import (
                    get_field_type_from_annotations,
                )

                field_type = get_field_type_from_annotations(self.dataclass, field.name)
                # Modify the `type` of the Field object, in-place.
                field.type = field_type

            if utils.is_subparser_field(field) or utils.is_choice(field):
                wrapper = field_wrapper_class(field, parent=self, prefix=prefix)
                self.fields.append(wrapper)

            elif utils.is_tuple_or_list_of_dataclasses(field.type):
                raise NotImplementedError(
                    f"Field {field.name} is of type {field.type}, which isn't "
                    f"supported yet. (container of a dataclass type)"
                )

            elif dataclasses.is_dataclass(field.type) and field.default is not None:
                # handle a nested dataclass attribute
                dataclass, name = field.type, field.name
                child_wrapper = DataclassWrapper(
                    dataclass,
                    name,
                    parent=self,
                    _field=field,
                    default=field_default,
                )
                self._children.append(child_wrapper)

            elif utils.contains_dataclass_type_arg(field.type):
                field_dataclass = utils.get_dataclass_type_arg(field.type)
                child_wrapper = DataclassWrapper(
                    field_dataclass,
                    name=field.name,
                    parent=self,
                    _field=field,
                    default=field_default,
                )
                child_wrapper.required = False
                child_wrapper.optional = True
                self._children.append(child_wrapper)

            else:
                # a normal attribute
                field_wrapper = field_wrapper_class(field, parent=self, prefix=self.prefix)
                logger.debug(
                    f"wrapped field at {field_wrapper.dest} has a default value of {field_wrapper.default}"
                )
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

            # if wrapped_field.is_subgroup:
            #     pass  # What to do in that case? Just add it like a regular `choice` argument?
            # wrapped_field.add_subparsers(parser)

            elif wrapped_field.arg_options:
                options = wrapped_field.arg_options
                if argparse.SUPPRESS in self.defaults:
                    options["default"] = argparse.SUPPRESS

                logger.debug(f"Arg options for field '{wrapped_field.name}': {options}")
                group.add_argument(*wrapped_field.option_strings, **options)

    def equivalent_argparse_code(self, leading="group") -> str:
        code = ""
        import textwrap

        code += textwrap.dedent(
            f"""
        group = parser.add_argument_group(title="{self.title.strip()}", description="{self.description.strip()}")
        """
        )
        for wrapped_field in self.fields:
            if wrapped_field.is_subparser:
                # TODO:
                raise NotImplementedError("Subparsers equivalent is TODO.")
                code += textwrap.dedent(
                    f"""\
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
                """
                )
            elif wrapped_field.arg_options:
                code += textwrap.dedent(wrapped_field.equivalent_argparse_code()) + "\n"
        return code

    @property
    def name(self) -> str:
        return self._name

    @property
    def parent(self) -> DataclassWrapper | None:
        return self._parent

    @property
    def defaults(self) -> list[Dataclass]:
        if self._defaults:
            return self._defaults
        if self._field is None:
            return []
        assert self.parent is not None
        if self.parent.defaults:
            self._defaults = []
            for default in self.parent.defaults:
                if default not in (None, argparse.SUPPRESS):
                    default = getattr(default, self.name)
                self._defaults.append(default)
        else:
            default_field_value = utils.default_value(self._field)
            if default_field_value is MISSING:
                self._defaults = []
            else:
                self._defaults = [default_field_value]
        return self._defaults

    @defaults.setter
    def defaults(self, value: list[Dataclass]):
        self._defaults = value

    @property
    def default(self) -> Dataclass | None:
        return self._default

    @default.setter
    def default(self, value: Dataclass | dict):
        if value is None:
            self._default = value
            return
        if not isinstance(value, dict):
            self._default = value
            value = dataclasses.asdict(value)
        for field_wrapper in self.fields:
            if field_wrapper.name in value:
                field_wrapper.default = value[field_wrapper.name]
        for nested_dataclass_wrapper in self._children:
            if nested_dataclass_wrapper.name in value:
                nested_dataclass_wrapper.default = value[nested_dataclass_wrapper.name]

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
    def destinations(self) -> list[str]:
        if not self._destinations:
            if self.parent:
                self._destinations = [f"{d}.{self.name}" for d in self.parent.destinations]
            else:
                self._destinations = [self.name]
        return self._destinations

    @destinations.setter
    def destinations(self, value: list[str]):
        self._destinations = value

    def merge(self, other: DataclassWrapper):
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
