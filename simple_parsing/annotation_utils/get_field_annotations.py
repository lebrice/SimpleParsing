import collections
import inspect
import sys
import types
import typing
from contextlib import contextmanager
from dataclasses import InitVar
from itertools import dropwhile
from logging import getLogger as get_logger
from typing import Any, Dict, Iterator, Optional, get_type_hints

logger = get_logger(__name__)

# NOTE: This dict is used to enable forward compatibility with things such as `tuple[int, str]`,
# `list[float]`, etc. when using `from __future__ import annotations`.
forward_refs_to_types = {
    "tuple": typing.Tuple,
    "set": typing.Set,
    "dict": typing.Dict,
    "list": typing.List,
    "type": typing.Type,
}


@contextmanager
def _initvar_patcher() -> Iterator[None]:
    """Patch InitVar to not fail when annotations are postponed.

    `TypeVar('Forward references must evaluate to types. Got dataclasses.InitVar[tp].')` is raised
    when postponed annotations are enabled and `get_type_hints` is called
    Bug is mentioned here https://github.com/python/cpython/issues/88962
    In python 3.11 this is fixed, but backport fix is not planned for old releases

    Workaround is mentioned here https://stackoverflow.com/q/70400639
    """
    if sys.version_info[:2] < (3, 11):
        InitVar.__call__ = lambda *args: None
    yield
    if sys.version_info[:2] < (3, 11):
        del InitVar.__call__


def evaluate_string_annotation(annotation: str, containing_class: Optional[type] = None) -> type:
    """Attempts to evaluate the given annotation string, to get a 'live' type annotation back.

    Any exceptions that are raised when evaluating are raised directly as-is.

    NOTE: This is probably not 100% safe. I mean, if the user code puts urls and stuff in their
    type annotations, and then uses simple-parsing, then sure, that code might get executed. But
    I don't think it's my job to prevent them from shooting themselves in the foot, you know what I
    mean?
    """
    # The type of the field might be a string when using `from __future__ import annotations`.
    # Get the local and global namespaces to pass to the `get_type_hints` function.
    local_ns: Dict[str, Any] = {"typing": typing, **vars(typing)}
    local_ns.update(forward_refs_to_types)
    global_ns = {}
    if containing_class:
        # Get the globals in the module where the class was defined.
        global_ns = sys.modules[containing_class.__module__].__dict__

    if "|" in annotation:
        annotation = _get_old_style_annotation(annotation)
    evaluated_t: type = eval(annotation, local_ns, global_ns)
    return evaluated_t


def _replace_UnionType_with_typing_Union(annotation):
    from simple_parsing.utils import builtin_types, is_dict, is_list, is_tuple

    if sys.version_info[:2] < (3, 10):
        # This is only useful for python 3.10+ (where UnionTypes exist).
        # Therefore just return the annotation as-is.
        return annotation

    if isinstance(annotation, types.UnionType):  # type: ignore
        union_args = typing.get_args(annotation)
        new_union_args = tuple(_replace_UnionType_with_typing_Union(arg) for arg in union_args)
        return typing.Union[new_union_args]  # type: ignore
    if is_list(annotation):
        item_annotation = typing.get_args(annotation)[0]
        new_item_annotation = _replace_UnionType_with_typing_Union(item_annotation)
        return typing.List[new_item_annotation]
    if is_tuple(annotation):
        item_annotations = typing.get_args(annotation)
        new_item_annotations = tuple(
            _replace_UnionType_with_typing_Union(arg) for arg in item_annotations
        )
        return typing.Tuple[new_item_annotations]  # type: ignore
    if is_dict(annotation):
        annotations = typing.get_args(annotation)
        if not annotations:
            return typing.Dict
        assert len(annotations) == 2
        key_annotation = annotations[0]
        value_annotation = annotations[1]
        new_key_annotation = _replace_UnionType_with_typing_Union(key_annotation)
        new_value_annotation = _replace_UnionType_with_typing_Union(value_annotation)
        return typing.Dict[new_key_annotation, new_value_annotation]
    if annotation in builtin_types:
        return annotation
    if inspect.isclass(annotation):
        return annotation
    raise NotImplementedError(annotation)


#     # return forward_refs_to_types.get(ann, local_ns.get(ann, global_ns.get(ann, getattr(builtins, ann, ann))))


def _not_supported(annotation) -> typing.NoReturn:
    raise NotImplementedError(f"Don't yet support annotations like this: {annotation}")


def _get_old_style_annotation(annotation: str) -> str:
    """Replaces A | B with Union[A,B] in the annotation."""
    # TODO: Add proper support for things like `list[int | float]`, which isn't currently
    # working, even without the new-style union.
    if "|" not in annotation:
        return annotation

    annotation = annotation.strip()
    if "[" not in annotation:
        assert "]" not in annotation
        return "Union[" + ", ".join(v.strip() for v in annotation.split("|")) + "]"

    before, lsep, rest = annotation.partition("[")
    middle, rsep, after = rest.rpartition("]")
    # BUG: Need to handle things like bob[int] | None
    assert (
        not after.strip()
    ), f"can't have text at HERE in <something>[<something>]<HERE>!: {annotation}"

    if "|" in before or "|" in after:
        _not_supported(annotation)
    assert "|" in middle

    if "," in middle:
        parts = [v.strip() for v in middle.split(",")]
        parts = [_get_old_style_annotation(part) for part in parts]
        middle = ", ".join(parts)

    new_middle = _get_old_style_annotation(annotation=middle)
    new_annotation = before + lsep + new_middle + rsep + after
    return new_annotation


def _replace_new_union_syntax_with_old_union_syntax(
    annotations_dict: Dict[str, str], context: collections.ChainMap
) -> Dict[str, Any]:
    new_annotations = annotations_dict.copy()
    for field, annotation_str in annotations_dict.items():
        updated_annotation = _get_old_style_annotation(annotation_str)
        new_annotations[field] = updated_annotation

    return new_annotations


def get_field_type_from_annotations(some_class: type, field_name: str) -> type:
    """Get the annotation for the given field, in the 'old-style' format with types from
    typing.List, typing.Union, etc.

    If the script uses `from __future__ import annotations`, and we are in python<3.9,
    Then we need to actually first make this forward-compatibility 'patch' so that we
    don't run into a "`type` object is not subscriptable" error.

    NOTE: If you get errors of this kind from the function below, then you might want to add an
    entry to the `forward_refs_to_types` dict above.
    """

    # Pretty hacky: Modify the type annotations of the class (preferably a copy of the class
    # if possible, to avoid modifying things in-place), and replace  the `a | b`-type
    # expressions with `Union[a, b]`, so that `get_type_hints` doesn't raise an error.
    # The type of the field might be a string when using `from __future__ import annotations`.

    # The type of the field might be a string when using `from __future__ import annotations`.
    # Get the local and global namespaces to pass to the `get_type_hints` function.
    local_ns: Dict[str, Any] = {"typing": typing, **vars(typing)}
    local_ns.update(forward_refs_to_types)

    # NOTE: Get the local namespace of the calling function / module where this class is defined,
    # and use it to get the correct type of the field, if it is a forward reference.
    frame = inspect.currentframe()
    # stack = []
    while frame.f_back is not None and frame.f_locals.get(some_class.__name__) is not some_class:
        # stack.append(frame)
        frame = frame.f_back
    # Found the frame with the dataclass definition. Update the locals. This makes it possible to
    # use dataclasses defined in local scopes!
    if frame is not None:
        local_ns.update(frame.f_locals)

    # Get the global_ns in the module starting from the deepest base until the module with the field_name last definition.
    global_ns = {}
    classes_to_iterate = list(
        dropwhile(
            lambda cls: field_name not in getattr(cls, "__annotations__", {}), some_class.mro()
        )
    )
    for base_cls in reversed(classes_to_iterate):
        global_ns.update(sys.modules[base_cls.__module__].__dict__)

    try:
        with _initvar_patcher():
            annotations_dict = get_type_hints(some_class, localns=local_ns, globalns=global_ns)
    except TypeError:
        annotations_dict = collections.ChainMap(
            *[getattr(cls, "__annotations__", {}) for cls in some_class.mro()]
        )

    if field_name not in annotations_dict:
        raise ValueError(f"Field {field_name} not found in annotations of class {some_class}")

    field_type = annotations_dict[field_name]

    if sys.version_info[:2] >= (3, 7) and isinstance(field_type, typing.ForwardRef):
        # Weird bug happens when mixing postponed evaluation of type annotations + forward
        # references: The ForwardRefs are left as-is, and not evaluated!
        forward_arg = field_type.__forward_arg__
        field_type = forward_arg

    if sys.version_info >= (3, 10) and isinstance(field_type, types.UnionType):
        # In python >= 3.10, int | float is allowed. Therefore, just to be consistent, we want
        # to convert those into the corresponding typing.Union type.
        # This is necessary for the rest of the code to work, since it's all based on typing.Union.
        field_type = _replace_UnionType_with_typing_Union(field_type)

    if isinstance(field_type, str) and "|" in field_type:
        field_type = _get_old_style_annotation(field_type)

        # Pretty hacky:
        # In order to use `get_type_hints`, we need to pass it a class. We can't just ask it to
        # evaluate a single annotation. Therefore, we create a temporary class and set it's
        # __annotation__ attribute, which is introspected by `get_type_hints`.

    try:

        class Temp_:
            pass

        Temp_.__annotations__ = {field_name: field_type}
        with _initvar_patcher():
            annotations_dict = get_type_hints(Temp_, globalns=global_ns, localns=local_ns)
        field_type = annotations_dict[field_name]
    except Exception:
        logger.warning(
            f"Unable to evaluate forward reference {field_type} for field '{field_name}'.\n"
            f"Leaving it as-is."
        )
        field_type = field_type

    return field_type
