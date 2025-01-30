"""Adds typed dataclasses for the "config" yaml files."""

from collections import OrderedDict
from collections.abc import MutableMapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from test.testutils import TestSetup, raises
from typing import Callable, Optional

import pytest

from simple_parsing import field, mutable_field
from simple_parsing.helpers import FrozenSerializable, JsonSerializable, Serializable
from simple_parsing.helpers.serialization.serializable import SerializableMixin

# class TestSerializable:
#     @dataclass
#     class Child(Serializable):
#         name: str = "bob"
#         age: int = 10

#     @dataclass
#     class Parent(Serializable):
#         name: str = "Consuela"
#         children: Dict[str, Child] = mutable_field(OrderedDict)

#     @dataclass
#     class ParentWithOptionalChildren(Parent):
#         name: str = "Consuela"
#         children: Dict[str, Optional[Child]] = mutable_field(OrderedDict)

#     @dataclass
#     class ChildWithFriends(Child):
#         friends: List[Optional[Child]] = mutable_field(list)

#     @dataclass
#     class ParentWithOptionalChildrenWithFriends(Serializable):
#         name: str = "Consuela"
#         children: Mapping[str, Optional[ChildWithFriends]] = mutable_field(OrderedDict)


@pytest.fixture(scope="function", params=[True, False])
def frozen(request, monkeypatch):
    """Switches from using frozen / non-frozen dataclasses during tests."""

    # NOTE: Need to unregister all the subclasses of SerializableMixin and FrozenSerializable, so
    # the dataclasses from one test aren't used in another.
    subclasses_before = SerializableMixin.subclasses.copy()
    from simple_parsing.helpers.serialization.decoding import _decoding_fns

    frozen = request.param
    decoding_fns_before = _decoding_fns.copy()

    yield frozen

    # NOTE: Not assigning a new list here, just to be sure we're changing the object on the class
    # where it is originally set.
    SerializableMixin.subclasses.clear()
    SerializableMixin.subclasses.extend(subclasses_before)

    # Unregister the decoding functions.
    _decoding_fns.clear()
    _decoding_fns.update(decoding_fns_before)

    # Clear the LRU cache of `get_decoding_fn`.
    # get_decoding_fn.cache_clear()

    # SerializableMixin.subclasses = subclasses_before
    # note: clear the `subclasses` of the base classes?


@pytest.fixture()
def Child(frozen: bool):
    @dataclass(frozen=frozen)
    class Child(FrozenSerializable if frozen else Serializable):
        name: str = "bob"
        age: int = 10

    return Child


@pytest.fixture()
def Parent(frozen: bool, Child):
    @dataclass(frozen=frozen)
    class Parent(FrozenSerializable if frozen else Serializable):
        name: str = "Consuela"
        children: dict[str, Child] = field(default_factory=OrderedDict)

    return Parent


@pytest.fixture()
def ParentWithOptionalChildren(Parent, Child):
    @dataclass(frozen=issubclass(Parent, FrozenSerializable))
    class ParentWithOptionalChildren(Parent):
        name: str = "Consuela"
        children: dict[str, Optional[Child]] = field(default_factory=OrderedDict)

    return ParentWithOptionalChildren


@pytest.fixture()
def ChildWithFriends(Child):
    @dataclass(frozen=issubclass(Child, FrozenSerializable))
    class ChildWithFriends(Child):
        friends: list[Optional[Child]] = mutable_field(list)

    return ChildWithFriends


@pytest.fixture()
def ParentWithOptionalChildrenWithFriends(ParentWithOptionalChildren, ChildWithFriends):
    @dataclass(frozen=issubclass(ParentWithOptionalChildren, FrozenSerializable))
    class ParentWithOptionalChildrenWithFriends(ParentWithOptionalChildren):
        name: str = "Consuela"
        children: MutableMapping[str, Optional[ChildWithFriends]] = mutable_field(OrderedDict)

    return ParentWithOptionalChildrenWithFriends


def test_to_dict(silent, Child, Parent):
    bob = Child("Bob")
    clarice = Child("Clarice")
    nancy = Parent("Nancy", children=dict(bob=bob, clarice=clarice))

    assert nancy.to_dict() == {
        "name": "Nancy",
        "children": {
            "bob": {"name": "Bob", "age": 10},
            "clarice": {"name": "Clarice", "age": 10},
        },
    }


def test_loads_dumps(silent, Child, Parent):
    bob = Child("Bob")
    clarice = Child("Clarice")
    nancy = Parent("Nancy", children=dict(bob=bob, clarice=clarice))
    assert Parent.loads(nancy.dumps()) == nancy


def test_load_dump(silent, tmp_path: Path, Child, Parent):
    bob = Child("Bob")
    clarice = Child("Clarice")
    nancy: JsonSerializable = Parent("Nancy", children=dict(bob=bob, clarice=clarice))
    tmp_path = tmp_path / "tmp.json"
    nancy.save(tmp_path)
    assert Parent.load(tmp_path) == nancy


def test_optionals(silent, Child, ParentWithOptionalChildren):
    bob = Child("Bob")
    clarice = Child("Clarice")
    nancy = ParentWithOptionalChildren("Nancy", children=dict(bob=bob, clarice=clarice))
    nancy.children["jeremy"] = None
    assert nancy.to_dict() == {
        "name": "Nancy",
        "children": {
            "bob": {"name": "Bob", "age": 10},
            "clarice": {"name": "Clarice", "age": 10},
            "jeremy": None,
        },
    }
    assert ParentWithOptionalChildren.loads(nancy.dumps()) == nancy


def test_lists(silent, ChildWithFriends, Child, ParentWithOptionalChildrenWithFriends):
    bob = ChildWithFriends("Bob")
    clarice = Child("Clarice")

    bob.friends.append(clarice)
    bob.friends.append(None)

    nancy = ParentWithOptionalChildrenWithFriends("Nancy", children=dict(bob=bob))
    nancy.children["jeremy"] = None

    assert nancy.to_dict() == {
        "name": "Nancy",
        "children": {
            "bob": {
                "name": "Bob",
                "age": 10,
                "friends": [
                    {"name": "Clarice", "age": 10},
                    None,
                ],
            },
            "jeremy": None,
        },
    }

    s = nancy.dumps()
    parsed_nancy = ParentWithOptionalChildrenWithFriends.loads(s)
    assert isinstance(parsed_nancy.children["bob"], ChildWithFriends), parsed_nancy.children["bob"]

    assert parsed_nancy == nancy


@pytest.fixture()
def Base(frozen: bool):
    @dataclass(frozen=frozen)
    class Base(FrozenSerializable if frozen else Serializable, decode_into_subclasses=True):
        name: str = "bob"

    return Base


@pytest.fixture()
def A(Base):
    @dataclass(frozen=issubclass(Base, FrozenSerializable))
    class A(Base):
        name: str = "A"
        age: int = 123

    return A


@pytest.fixture()
def B(Base):
    @dataclass(frozen=issubclass(Base, FrozenSerializable))
    class B(Base):
        name: str = "B"
        favorite_color: str = "blue"

    return B


@pytest.fixture()
def Container(frozen: bool, Base):
    @dataclass(frozen=frozen)
    class Container(FrozenSerializable if frozen else Serializable):
        items: list[Base] = field(default_factory=list)

    return Container


def test_decode_right_subclass(silent, Container, Base, A, B):
    c = Container()
    c.items.append(Base())
    c.items.append(A())
    c.items.append(B())
    val = c.dumps()
    parsed_val = Container.loads(val)
    assert c == parsed_val


def test_forward_ref_dict(silent, frozen: bool):
    @dataclass(frozen=frozen)
    class LossWithDict(FrozenSerializable if frozen else Serializable):
        name: str = ""
        total: float = 0.0
        sublosses: dict[str, "LossWithDict"] = field(default_factory=dict)  # noqa

    LossWithDict.frozen = frozen
    recon = LossWithDict(name="recon", total=1.2)
    kl = LossWithDict(name="kl", total=3.4)
    original = LossWithDict(
        name="test",
        total=recon.total + kl.total,
        sublosses={"recon": recon, "kl": kl},
    )

    reconstructed = LossWithDict.from_dict(original.to_dict())
    assert original.to_dict() == reconstructed.to_dict()
    assert reconstructed == reconstructed


def test_forward_ref_list(silent, frozen: bool):
    @dataclass(frozen=frozen)
    class JLossWithList(FrozenSerializable if frozen else Serializable):
        name: str = ""
        total: float = 0.0
        same_level: list["JLossWithList"] = field(default_factory=list)  # noqa: F821

    recon = JLossWithList(name="recon", total=1.2)
    kl = JLossWithList(name="kl", total=3.4)
    test = JLossWithList(name="test", total=recon.total + kl.total, same_level=[kl])
    assert JLossWithList.loads(test.dumps()) == test


def test_forward_ref_attribute(frozen: bool):
    @dataclass(frozen=frozen)
    class LossWithAttr(FrozenSerializable if frozen else Serializable):
        name: str = ""
        total: float = 0.0
        attribute: Optional["LossWithAttr"] = None  # noqa: F821

    recon = LossWithAttr(name="recon", total=1.2)
    kl = LossWithAttr(name="kl", total=3.4)
    test = LossWithAttr(name="test", total=recon.total + kl.total, attribute=recon)
    assert LossWithAttr.loads(test.dumps()) == test


def test_forward_ref_correct_one_chosen_if_two_types_have_same_name(frozen: bool):
    @dataclass(frozen=frozen)
    class Loss(FrozenSerializable if frozen else Serializable):
        name: str = ""
        total: float = 0.0
        sublosses: dict[str, "Loss"] = field(default_factory=OrderedDict)  # noqa: F821
        fofo: int = 1

    def foo():
        @dataclass(frozen=frozen)
        class Loss(FrozenSerializable if frozen else Serializable):
            bob: str = "hello"

        return Loss

    # Get another class with name of "Loss" in our scope.
    _ = foo()
    # Check that the forward ref gets parsed to the right type.
    recon = Loss(name="recon", total=1.2)
    kl = Loss(name="kl", total=3.4)
    test = Loss(
        name="test",
        total=recon.total + kl.total,
        sublosses={"recon": recon, "kl": kl},
        fofo=123,
    )
    assert Loss.loads(test.dumps(), drop_extra_fields=False) == test


def test_simple_forwardref(frozen: bool):
    @dataclass(frozen=frozen)
    class Foo(FrozenSerializable if frozen else Serializable):
        name: str = ""
        total: "float" = 0.0
        fofo: "int" = 1

    foo = Foo()
    assert Foo.from_dict(foo.to_dict()) == foo


def test_nested_list(frozen: bool):
    @dataclass(frozen=frozen)
    class Kitten(FrozenSerializable if frozen else Serializable):
        name: str = "Meow"

    @dataclass(frozen=frozen)
    class Cat(FrozenSerializable if frozen else Serializable):
        name: str = "bob"
        age: int = 12
        litters: list[list[Kitten]] = field(default_factory=list)

    kittens: list[list[Kitten]] = [
        [Kitten(name=f"kitten_{i}") for i in range(i * 5, i * 5 + 5)] for i in range(2)
    ]
    mom = Cat("Chloe", age=12, litters=kittens)

    assert Cat.loads(mom.dumps()) == mom


def test_nested_list_optional(frozen: bool):
    @dataclass(frozen=frozen)
    class Kitten(FrozenSerializable if frozen else Serializable):
        name: str = "Meow"

    @dataclass(frozen=frozen)
    class Cat(FrozenSerializable if frozen else Serializable):
        name: str = "bob"
        age: int = 12
        litters: list[list[Optional[Kitten]]] = field(default_factory=list)

    kittens: list[list[Optional[Kitten]]] = [
        [(Kitten(name=f"kitten_{i}") if i % 2 == 0 else None) for i in range(i * 5, i * 5 + 5)]
        for i in range(2)
    ]
    mom = Cat("Chloe", age=12, litters=kittens)

    assert Cat.loads(mom.dumps()) == mom


def test_dicts(frozen: bool):
    @dataclass(frozen=frozen)
    class Cat(FrozenSerializable if frozen else Serializable):
        name: str
        age: int = 1

    @dataclass(frozen=frozen)
    class Bob(FrozenSerializable if frozen else Serializable):
        cats: dict[str, Cat] = mutable_field(dict)

    bob = Bob(cats={"Charlie": Cat("Charlie", 1)})
    assert Bob.loads(bob.dumps()) == bob

    d = bob.to_dict()
    assert Bob.from_dict(d) == bob


def test_from_dict_raises_error_on_failure(frozen: bool):
    @dataclass(frozen=frozen)
    class Something(FrozenSerializable if frozen else Serializable):
        name: str
        age: int = 0

    with raises(RuntimeError):
        Something.from_dict({"babla": 123}, drop_extra_fields=True)

    with raises(RuntimeError):
        Something.from_dict({"babla": 123}, drop_extra_fields=False)

    with raises(RuntimeError):
        Something.from_dict({}, drop_extra_fields=False)


def test_custom_encoding_fn(frozen: bool):
    @dataclass(frozen=frozen)
    class Person(FrozenSerializable if frozen else Serializable):
        name: str = field(encoding_fn=lambda s: s.upper(), decoding_fn=lambda s: s.lower())
        age: int = 0

    bob = Person("Bob")
    d = bob.to_dict()
    assert d["name"] == "BOB"
    _bob = Person.from_dict(d)
    assert _bob.name == "bob"


def test_set_field(frozen):
    from collections.abc import Hashable

    @dataclass(unsafe_hash=True, order=True, frozen=frozen)
    class Person(FrozenSerializable if frozen else Serializable, Hashable):
        name: str = "Bob"
        age: int = 0

    bob = Person("Bob", 10)
    peter = Person("Peter", 11)

    from simple_parsing.helpers import set_field

    @dataclass(frozen=frozen)
    class Group(FrozenSerializable if frozen else Serializable):
        members: set[Person] = set_field(bob, peter)

    g = Group()
    s = g.dumps_json(sort_keys=True)
    assert (
        s == '{"members": [{"age": 10, "name": "Bob"}, {"age": 11, "name": "Peter"}]}'
        or s == '{"members": [{"age": 11, "name": "Peter"}, {"age": 10, "name": "Bob"}]}'
    )

    g_ = Group.loads(s)
    assert isinstance(g_.members, set)
    m1 = sorted(g.members)
    m2 = sorted(g_.members)
    assert m1 == m2
    assert isinstance(m1[0], Person)
    assert isinstance(m2[0], Person)
    assert g_ == g


def test_used_as_dict_key(frozen: bool):
    from collections.abc import Hashable

    @dataclass(unsafe_hash=True, order=True, frozen=frozen)
    class Person(FrozenSerializable if frozen else Serializable, Hashable):
        name: str = "Bob"
        age: int = 0

    bob = Person("Bob", 10)
    peter = Person("Peter", 11)

    from simple_parsing.helpers import dict_field

    @dataclass(frozen=frozen)
    class Leaderboard(FrozenSerializable if frozen else Serializable):
        participants: dict[Person, int] = dict_field({bob: 1, peter: 2})

    # TODO: When serializing a dict, if the key itself is a dict, then we
    # need to serialize it as an ordered dict (list of tuples), because a dict isn't hashable!
    g = Leaderboard()
    assert g.to_dict() == {
        "participants": [
            ({"age": 10, "name": "Bob"}, 1),
            ({"age": 11, "name": "Peter"}, 2),
        ]
    }
    s = g.dumps_json(sort_keys=True)
    assert (
        s
        == '{"participants": [[{"age": 10, "name": "Bob"}, 1], [{"age": 11, "name": "Peter"}, 2]]}'
    )

    g_ = Leaderboard.loads(s)
    assert isinstance(g_.participants, dict)


def test_tuple_with_ellipsis(frozen: bool):
    @dataclass(frozen=frozen)
    class Container(FrozenSerializable if frozen else Serializable):
        ints: tuple[int, ...] = ()

    container = Container(ints=(1, 2))
    assert Container.loads(container.dumps()) == container


def test_choice_dict_with_nonserializable_values(frozen: bool):
    """Test that when a choice_dict has values of some non-json-FrozenSerializable if frozen else
    Serializable type, a custom encoding/decoding function is provided that will map to/from the
    dict keys rather than attempt to serialize the field value."""
    from simple_parsing import choice

    def identity(x: int):
        print(f"Func a: {x}")
        return x

    def double(x: int):
        print(f"func B: {x}")
        return x * 2

    @dataclass(frozen=frozen)
    class Bob(FrozenSerializable if frozen else Serializable, TestSetup):
        func: Callable = choice({"identity": identity, "double": double}, default="a")

    b = Bob(func=identity)
    assert b.func(10) == 10

    b = Bob(func=double)
    assert b.func(10) == 20

    b = Bob.setup("--func identity")
    assert b.func(10) == 10
    assert b.to_dict() == {"func": "identity"}
    assert Bob.from_dict(b.to_dict()) == b

    b = Bob.setup("--func double")
    assert b.func(10) == 20
    assert b.to_dict() == {"func": "double"}
    assert Bob.from_dict(b.to_dict()) == b


def test_enum(frozen: bool):
    class AnimalType(Enum):
        CAT = "cat"
        DOG = "dog"

    @dataclass(frozen=frozen)
    class Animal(FrozenSerializable if frozen else Serializable):
        animal_type: AnimalType
        name: str

    animal = Animal(AnimalType.CAT, "Fluffy")
    assert Animal.loads(animal.dumps()) == animal

    d = animal.to_dict()
    assert d["animal_type"] == "CAT"
    assert Animal.from_dict(d) == animal


def test_enum_with_ints(frozen: bool):
    class AnimalType(Enum):
        CAT = 1
        DOG = 2

    @dataclass(frozen=frozen)
    class Animal(FrozenSerializable if frozen else Serializable):
        animal_type: AnimalType
        name: str

    animal = Animal(AnimalType.CAT, "Fluffy")
    assert Animal.loads(animal.dumps()) == animal

    d = animal.to_dict()
    assert d["animal_type"] == "CAT"
    assert Animal.from_dict(d) == animal


def test_path(frozen: bool):
    @dataclass(frozen=frozen)
    class Foo(FrozenSerializable if frozen else Serializable):
        path: Path

    foo = Foo(Path("/tmp/foo"))
    assert Foo.loads(foo.dumps()) == foo

    d = foo.to_dict()
    assert isinstance(d["path"], str)
    assert Foo.from_dict(d) == foo
    assert isinstance(Foo.from_dict(d).path, Path)
