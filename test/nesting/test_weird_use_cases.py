from dataclasses import dataclass
from typing import *
from test.testutils import *
from simple_parsing import ArgumentParser, MutableField, ConflictResolution
import pytest
import logging
T = TypeVar("T", str, int, float)


def simple_tree_structure(some_type: Type[T], default_value_function: Callable[[str], T]):
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
        child_a: A = A(default_value_function("AB_a"))
        child_b: B = B(default_value_function("AB_b"))

    @dataclass
    class CD:
        child_c: C = C(default_value_function("CD_c"))
        child_d: D = D(default_value_function("CD_c"))

    @dataclass
    class ABCD(TestSetup):
        child_ab: AB = AB(A(default_value_function("ABCD_AB_a")),
                          B(default_value_function("ABCD_AB_b")))
        child_cd: CD = CD(C(default_value_function("ABCD_CD_c")),
                          D(default_value_function("ABCD_CD_d")))

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
    abcd: ABCD = ABCD.setup(
        "", conflict_resolution_mode=ConflictResolution.ALWAYS_MERGE)
    assert abcd.child_ab.child_a.a == "ABCD_AB_a"
    assert abcd.child_ab.child_b.b == "ABCD_AB_b"
    assert abcd.child_cd.child_c.c == "ABCD_CD_c"
    assert abcd.child_cd.child_d.d == "ABCD_CD_d"


def tree_structure_with_repetitions(some_type: Type[T], default_value_function: Callable[[str], T]):
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
        """ Weird AA Class """
        a1: A = A(default_value_function("A_1"))
        a2: A = A(default_value_function("A_2"))

    @dataclass
    class BB:
        """ Weird BB Class """
        b1: B = B(default_value_function("B_1"))
        b2: B = B(default_value_function("B_2"))

    @dataclass
    class CC:
        """ Weird CC Class """
        c1: C = C(default_value_function("C_1"))
        c2: C = C(default_value_function("C_2"))

    @dataclass
    class DD:
        """ Weird DD Class """
        d1: D = D(default_value_function("D_1"))
        d2: D = D(default_value_function("D_2"))

    @dataclass
    class AABB:
        """ Weird AABB Class """
        aa: AA = AA(A(default_value_function("aa_a_1")), A(default_value_function("aa_a_2")))
        bb: BB = BB(B(default_value_function("bb_b_1")), B(default_value_function("bb_b_2")))

    @dataclass
    class CCDD:
        """ Weird CCDD Class """
        cc: CC = CC(C(default_value_function("cc_c_1")), C(default_value_function("cc_c_2")))
        dd: DD = DD(D(default_value_function("dd_d_1")), D(default_value_function("dd_d_2")))

    @dataclass
    class AABBCCDD(TestSetup):
        """Weird AABBCCDD Class"""
        aabb: AABB = AABB(AA(A(default_value_function("aabb_aa_a_1")), A(default_value_function("aabb_aa_a_2"))),
                          BB(B(default_value_function("aabb_bb_b_1")), B(default_value_function("aabb_bb_b_2"))))
        ccdd: CCDD = CCDD(CC(C(default_value_function("ccdd_cc_c_1")), C(default_value_function("ccdd_cc_c_2"))),
                          DD(D(default_value_function("ccdd_dd_d_1")), D(default_value_function("ccdd_dd_d_2"))))

    @dataclass
    class AABBCCDDWeird(TestSetup):
        """ Weird AABBCCDDWeird Class """
        a: A = A("a")
        b: B = B("b")
        c: C = C("c")
        d: D = D("d")
        aabb: AABB = AABB(AA(A("aabb_aa_a_1"), A("aabb_aa_a_2")),
                        BB(B("aabb_bb_b_1"), B("aabb_bb_b_2")))
        ccdd: CCDD = CCDD(CC(C("ccdd_cc_c_1"), C("ccdd_cc_c_2")),
                        DD(D("ccdd_dd_d_1"), D("ccdd_dd_d_2")))
    
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


def test_defaults(HyperParameters):
    default = HyperParameters()
    parsed = HyperParameters.setup("")
    for attr, value in vars(default).items():
        assert getattr(parsed, attr) == value
