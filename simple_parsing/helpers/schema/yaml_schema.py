from __future__ import annotations

import copy
import dataclasses
import json
from dataclasses import dataclass
from logging import getLogger as get_logger
from pathlib import Path
from typing import Any, TypeVar

from typing_extensions import TypeGuard

from simple_parsing.docstring import get_attribute_docstring, inspect_getdoc
from simple_parsing.helpers.serialization.serializable import dump_yaml
from simple_parsing.utils import Dataclass, PossiblyNestedDict, is_dataclass_type

logger = get_logger(__name__)


@dataclass
class Bob:
    """Some docstring."""

    foo: int = 123
    """A very important field."""


@dataclass
class Nested:
    bob: Bob
    other_field: str


def save_yaml_with_schema(
    dc: Dataclass,
    path: Path,
    repo_root: Path | None = Path.cwd(),
    generated_schemas_dir: Path | None = None,
    gitignore_schemas: bool = True,
) -> None:
    try:
        import pydantic
    except ModuleNotFoundError:
        logger.error("pydantic is required for this feature.")
        raise

    json_schema = pydantic.TypeAdapter(type(dc)).json_schema(mode="serialization")
    # Add field docstrings as descriptions in the schema!
    json_schema = _update_schema_with_descriptions(dc, json_schema=json_schema)

    dc_schema_filename = f"{type(dc).__qualname__}_schema.json"

    if generated_schemas_dir is None:
        # Defaults to saving in a .schemas folder next to the config yaml file.
        generated_schemas_dir = path.parent / ".schemas"
    generated_schemas_dir.mkdir(exist_ok=True, parents=True)

    if repo_root:
        repo_root, _ = _try_make_relative(repo_root, relative_to=Path.cwd())
        generated_schemas_dir, _ = _try_make_relative(generated_schemas_dir, relative_to=repo_root)

    if gitignore_schemas:
        # Add a .gitignore in the schemas dir so the schema files aren't tracked by git.
        _write_gitignore_file_for_schemas(generated_schemas_dir)

    schema_file = generated_schemas_dir / dc_schema_filename
    schema_file.write_text(json.dumps(json_schema, indent=2))

    # Try to write out a relative path to the schema if possible, because we wouldn't want to
    # include the absolute paths (e.g. /home/my_user/...) into the config yaml file.
    schema_file, success = _try_make_relative(schema_file, path.parent)
    if success:
        # The schema is saved in a file relative to the config file, so we just embed the
        # *relative* path to the schema as a comment in the first line of the yaml file.
        _write_yaml_with_schema_header(dc, path=path, schema_file=schema_file)
        return

    if repo_root is None or not (vscode_dir := repo_root / ".vscode").exists():
        nameof_generated_schemas_dir = f"{generated_schemas_dir=}".partition("=")[0]
        logger.warning(
            f"Writing the dataclass to a config file at {path} that will include an absolute path "
            f"to the schema file. To avoid this, set {nameof_generated_schemas_dir} to `None` or "
            f"to a relative path with respect to {path.parent}."
        )
        _write_yaml_with_schema_header(dc, path=path, schema_file=schema_file)
        return

    # Alternatively: we can also use a setting in the VsCode editor to associate a schema file with
    # a list of config files.

    vscode_settings_file = vscode_dir / "settings.json"
    try:
        vscode_settings: dict[str, Any] = json.loads(vscode_settings_file.read_text())
    except json.decoder.JSONDecodeError:
        return

    yaml_schemas: dict[str, str | list[str]] = vscode_settings.setdefault("yaml.schemas", {})

    schema_key = str(schema_file.relative_to(repo_root))
    try:
        path_to_add = str(path.relative_to(repo_root))
    except ValueError:
        path_to_add = str(path)

    files_associated_with_schema: str | list[str] = yaml_schemas.get(schema_key, [])
    if isinstance(files_associated_with_schema, str):
        existing_value = files_associated_with_schema
        files_associated_with_schema = sorted(set([existing_value, path_to_add]))
    else:
        files_associated_with_schema = sorted(set(files_associated_with_schema + [path_to_add]))
    yaml_schemas[schema_key] = files_associated_with_schema

    vscode_settings_file.write_text(json.dumps(vscode_settings, indent=2))


def _write_yaml_with_schema_header(dc: Dataclass, path: Path, schema_file: Path):
    with path.open("w") as f:
        f.write(f"# yaml-language-server: $schema={schema_file}\n")
        dump_yaml(dc, f)


def _try_make_relative(p: Path, relative_to: Path) -> tuple[Path, bool]:
    try:
        return p.relative_to(relative_to), True
    except ValueError:
        return p, False


def _write_gitignore_file_for_schemas(generated_schemas_dir: Path):
    gitignore_file = generated_schemas_dir / ".gitignore"
    if gitignore_file.exists():
        gitignore_entries = [
            stripped_line
            for line in gitignore_file.read_text().splitlines()
            if (stripped_line := line.strip())
        ]
    else:
        gitignore_entries = []
    schema_filename_pattern = "*_schema.json"
    if schema_filename_pattern not in gitignore_entries:
        gitignore_entries.append(schema_filename_pattern)
    gitignore_file.write_text("\n".join(gitignore_entries) + "\n")


def _has_default_dataclass_docstring(dc_type: type[Dataclass]) -> bool:
    docstring: str | None = inspect_getdoc(dc_type)
    return bool(docstring) and docstring.startswith(f"{dc_type.__name__}(")


def _update_schema_with_descriptions(
    dc: Dataclass, json_schema: PossiblyNestedDict[str, str | list[str]], inplace: bool = True
):
    if not inplace:
        json_schema = copy.deepcopy(json_schema)

    definitions = json_schema["$defs"]
    assert isinstance(definitions, dict)
    for classname, definition in definitions.items():
        if classname == type(dc).__name__:
            definition_dc_type = type(dc)
        else:
            # Get the dataclass type has this classname.
            definition_dc_type = globals().get(classname)
            if not is_dataclass_type(definition_dc_type):
                continue

        assert isinstance(definition, dict)
        _update_definition_in_schema_using_dc(definition, dc_type=definition_dc_type)

    return json_schema


K = TypeVar("K")
V = TypeVar("V")


def is_possibly_nested_dict(
    some_dict: Any, k_type: type[K], v_type: type[V]
) -> TypeGuard[PossiblyNestedDict[K, V]]:
    return isinstance(some_dict, dict) and all(
        isinstance(k, k_type)
        and (isinstance(v, v_type) or is_possibly_nested_dict(v, k_type, v_type))
        for k, v in some_dict.items()
    )


def _update_definition_in_schema_using_dc(definition: dict[str, Any], dc_type: type[Dataclass]):
    # If the class has a docstring that isn't the default one generated by dataclasses, add a
    # description.
    docstring = inspect_getdoc(dc_type)
    if docstring is not None and not _has_default_dataclass_docstring(dc_type):
        definition.setdefault("description", docstring)

    if "properties" not in definition:
        # Maybe a dataclass without any fields?
        return

    assert isinstance(definition["properties"], dict)
    dc_fields = {field.name: field for field in dataclasses.fields(dc_type)}

    for property_name, property_values in definition["properties"].items():
        assert isinstance(property_values, dict)
        # note: here `property_name` is supposed to be a field of the dataclass.
        # double-check just to be sure.
        if property_name not in dc_fields:
            logger.warning(
                RuntimeWarning(
                    "assuming that properties are dataclass fields, but encountered"
                    f"property {property_name} which isn't a field of the dataclass {dc_type}"
                )
            )
            continue
        field_docstring = get_attribute_docstring(dc_type, property_name)
        field_desc = field_docstring.help_string.strip()
        if field_desc:
            property_values.setdefault("description", field_desc)


if __name__ == "__main__":
    save_yaml_with_schema(
        Nested(bob=Bob(foo=222), other_field="babab"), Path(__file__).parent / "nested.yaml"
    )
