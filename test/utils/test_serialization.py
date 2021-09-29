"""Adds typed dataclasses for the "config" yaml files.
"""
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from test.testutils import raises, TestSetup
from typing import Dict, List, Mapping, Optional, Set, Tuple, Callable


from simple_parsing import field, mutable_field
from simple_parsing.helpers import Serializable, YamlSerializable

SerializableBase = Serializable


# Test both json and yaml serialization.
for serializable_class in (Serializable, YamlSerializable):
    # Clear the subclasses between each 'round' of tests, so they don't influence each other.
    # TODO: This for loop thingy is quite ugly. Might be better to create a test base class and then
    # subclass it?
    SerializableBase.subclasses.clear()

    @dataclass
    class Child(serializable_class):
        name: str = "bob"
        age: int = 10

    @dataclass
    class Parent(serializable_class):
        name: str = "Consuela"
        children: Dict[str, Child] = mutable_field(OrderedDict)

    def test_to_dict(silent):
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

    def test_loads_dumps(silent):
        bob = Child("Bob")
        clarice = Child("Clarice")
        nancy = Parent("Nancy", children=dict(bob=bob, clarice=clarice))
        assert Parent.loads(nancy.dumps()) == nancy

    def test_load_dump(silent, tmpdir: Path):
        bob = Child("Bob")
        clarice = Child("Clarice")
        nancy = Parent("Nancy", children=dict(bob=bob, clarice=clarice))
        tmp_path = tmpdir / "tmp"
        with open(tmp_path, "w") as fp:
            nancy.dump(fp)
        with open(tmp_path, "r") as fp:
            assert Parent.load(fp) == nancy

    @dataclass
    class ParentWithOptionalChildren(Parent):
        name: str = "Consuela"
        children: Dict[str, Optional[Child]] = mutable_field(OrderedDict)

    def test_optionals(silent):
        bob = Child("Bob")
        clarice = Child("Clarice")
        nancy = ParentWithOptionalChildren(
            "Nancy", children=dict(bob=bob, clarice=clarice)
        )
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

    @dataclass
    class ChildWithFriends(Child):
        friends: List[Optional[Child]] = mutable_field(list)

    @dataclass
    class ParentWithOptionalChildrenWithFriends(serializable_class):
        name: str = "Consuela"
        children: Mapping[str, Optional[ChildWithFriends]] = mutable_field(OrderedDict)

    def test_lists(silent):
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
        assert isinstance(
            parsed_nancy.children["bob"], ChildWithFriends
        ), parsed_nancy.children["bob"]

        assert parsed_nancy == nancy

    @dataclass
    class Base(serializable_class, decode_into_subclasses=True):
        name: str = "bob"

    @dataclass
    class A(Base):
        name: str = "A"
        age: int = 123

    @dataclass
    class B(Base):
        name: str = "B"
        favorite_color: str = "blue"

    @dataclass
    class Container(serializable_class):
        items: List[Base] = field(default_factory=list)

    def test_decode_right_subclass(silent):
        c = Container()
        c.items.append(Base())
        c.items.append(A())
        c.items.append(B())
        val = c.dumps()
        parsed_val = Container.loads(val)
        assert c == parsed_val

    def test_forward_ref_dict(silent):
        @dataclass
        class LossWithDict(serializable_class):
            name: str = ""
            total: float = 0.0
            sublosses: Dict[str, "LossWithDict"] = field(default_factory=OrderedDict)

        recon = LossWithDict(name="recon", total=1.2)
        kl = LossWithDict(name="kl", total=3.4)
        test = LossWithDict(
            name="test",
            total=recon.total + kl.total,
            sublosses={"recon": recon, "kl": kl},
        )
        assert LossWithDict.loads(test.dumps()) == test

    def test_forward_ref_list(silent):
        @dataclass
        class JLossWithList(serializable_class):
            name: str = ""
            total: float = 0.0
            same_level: List["JLossWithList"] = field(default_factory=list)

        recon = JLossWithList(name="recon", total=1.2)
        kl = JLossWithList(name="kl", total=3.4)
        test = JLossWithList(name="test", total=recon.total + kl.total, same_level=[kl])
        assert JLossWithList.loads(test.dumps()) == test

    def test_forward_ref_attribute():
        @dataclass
        class LossWithAttr(serializable_class):
            name: str = ""
            total: float = 0.0
            attribute: Optional["LossWithAttr"] = None

        recon = LossWithAttr(name="recon", total=1.2)
        kl = LossWithAttr(name="kl", total=3.4)
        test = LossWithAttr(name="test", total=recon.total + kl.total, attribute=recon)
        assert LossWithAttr.loads(test.dumps()) == test

    @dataclass
    class Loss(serializable_class):
        bob: str = "hello"

    def test_forward_ref_correct_one_chosen_if_two_types_have_same_name():
        @dataclass
        class Loss(serializable_class):
            name: str = ""
            total: float = 0.0
            sublosses: Dict[str, "Loss"] = field(default_factory=OrderedDict)
            fofo: int = 1

        recon = Loss(name="recon", total=1.2)
        kl = Loss(name="kl", total=3.4)
        test = Loss(
            name="test",
            total=recon.total + kl.total,
            sublosses={"recon": recon, "kl": kl},
            fofo=123,
        )
        assert Loss.loads(test.dumps(), drop_extra_fields=False) == test

    def test_nested_list():
        @dataclass
        class Kitten(serializable_class):
            name: str = "Meow"

        @dataclass
        class Cat(serializable_class):
            name: str = "bob"
            age: int = 12
            litters: List[List[Kitten]] = field(default_factory=list)

        kittens: List[List[Kitten]] = [
            [Kitten(name=f"kitten_{i}") for i in range(i * 5, i * 5 + 5)]
            for i in range(2)
        ]
        mom = Cat("Chloe", age=12, litters=kittens)

        assert Cat.loads(mom.dumps()) == mom

    def test_nested_list_optional():
        @dataclass
        class Kitten(serializable_class):
            name: str = "Meow"

        @dataclass
        class Cat(serializable_class):
            name: str = "bob"
            age: int = 12
            litters: List[List[Optional[Kitten]]] = field(default_factory=list)

        kittens: List[List[Optional[Kitten]]] = [
            [
                (Kitten(name=f"kitten_{i}") if i % 2 == 0 else None)
                for i in range(i * 5, i * 5 + 5)
            ]
            for i in range(2)
        ]
        mom = Cat("Chloe", age=12, litters=kittens)

        assert Cat.loads(mom.dumps()) == mom

    def test_dicts():
        @dataclass
        class Cat(serializable_class):
            name: str
            age: int = 1

        @dataclass
        class Bob(serializable_class):
            cats: Dict[str, Cat] = mutable_field(dict)

        bob = Bob(cats={"Charlie": Cat("Charlie", 1)})
        assert Bob.loads(bob.dumps()) == bob

        d = bob.to_dict()
        assert Bob.from_dict(d) == bob

    def test_from_dict_raises_error_on_failure():
        @dataclass
        class Something(serializable_class):
            name: str
            age: int = 0

        with raises(RuntimeError):
            Something.from_dict({"babla": 123}, drop_extra_fields=True)

        with raises(RuntimeError):
            Something.from_dict({"babla": 123}, drop_extra_fields=False)

        with raises(RuntimeError):
            Something.from_dict({}, drop_extra_fields=False)

    def test_custom_encoding_fn():
        @dataclass
        class Person(serializable_class):
            name: str = field(
                encoding_fn=lambda s: s.upper(), decoding_fn=lambda s: s.lower()
            )
            age: int = 0

        bob = Person("Bob")
        d = bob.to_dict()
        assert d["name"] == "BOB"
        _bob = Person.from_dict(d)
        assert _bob.name == "bob"

    def test_set_field():
        from typing import Hashable

        @dataclass(unsafe_hash=True, order=True)
        class Person(serializable_class, Hashable):
            name: str = "Bob"
            age: int = 0

        bob = Person("Bob", 10)
        peter = Person("Peter", 11)

        from simple_parsing.helpers import set_field

        @dataclass
        class Group(serializable_class):
            members: Set[Person] = set_field(bob, peter)

        g = Group()
        s = g.dumps_json(sort_keys=True)
        assert (
            s
            == '{"members": [{"age": 10, "name": "Bob"}, {"age": 11, "name": "Peter"}]}'
            or s
            == '{"members": [{"age": 11, "name": "Peter"}, {"age": 10, "name": "Bob"}]}'
        )

        g_ = Group.loads(s)
        assert isinstance(g_.members, set)
        m1 = sorted(g.members)
        m2 = sorted(g_.members)
        assert m1 == m2
        assert isinstance(m1[0], Person)
        assert isinstance(m2[0], Person)
        assert g_ == g

    def test_used_as_dict_key():
        from typing import Hashable

        @dataclass(unsafe_hash=True, order=True)
        class Person(serializable_class, Hashable):
            name: str = "Bob"
            age: int = 0

        bob = Person("Bob", 10)
        peter = Person("Peter", 11)

        from simple_parsing.helpers import dict_field

        @dataclass
        class Leaderboard(serializable_class):
            participants: Dict[Person, int] = dict_field({bob: 1, peter: 2})

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

    def test_tuple_with_ellipsis():
        @dataclass
        class Container(serializable_class):
            ints: Tuple[int, ...] = ()

        container = Container(ints=(1, 2))
        assert Container.loads(container.dumps()) == container


def test_choice_dict_with_nonserializable_values():
    """Test that when a choice_dict has values of some non-json-serializable_class type, a
    custom encoding/decoding function is provided that will map to/from the dict keys
    rather than attempt to serialize the field value.

    """
    from simple_parsing import choice

    def identity(x: int):
        print(f"Func a: {x}")
        return x

    def double(x: int):
        print(f"func B: {x}")
        return x * 2

    @dataclass
    class Bob(TestSetup, serializable_class):
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
