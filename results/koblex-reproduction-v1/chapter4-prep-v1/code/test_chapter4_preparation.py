"""Check the structural gold bound against exhaustive feasible selections.

Extract the pure function to keep preparation I/O and network guards out of tests.
"""
import ast
import itertools
from pathlib import Path


def matching_function():
    tree = ast.parse(Path("scripts/prepare_chapter4.py").read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "max_gold_matching")
    scope = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "prep-matching", "exec"), scope)
    return scope["max_gold_matching"]


def test_union_coverage_does_not_imply_pool_feasibility():
    matching = matching_function()
    pools = [{"A", "B"}, {"OTHER"}]
    assert {"A", "B"} <= set.union(*pools)
    assert matching(pools, {"A", "B"}) == 1


def test_augmenting_path_reassigns_previous_gold_to_another_pool():
    matching = matching_function()
    assert matching([{"A", "B"}, {"A"}], {"A", "B"}) == 2


def test_gold_bound_matches_exhaustive_one_choice_per_pool():
    matching = matching_function()
    # Includes unavailable gold and repeated passage occurrence across pools.
    gold = {"A", "B", "C"}
    pool_options = [set(combo) for n in (1, 2, 3) for combo in itertools.combinations(["A", "B", "C", "X"], n)]
    for pools in itertools.product(pool_options, repeat=3):
        expected = max(len(gold & set(chosen)) for chosen in itertools.product(*pools))
        assert matching(pools, gold) == expected
