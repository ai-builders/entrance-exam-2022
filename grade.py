#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import unittest
from collections.abc import Callable

import click
import numpy as np
import pandas as pd
from pytest import approx

from aibuilders_exam.grading.context import ApplicationContext
from aibuilders_exam.grading.engine import ModuleItem, Param, TestGroup, TestScenario, TestSuite
from aibuilders_exam.grading.loader import NotebookLoader
from aibuilders_exam.helpers import rich_time, validate_pos

unit_testing = unittest.TestCase()

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FUNNY_WORDS = [
    "poboy", "dobby", "cuppy", "hobby", "pudgy", "cocky", "bawdy", "miffy", "foamy", "jazzy",
    "caddy", "jaggy", "muddy", "jumpy", "duchy", "poppy", "yucky", "bumpy", "biddy", "choky",
    "fuzzy", "buggy", "byway", "gaudy", "dizzy", "moody", "muggy", "gabby", "dicky", "doggy",
    "wiggy", "hooky", "kiddy", "dumpy", "waddy", "guppy", "woody", "doozy", "giddy", "mummy",
    "gamay", "piggy", "divvy", "gawky", "bobby", "woozy", "ducky", "buddy", "cooky", "mommy",
    "dodgy", "middy", "gummy", "kooky", "jiffy", "humpy", "picky", "comfy", "puppy", "muzzy",
    "copay", "cabby", "gauzy", "booby", "boomy", "mammy", "boody", "pommy", "zappy", "yummy",
    "wacky", "jimmy", "hubby", "bubby", "paddy", "pappy", "goofy", "cubby", "goody", "juicy",
    "hammy", "daffy", "kicky", "zippy", "pawky", "biffy", "hippy", "baggy", "howdy", "cuddy",
    "daddy", "dowdy", "dippy", "happy", "huffy", "dummy", "foggy",
]
SPORTSDAY_DF = pd.read_csv(os.path.join(THIS_DIR, "sportsday.csv"))


@click.command()
@click.argument('notebook_file', type=click.Path(exists=True, dir_okay=False))
@click.option(
    '--export-json', type=click.Path(dir_okay=False, writable=True),
    help="Path to save grading result as a JSON file",
)
@click.option(
    '--force-grade-all', is_flag=True,
    help="Turn this option on to keep grading even after encountering the first mistake in each test group",
)
@click.option('--always-zero-exit', is_flag=True, help="Always returns exit status 0 even mistakes were found")
@click.option('-v', '--verbose', count=True, help="Produce more detailed message (can be stacked)")
@click.option('-q', '--quiet', count=True, help="Produce less detailed message (can be stacked)")
@click.option('--width', type=int, callback=validate_pos, help="Width of terminal (default: auto detect)")
@click.option('--height', type=int, callback=validate_pos, help="Height of terminal (default: auto detect)")
@click.option('--force-color/--no-force-color', default=None, help="Display color on terminal (default: auto detect)")
def program(
        notebook_file: str,
        export_json: str = None,
        force_grade_all: bool = False,
        always_zero_exit: bool = False,
        verbose: int = 0,
        quiet: int = 0,
        width: int = None,
        height: int = None,
        force_color: bool = None,
):
    """Grades the exam notebook."""
    ctx = ApplicationContext(
        force_grade_all=force_grade_all,
        always_zero_exit=always_zero_exit,
        verbose=verbose,
        quiet=quiet,
        width=width,
        height=height,
        force_color=force_color,
    )

    # Setup rich console object for pretty terminal printing
    ctx.console.print(rich_time(), "Grading script started")

    # Load the exam notebook from the specified path as a Python module object
    nb_loader = NotebookLoader(console=ctx.console, show_skip_cells=ctx.show_skip_cells)
    module_name = 'exam'
    try:
        mod = nb_loader.load_module(module_name, notebook_file)
    except Exception as exc:
        ctx.console.print_exception()
        if export_json:
            with open(export_json, "w") as f:
                json.dump(TEST_SUITE.do_skip().serialize(), f, ensure_ascii=False, indent=2)
        raise SystemExit(1) from exc

    # Execute the entire test suite and print the score summary
    result = TEST_SUITE.execute(ctx, mod)
    ctx.console.print(rich_time(), result.rich_score())

    # Export the result into JSON file if option is set
    if export_json:
        with open(export_json, "w") as f:
            json.dump(result.serialize(), f, ensure_ascii=False, indent=2)
        ctx.console.print(rich_time(), "Result written to", repr(export_json))

    raise SystemExit(0 if always_zero_exit or result.is_perfect else 1)


@TestScenario.create(ModuleItem('count_even'), Param(), Param())
def test_count_even(func: Callable[[list[int]], int], values: list[int], expected: int) -> None:
    result = func(values)
    unit_testing.assertEqual(result, expected)


@TestScenario.create(ModuleItem('cone_surface_area'), Param(), Param(), Param())
def test_cone_surface_area(
        func: Callable[[float, float], float],
        radius: float,
        height: float,
        expected: float,
) -> None:
    result = func(radius, height)
    unit_testing.assertEqual(result, approx(expected))


@TestScenario.create(ModuleItem('filter_matching'), Param(), Param(), Param(), Param())
def test_filter_matching(
        func: Callable[[list[str], str, int], list[str]],
        wordbank: list[str],
        target: str,
        position: int,
        expected: list[str],
) -> None:
    result = func(wordbank, target, position)
    unit_testing.assertEqual(result, expected)


@TestScenario.create(ModuleItem('filter_absence'), Param(), Param(), Param())
def test_filter_absence(
        func: Callable[[list[str], str], list[str]],
        wordbank: list[str],
        unwanted: str,
        expected: list[str],
) -> None:
    result = func(wordbank, unwanted)
    unit_testing.assertEqual(result, expected)


@TestScenario.create(ModuleItem('filter_misplaced'), Param(), Param(), Param(), Param())
def test_filter_misplaced(
        func: Callable[[list[str], str, list[int]], list[str]],
        wordbank: list[str],
        target: str,
        unwanted_positions: list[int],
        expected: list[str],
) -> None:
    result = func(wordbank, target, unwanted_positions)
    unit_testing.assertEqual(result, expected)


@TestScenario.create(ModuleItem('all_prefixes'), Param(), Param())
def test_all_prefixes(func: Callable[[str], list[str]], s: str, expected: list[str]) -> None:
    result = func(s)
    unit_testing.assertEqual(result, expected)


@TestScenario.create(ModuleItem('longest_common_prefix'), Param(), Param(), Param())
def test_longest_common_prefix(func: Callable[[str, str], str], s1: str, s2: str, expected: str) -> None:
    result = func(s1, s2)
    unit_testing.assertEqual(result, expected)


@TestScenario.create(ModuleItem('appear_once'), Param(), Param())
def test_appear_once(func: Callable[[list[int]], set[int]], values: list[int], expected: set[int]) -> None:
    result = func(values)
    unit_testing.assertEqual(result, expected)


@TestScenario.create(ModuleItem('create_enumerate_array'), Param(), Param(), Param())
def test_create_enumerate_array(
        func: Callable[[int, int], np.ndarray],
        nrows: int,
        ncols: int,
        expected: np.ndarray,
) -> None:
    result = func(nrows, ncols)
    np.testing.assert_array_equal(result, expected)


@TestScenario.create(ModuleItem('rotate_point'), Param(), Param(), Param())
def test_rotate_point(
        func: Callable[[np.ndarray, float], np.ndarray],
        point: np.ndarray,
        angle: float,
        expected: np.ndarray,
) -> None:
    result = func(point, angle)
    np.testing.assert_allclose(result, expected, atol=1e-9)


@TestScenario.create(ModuleItem('remove_neg_sum_cols'), Param(), Param())
def test_remove_neg_sum_cols(
        func: Callable[[np.ndarray], np.ndarray],
        array: np.ndarray,
        expected: np.ndarray,
) -> None:
    result = func(array)
    np.testing.assert_equal(result, expected)


@TestScenario.create(ModuleItem('subtract_by_row_min'), Param(), Param())
def test_subtract_by_row_min(
        func: Callable[[np.ndarray], np.ndarray],
        array: np.ndarray,
        expected: np.ndarray,
) -> None:
    result = func(array)
    np.testing.assert_equal(result, expected)


@TestScenario.create(ModuleItem('common_last_name'), Param(), Param())
def test_common_last_name(
        func: Callable[[pd.DataFrame], str],
        df: pd.DataFrame,
        expected: str,
) -> None:
    result = func(df)
    np.testing.assert_equal(result, expected)


@TestScenario.create(ModuleItem('fast_runners'), Param(), Param(), Param(), Param())
def test_fast_runners(
        func: Callable[[pd.DataFrame, str, float], pd.DataFrame],
        df: pd.DataFrame,
        team_color: str,
        max_running_time: float,
        expected: set[tuple[str, str]],
) -> None:
    result = func(df, team_color, max_running_time)
    pd.testing.assert_index_equal(result.columns, SPORTSDAY_DF.columns)
    unit_testing.assertEqual(
        set(result[['first_name', 'last_name']].itertuples(index=False, name=None)),
        expected,
    )


@TestScenario.create(ModuleItem('best_bowling_and_minigolf'), Param(), Param(), Param())
def test_best_bowling_and_minigolf(
        func: Callable[[pd.DataFrame, int], tuple[float, float]],
        df: pd.DataFrame,
        class_no: int,
        expected: tuple[float, float],
) -> None:
    result = func(df, class_no)
    unit_testing.assertEqual(result, expected)


@TestScenario.create(ModuleItem('highjump_averages'), Param(), Param())
def test_highjump_averages(
        func: Callable[[pd.DataFrame], pd.Series],
        df: pd.DataFrame,
        expected: dict[str, float],
) -> None:
    result = func(df)
    unit_testing.assertEqual(result.to_dict(), approx(expected))


TEST_SUITE = TestSuite([
    TestGroup("0. Count Even", 10, [
        test_count_even.data([1, 2, 3, 4, 5], 2),
        test_count_even.data([1, 3, 5, 7], 0),
        test_count_even.data([2, 4, 8, 16, 32], 5),
        test_count_even.data([], 0),
    ]),
    TestGroup("1. Cone Surface Area", 10, [
        test_cone_surface_area.data(2, 3, 35.22071741263713),
        test_cone_surface_area.data(2, 0, 8 * math.pi),
        test_cone_surface_area.data(0, 3, 0),
        test_cone_surface_area.data(3, 4, 24 * math.pi),
    ]),
    TestGroup("2.1 Wordle Matching", 10, [
        test_filter_matching.data(["hippo", "zebra", "panda", "koala"], "a", 5, ["zebra", "panda", "koala"]),
        test_filter_matching.data(["hippo", "zebra", "panda", "koala"], "e", 2, ["zebra"]),
        test_filter_matching.data(["hippo", "zebra", "panda", "koala"], "x", 1, []),
        test_filter_matching.data(FUNNY_WORDS, "m", 1, [
            "miffy", "muddy", "moody", "muggy", "mummy", "mommy", "middy", "muzzy", "mammy",
        ]),
        test_filter_matching.data(FUNNY_WORDS, "m", 2, []),
        test_filter_matching.data(FUNNY_WORDS, "i", 3, ["juicy"]),
        test_filter_matching.data(FUNNY_WORDS, "e", 4, []),
        test_filter_matching.data(FUNNY_WORDS, "y", 5, FUNNY_WORDS),
        test_filter_matching.data(FUNNY_WORDS, "k", 4, [
            "cocky", "yucky", "choky", "dicky", "hooky", "gawky", "ducky", "cooky", "kooky", "picky",
            "wacky", "kicky", "pawky",
        ]),
        test_filter_matching.data([], "x", 2, []),
    ]),
    TestGroup("2.2 Wordle Absence", 10, [
        test_filter_absence.data(["hippo", "zebra", "panda", "koala"], "a", ["hippo"]),
        test_filter_absence.data(["zebra", "panda", "koala"], "a", []),
        test_filter_absence.data(["hippo", "zebra", "panda", "koala"], "x", ["hippo", "zebra", "panda", "koala"]),
        test_filter_absence.data(FUNNY_WORDS, "m", [
            "poboy", "dobby", "cuppy", "hobby", "pudgy", "cocky", "bawdy", "jazzy", "caddy", "jaggy",
            "duchy", "poppy", "yucky", "biddy", "choky", "fuzzy", "buggy", "byway", "gaudy", "dizzy",
            "gabby", "dicky", "doggy", "wiggy", "hooky", "kiddy", "waddy", "guppy", "woody", "doozy",
            "giddy", "piggy", "divvy", "gawky", "bobby", "woozy", "ducky", "buddy", "cooky", "dodgy",
            "kooky", "jiffy", "picky", "puppy", "copay", "cabby", "gauzy", "booby", "boody", "zappy",
            "wacky", "hubby", "bubby", "paddy", "pappy", "goofy", "cubby", "goody", "juicy", "daffy",
            "kicky", "zippy", "pawky", "biffy", "hippy", "baggy", "howdy", "cuddy", "daddy", "dowdy",
            "dippy", "happy", "huffy", "foggy",
        ]),
        test_filter_absence.data(FUNNY_WORDS, "u", [
            "poboy", "dobby", "hobby", "cocky", "bawdy", "miffy", "foamy", "jazzy", "caddy", "jaggy",
            "poppy", "biddy", "choky", "byway", "dizzy", "moody", "gabby", "dicky", "doggy", "wiggy",
            "hooky", "kiddy", "waddy", "woody", "doozy", "giddy", "gamay", "piggy", "divvy", "gawky",
            "bobby", "woozy", "cooky", "mommy", "dodgy", "middy", "kooky", "jiffy", "picky", "comfy",
            "copay", "cabby", "booby", "boomy", "mammy", "boody", "pommy", "zappy", "wacky", "jimmy",
            "paddy", "pappy", "goofy", "goody", "hammy", "daffy", "kicky", "zippy", "pawky", "biffy",
            "hippy", "baggy", "howdy", "daddy", "dowdy", "dippy", "happy", "foggy",
        ]),
        test_filter_absence.data(FUNNY_WORDS, "y", []),
        test_filter_absence.data(FUNNY_WORDS, "r", FUNNY_WORDS),
        test_filter_absence.data([], "j", []),
    ]),
    TestGroup("2.3 Wordle Misplaced", 10, [
        test_filter_misplaced.data(["hippo", "zebra", "panda", "koala"], "a", [2, 3], ["zebra"]),
        test_filter_misplaced.data(["hippo", "zebra", "panda", "koala"], "o", [1, 4], ["hippo", "koala"]),
        test_filter_misplaced.data(["hippo", "zebra", "panda", "koala"], "x", [1, 2, 5], []),
        test_filter_misplaced.data(FUNNY_WORDS, "m", [1, 4], [
            "jumpy", "bumpy", "dumpy", "gamay", "humpy", "comfy",
        ]),
        test_filter_misplaced.data(FUNNY_WORDS, "u", [2, 3], []),
        test_filter_misplaced.data(FUNNY_WORDS, "f", [], [
            "miffy", "foamy", "fuzzy", "jiffy", "comfy", "goofy", "daffy", "biffy", "huffy", "foggy",
        ]),
        test_filter_misplaced.data(FUNNY_WORDS, "y", [3], FUNNY_WORDS),
        test_filter_misplaced.data(FUNNY_WORDS, "o", [1, 2, 3, 4, 5], []),
        test_filter_misplaced.data([], "x", [3, 5], []),
    ]),
    TestGroup("3.1 All Prefixes", 10, [
        test_all_prefixes.data("APPLES", ["", "A", "AP", "APP", "APPL", "APPLE", "APPLES"]),
        test_all_prefixes.data("Hello, World!", [
            "",
            "H",
            "He",
            "Hel",
            "Hell",
            "Hello",
            "Hello,",
            "Hello, ",
            "Hello, W",
            "Hello, Wo",
            "Hello, Wor",
            "Hello, Worl",
            "Hello, World",
            "Hello, World!",
        ]),
        test_all_prefixes.data("👨‍🦱", ["", "👨", "👨\u200d", "👨\u200d🦱"]),
        test_all_prefixes.data("", [""]),
    ]),
    TestGroup("3.2 Longest Common Prefix", 10, [
        test_longest_common_prefix.data("dolphin", "dog", "do"),
        test_longest_common_prefix.data("dog", "cat", ""),
        test_longest_common_prefix.data("anteater", "ant", "ant"),
        test_longest_common_prefix.data("ant", "anteater", "ant"),
        test_longest_common_prefix.data("", "", ""),
    ]),
    TestGroup("4. Appear Once", 10, [
        test_appear_once.data([1, 2, 3, 4, 5, 3, 6, 4, 8], {1, 2, 5, 6, 8}),
        test_appear_once.data([1, 3, 5, 7, 9], {1, 3, 5, 7, 9}),
        test_appear_once.data([1, 1, 2, 2, 3, 3, 3], set()),
        test_appear_once.data([], set()),
    ]),
    TestGroup("5. Column Major Enum Array", 10, [
        test_create_enumerate_array.data(2, 3, np.array([
            [1, 3, 5],
            [2, 4, 6],
        ])),
        test_create_enumerate_array.data(3, 2, np.array([
            [1, 4],
            [2, 5],
            [3, 6],
        ])),
        test_create_enumerate_array.data(1, 1, np.array([[1]])),
    ]),
    TestGroup("6. Rotate Point", 10, [
        test_rotate_point.data(np.array([1, 2]), 90, np.array([-2, 1])),
        test_rotate_point.data(np.array([-4, 1]), -45, np.array([-2.121320343559643, 3.5355339059327373])),
        test_rotate_point.data(np.array([7.25, -4.75]), 108, np.array([2.2771452431836114, 8.362990466420865])),
        test_rotate_point.data(np.array([-12, -16]), -143.13010235415598, np.array([0, 20])),
        test_rotate_point.data(np.array([3, -6]), 0, np.array([3, -6])),
        test_rotate_point.data(np.array([-8, 4]), 360, np.array([-8, 4])),
        test_rotate_point.data(np.array([0, 0]), 17.29, np.array([0, 0])),
    ]),
    TestGroup("7. Remove Negative-Sum Columns", 10, [
        test_remove_neg_sum_cols.data(
            np.array([
                [3, 2, -6, -3, -6],
                [-3, -5, 1, 3, -5],
                [3, 2, 2, -1, 2],
                [-3, 1, -5, -1, -3],
            ]),
            np.array([
                [3, 2],
                [-3, -5],
                [3, 2],
                [-3, 1],
            ]),
        ),
        test_remove_neg_sum_cols.data(
            np.array([
                [-5, -12, -9, -6],
                [-15, 2, 2, -9],
                [-11, -7, -15, 4],
            ]),
            np.array([[], [], []]),
        ),
        test_remove_neg_sum_cols.data(
            np.array([
                [0, 3, 3, 1],
                [4, 0, 3, -2],
                [-1, 2, 4, 3],
            ]),
            np.array([
                [0, 3, 3, 1],
                [4, 0, 3, -2],
                [-1, 2, 4, 3],
            ]),
        ),
        test_remove_neg_sum_cols.data(
            np.array([
                [7, 2, -6],
                [3, -8, -4],
                [-4, -9, -4],
                [-6, 13, 15],
            ]),
            np.array([
                [7, -6],
                [3, -4],
                [-4, -4],
                [-6, 15],
            ]),
        ),
    ]),
    TestGroup("8. Subtract By Row Minimum", 10, [
        test_subtract_by_row_min.data(
            np.array([
                [48, 54, 79, -22, -23],
                [-72, -39, 45, -21, -53],
                [100, 62, -74, 0, 95],
                [99, -2, 58, 12, 60],
            ]),
            np.array([
                [71, 77, 102, 1, 0],
                [0, 33, 117, 51, 19],
                [174, 136, 0, 74, 169],
                [101, 0, 60, 14, 62],
            ]),
        ),
        test_subtract_by_row_min.data(
            np.array([
                [16, 70, 24, -9],
                [90, 76, 49, 91],
                [65, 72, 80, 55],
            ]),
            np.array([
                [25, 79, 33, 0],
                [41, 27, 0, 42],
                [10, 17, 25, 0],
            ]),
        ),
        test_subtract_by_row_min.data(
            np.array([
                [241, 319, 241],
                [254, 266, 118],
            ]),
            np.array([
                [0, 78, 0],
                [136, 148, 0],
            ]),
        ),
    ]),
    TestGroup("9. Common Last Name", 10, [
        test_common_last_name.data(SPORTSDAY_DF, 8),
        test_common_last_name.data(SPORTSDAY_DF[SPORTSDAY_DF.team_color == 'salmon_red'], 4),
        test_common_last_name.data(SPORTSDAY_DF[SPORTSDAY_DF['class'] == 7], 3),
    ]),
    TestGroup("10. Fast Runners", 10, [
        test_fast_runners.data(SPORTSDAY_DF, 'salmon_red', 12.0, {
            ('Angela', 'Williams'),
            ('Emily', 'Flores'),
            ('Gary', 'Martinez'),
            ('Jason', 'Scott'),
            ('Justin', 'Lopez'),
        }),
        test_fast_runners.data(SPORTSDAY_DF, 'caterpillar_green', 11.5, {
            ('Daniel', 'Rodriguez'),
            ('Kathleen', 'Edwards'),
            ('Linda', 'Turner'),
        }),
        test_fast_runners.data(SPORTSDAY_DF, 'whale_blue', 11.0, set()),
    ]),
    TestGroup("11. Best Bowling and Minigolf", 10, [
        test_best_bowling_and_minigolf.data(SPORTSDAY_DF, 8, (291, 18)),
        test_best_bowling_and_minigolf.data(SPORTSDAY_DF, 10, (284, 21)),
        test_best_bowling_and_minigolf.data(SPORTSDAY_DF, 12, (300, 18)),
    ]),
    TestGroup("12. High Jump Averages", 10, [
        test_highjump_averages.data(SPORTSDAY_DF, {
            'caterpillar_green': 93.21265306122449,
            'duckling_yellow': 98.88854166666665,
            'salmon_red': 89.11403846153847,
            'whale_blue': 93.18333333333334,
        }),
        test_highjump_averages.data(SPORTSDAY_DF[SPORTSDAY_DF['class'] == 9], {
            'caterpillar_green': 103.64555555555555,
            'duckling_yellow': 100.98625,
            'salmon_red': 83.57,
            'whale_blue': 90.29,
        }),
        test_highjump_averages.data(SPORTSDAY_DF[SPORTSDAY_DF['class'].isin([7, 11])], {
            'caterpillar_green': 87.44583333333333,
            'duckling_yellow': 101.9042105263158,
            'salmon_red': 90.19999999999999,
            'whale_blue': 96.38307692307693,
        }),
    ]),
])

if __name__ == '__main__':
    program()
