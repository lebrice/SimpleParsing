import dataclasses
import warnings
from typing import *

from ..logging_utils import get_logger

logger = get_logger(__file__)

class FlattenedAccess:
    """ Allows flattened access to the attributes of all children dataclasses.

    This is meant to simplify the adoption of dataclasses for argument
    hierarchies, rather than a single-level dictionary.
    Dataclasses allow for easy, neatly separated arguments, but suffer from 2
    potential drawbacks:
    - When using a highly nested structure, having long accesses is annoying
    - The dictionary access syntax is often more natural than using getattr()
        when reading an attribute whose name is a variable.
    """
    
    def attributes(self,
                   recursive: bool=True,
                   prefix: str="") -> Iterable[Tuple[str, Any]]:
        """Returns an Iterator over the attributes of the dataclass.
        
        [extended_summary]
        
        Parameters
        ----------
        - dataclass : Dataclass
        
            A dataclass type or instance.
        - recursive : bool, optional, by default True
        
            Wether or not to recurse and yield all the elements of the children
            dataclass attributes.
        - prefix : str, optional, by default ""
        
            A prefix to prepend to all the attribute names before yielding them.
        
        Returns
        -------
        Iterable[Tuple[str, Any]]
            An iterable of attribute names and values.
        
        Yields
        -------
        Iterable[Tuple[str, Any]]
            A Tuple of the form <Attribute name, attribute_value>.
        """
        for field in dataclasses.fields(self):
            if field.name not in self.__dict__:
                # the dataclass isn't yet instantiated, or the attr was deleted.
                continue
            # get the field value (without needless recursion)
            field_value = self.__dict__[field.name]
            
            yield prefix + field.name, field_value
            if recursive and dataclasses.is_dataclass(field_value):
                yield from FlattenedAccess.attributes(
                    field_value,
                    recursive=True,
                    prefix=prefix + field.name + "."
                )

    def __getattr__(self, name: str):
        """Retrieves the attribute on self, or recursively on the children.
        
        NOTE: `__getattribute__` is always called before `__getattr__`, hence we
        always get here because `self` does not have an attribute of `name`.
        """
        # potential parents and corresponding values.
        parents: List[str] = []
        values: List[Any] = []

        for attr_name, attr_value in FlattenedAccess.attributes(self):
            # if the attribute name's last part ends with `name`, we add it to
            # some list of potential parent attributes.
            name_parts = name.split(".")
            dest_parts = attr_name.split(".")
            if dest_parts[-len(name_parts):] == name_parts:
                parents.append(attr_name)
                values.append(attr_value)
        
        if not parents:
            raise AttributeError(
                f"{type(self)} object has no attribute '{name}', "
                "and neither does any of its children attributes."
            )
        elif len(parents) > 1:
            raise AttributeError(
                f"Ambiguous Attribute access: name '{name}' may refer to:\n" + 
                "\n".join(f"- '{parent}' (with a value of: '{value}')"
                    for parent, value in zip(parents, values)
                )
            )
        else:
            return values[0]

    def __setattr__(self, name: str, value: Any):
        """Write the attribute in self or in the children that has it.

        If more than one child has attributes that match the given one, an
        `AttributeError` is raised. 
        """
        # potential parents and corresponding values.
        parents: List[str] = []
        values: List[Any] = []

        field_names = {field.name for field in dataclasses.fields(self)}
        if name in field_names:
            object.__setattr__(self, name, value)
            return

        for attr_name, attr_value in self.attributes():
            # if the attribute name of the attribute ends with `name`, we add it
            # to some list of potential parent attributes.
            name_parts = name.split(".")
            dest_parts = attr_name.split(".")
            if dest_parts[-len(name_parts):] == name_parts:
                parents.append(attr_name)
                values.append(attr_value)
        
        if not parents:
            # We set the value on the dataclass directly, since it wasn't found.
            warnings.warn(UserWarning(f"Setting a new attribute '{name}' on the"
                f" dataclass, but it does not have a field of the same name. \n"
                f"(Consider adding a field '{name}' of type {type(value)} to "
                f"{type(self)})"))      
            object.__setattr__(self, name, value)

        elif len(parents) > 1:
            # more than one parent (ambiguous).
            raise AttributeError(
                f"Ambiguous Attribute access: name '{name}' may refer to:\n" + 
                "\n".join(f"- '{parent}' (with a value of: '{value}')"
                    for parent, value in zip(parents, values)
                )
            )
        else:
            # We recursively set the attribute.
            attr_name = parents[0]
            lineage = attr_name.split(".")[:-1]
            parent: object = self
            for parent_name in lineage:
                # NOTE: we can't use getattr, otherwise we would recurse.
                parent = object.__getattribute__(parent, parent_name)
            # destination attribute name
            dest_name = name.split(".")[-1]   
            # Set the attribute on the parent.
            object.__setattr__(parent, dest_name, value) 

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)
    
    def asdict(self) -> Dict:
        return dataclasses.asdict(self)
