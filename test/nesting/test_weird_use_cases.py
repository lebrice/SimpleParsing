import functools
from dataclasses import dataclass, field
from test.testutils import T, TestSetup
from typing import Callable

from simple_parsing import ConflictResolution

from .example_use_cases import HyperParameters


def simple_tree_structure(some_type: type[T], default_value_function: Callable[[str], T]):
    @dataclass
    class A:
        a: some_type = default_value_function("a")  # type: ignore

    @dataclass
    class B:
        b: some_type = default_value_function("b")  # type: ignore

    @dataclass
    class C:
        c: some_type = default_value_function("c")  # type: ignore

    @dataclass
    class D:
        d: some_type = default_value_function("d")  # type: ignore

    @dataclass
    class AB:
        child_a: A = field(default_factory=functools.partial(A, default_value_function("AB_a")))
        child_b: B = field(default_factory=functools.partial(B, default_value_function("AB_b")))

    @dataclass
    class CD:
        child_c: C = field(default_factory=functools.partial(C, default_value_function("CD_c")))
        child_d: D = field(default_factory=functools.partial(D, default_value_function("CD_c")))

    @dataclass
    class ABCD(TestSetup):
        # TODO: Making a nested dataclass with `functools.partial` probably actually doesn't work
        # for nested fields!
        child_ab: AB = field(
            default_factory=functools.partial(
                AB,
                A(default_value_function("ABCD_AB_a")),
                B(default_value_function("ABCD_AB_b")),
            )
        )
        child_cd: CD = field(
            default_factory=functools.partial(
                CD,
                C(default_value_function("ABCD_CD_c")),
                D(default_value_function("ABCD_CD_d")),
            )
        )

    return ABCD


def test_beautiful_tree_structure_auto():
    ABCD = simple_tree_structure(str, lambda attribute_name: str(attribute_name))
    abcd: ABCD = ABCD.setup("")
    assert abcd.child_ab.child_a.a == "ABCD_AB_a"
    assert abcd.child_ab.child_b.b == "ABCD_AB_b"
    assert abcd.child_cd.child_c.c == "ABCD_CD_c"
    assert abcd.child_cd.child_d.d == "ABCD_CD_d"


def test_beautiful_tree_structure_merge():
    ABCD = simple_tree_structure(str, str)
    abcd: ABCD = ABCD.setup("", conflict_resolution_mode=ConflictResolution.ALWAYS_MERGE)
    assert abcd.child_ab.child_a.a == "ABCD_AB_a"
    assert abcd.child_ab.child_b.b == "ABCD_AB_b"
    assert abcd.child_cd.child_c.c == "ABCD_CD_c"
    assert abcd.child_cd.child_d.d == "ABCD_CD_d"


def tree_structure_with_repetitions(
    some_type: type[T], default_value_function: Callable[[str], T]
):
    @dataclass
    class A:
        a: some_type = default_value_function("a")  # type: ignore

    @dataclass
    class B:
        b: some_type = default_value_function("b")  # type: ignore

    @dataclass
    class C:
        c: some_type = default_value_function("c")  # type: ignore

    @dataclass
    class D:
        d: some_type = default_value_function("d")  # type: ignore

    @dataclass
    class AA:
        """Weird AA Class."""

        a1: A = field(default_factory=functools.partial(A, default_value_function("A_1")))
        a2: A = field(default_factory=functools.partial(A, default_value_function("A_2")))

    @dataclass
    class BB:
        """Weird BB Class."""

        b1: B = field(default_factory=functools.partial(B, default_value_function("B_1")))
        b2: B = field(default_factory=functools.partial(B, default_value_function("B_2")))

    @dataclass
    class CC:
        """Weird CC Class."""

        c1: C = field(default_factory=functools.partial(C, default_value_function("C_1")))
        c2: C = field(default_factory=functools.partial(C, default_value_function("C_2")))

    @dataclass
    class DD:
        """Weird DD Class."""

        d1: D = field(default_factory=functools.partial(D, default_value_function("D_1")))
        d2: D = field(default_factory=functools.partial(D, default_value_function("D_2")))

    @dataclass
    class AABB:
        """Weird AABB Class."""

        aa: AA = field(
            default_factory=functools.partial(
                AA, A(default_value_function("aa_a_1")), A(default_value_function("aa_a_2"))
            )
        )
        bb: BB = field(
            default_factory=functools.partial(
                BB, B(default_value_function("bb_b_1")), B(default_value_function("bb_b_2"))
            )
        )

    @dataclass
    class CCDD:
        """Weird CCDD Class."""

        cc: CC = field(
            default_factory=functools.partial(
                CC, C(default_value_function("cc_c_1")), C(default_value_function("cc_c_2"))
            )
        )
        dd: DD = field(
            default_factory=functools.partial(
                DD, D(default_value_function("dd_d_1")), D(default_value_function("dd_d_2"))
            )
        )

    @dataclass
    class AABBCCDD(TestSetup):
        """Weird AABBCCDD Class."""

        aabb: AABB = field(
            default_factory=functools.partial(
                AABB,
                AA(
                    A(default_value_function("aabb_aa_a_1")),
                    A(default_value_function("aabb_aa_a_2")),
                ),
                BB(
                    B(default_value_function("aabb_bb_b_1")),
                    B(default_value_function("aabb_bb_b_2")),
                ),
            )
        )
        ccdd: CCDD = field(
            default_factory=functools.partial(
                CCDD,
                CC(
                    C(default_value_function("ccdd_cc_c_1")),
                    C(default_value_function("ccdd_cc_c_2")),
                ),
                DD(
                    D(default_value_function("ccdd_dd_d_1")),
                    D(default_value_function("ccdd_dd_d_2")),
                ),
            )
        )

    @dataclass
    class AABBCCDDWeird(TestSetup):
        """Weird AABBCCDDWeird Class."""

        a: A = field(default_factory=functools.partial(A, "a"))
        b: B = field(default_factory=functools.partial(B, "b"))
        c: C = field(default_factory=functools.partial(C, "c"))
        d: D = field(default_factory=functools.partial(D, "d"))
        aabb: AABB = field(
            default_factory=functools.partial(
                AABB,
                AA(A("aabb_aa_a_1"), A("aabb_aa_a_2")),
                BB(B("aabb_bb_b_1"), B("aabb_bb_b_2")),
            )
        )
        ccdd: CCDD = field(
            default_factory=functools.partial(
                CCDD,
                CC(C("ccdd_cc_c_1"), C("ccdd_cc_c_2")),
                DD(D("ccdd_dd_d_1"), D("ccdd_dd_d_2")),
            )
        )

    return AABBCCDD, AABBCCDDWeird


def test_weird_tree_with_repetitions():
    AABBCCDD, AABBCCDDWeird = tree_structure_with_repetitions(str, str)
    aabbccdd: AABBCCDD = AABBCCDD.setup("")
    assert aabbccdd.aabb.aa.a1.a == "aabb_aa_a_1"
    assert aabbccdd.aabb.aa.a2.a == "aabb_aa_a_2"
    assert aabbccdd.aabb.bb.b1.b == "aabb_bb_b_1"
    assert aabbccdd.aabb.bb.b2.b == "aabb_bb_b_2"

    assert aabbccdd.ccdd.cc.c1.c == "ccdd_cc_c_1"
    assert aabbccdd.ccdd.cc.c2.c == "ccdd_cc_c_2"
    assert aabbccdd.ccdd.dd.d1.d == "ccdd_dd_d_1"
    assert aabbccdd.ccdd.dd.d2.d == "ccdd_dd_d_2"


def test_weird_with_duplicates_and_at_different_levels():
    AABBCCDD, AABBCCDDWeird = tree_structure_with_repetitions(str, str)
    aabbccdd: AABBCCDDWeird = AABBCCDDWeird.setup("")
    assert aabbccdd.a.a == "a"
    assert aabbccdd.b.b == "b"
    assert aabbccdd.c.c == "c"
    assert aabbccdd.d.d == "d"
    assert aabbccdd.aabb.aa.a1.a == "aabb_aa_a_1"
    assert aabbccdd.aabb.aa.a2.a == "aabb_aa_a_2"
    assert aabbccdd.aabb.bb.b1.b == "aabb_bb_b_1"
    assert aabbccdd.aabb.bb.b2.b == "aabb_bb_b_2"

    assert aabbccdd.ccdd.cc.c1.c == "ccdd_cc_c_1"
    assert aabbccdd.ccdd.cc.c2.c == "ccdd_cc_c_2"
    assert aabbccdd.ccdd.dd.d1.d == "ccdd_dd_d_1"
    assert aabbccdd.ccdd.dd.d2.d == "ccdd_dd_d_2"


def test_defaults():
    default = HyperParameters()
    parsed = HyperParameters.setup("")
    for attr, value in vars(default).items():
        assert getattr(parsed, attr) == value
