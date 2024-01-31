from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import IO

try:
    import yaml
except ImportError:
    pass

from .serializable import D, Serializable

logger = getLogger(__name__)


class YamlSerializable(Serializable):
    """Convenience class, just sets different `load_fn` and `dump_fn` defaults for the `dump`,
    `dumps`, `load`, `loads` methods of `Serializable`.

    Uses the `yaml.safe_load` and `yaml.dump` for loading and dumping.

    Requires the pyyaml package.
    """

    def dump(self, fp: IO[str], dump_fn=None, **kwargs) -> None:
        if dump_fn is None:
            dump_fn = yaml.dump
        dump_fn(self.to_dict(), fp, **kwargs)

    def dumps(self, dump_fn=None, **kwargs) -> str:
        if dump_fn is None:
            dump_fn = yaml.dump
        return dump_fn(self.to_dict(), **kwargs)

    @classmethod
    def load(
        cls: type[D],
        path: Path | str | IO[str],
        drop_extra_fields: bool | None = None,
        load_fn=None,
        **kwargs,
    ) -> D:
        if load_fn is None:
            load_fn = yaml.safe_load

        return super().load(path, drop_extra_fields=drop_extra_fields, load_fn=load_fn, **kwargs)

    @classmethod
    def loads(
        cls: type[D],
        s: str,
        drop_extra_fields: bool | None = None,
        load_fn=None,
        **kwargs,
    ) -> D:
        if load_fn is None:
            load_fn = yaml.safe_load
        return super().loads(s, drop_extra_fields=drop_extra_fields, load_fn=load_fn, **kwargs)

    @classmethod
    def _load(
        cls: type[D],
        fp: IO[str],
        drop_extra_fields: bool | None = None,
        load_fn=None,
        **kwargs,
    ) -> D:
        if load_fn is None:
            load_fn = yaml.safe_load
        return super()._load(fp, drop_extra_fields=drop_extra_fields, load_fn=load_fn, **kwargs)
