"""Test runner."""
from __future__ import annotations

import abc
import importlib
import inspect
import unittest
from collections.abc import Callable
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, TypeVar

import pytest
from rich.console import Group, RenderableType
from rich.padding import Padding
from rich.text import Text
from rich.traceback import Traceback
from typing_extensions import Literal, ParamSpec

from nbnursery.config import ApplicationContext
from nbnursery.helpers import BriefTraceback, assert_never, inflect_engine, rich_time

__all__ = [
    'ExecArg', 'ModuleItem', 'Param', 'TestScenario',
    'TestCase', 'TestCaseResult',
    'TestGroup', 'TestGroupResult',
    'TestSuite', 'TestSuiteResult',
]

T = TypeVar('T')
P = ParamSpec('P')

POSITIONAL_ARGS = [inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD]


class ExecArg(metaclass=abc.ABCMeta):
    """Base class for test execution argument"""

    @abc.abstractmethod
    def get_value(self, test_data: TestCase, mod: ModuleType) -> Any:
        """Obtains the argument value from the environment"""
        raise NotImplementedError


@dataclass
class ModuleItem(ExecArg):
    """Indicates looking up an item from the module"""
    item_name: str

    def get_value(self, test_data: TestCase, mod: ModuleType) -> Any:
        return getattr(mod, self.item_name)


@dataclass
class Param(ExecArg):
    """Indicates the parameter name"""

    def get_value(self, test_data: TestCase, mod: ModuleType) -> Any:
        return test_data.params[id(self)]


@dataclass
class TestScenario:
    """Represents a testing scenario (à la pytest function).
    Use decorator ``TestScenario.create`` to create a new test scenario::

        @TestScenario.create(ModuleItem('func_name'), Param(), Param())
        def test_count_even(func: Callable[[int], int], value: int, expected: int) -> None:
            result = func(values)
            assert result == expected
    """
    #: Actual function to execute to run the test
    wrapped_func: Callable
    #: List of metadata of input arguments to the wrapped_func
    exec_args: list[ExecArg]

    @classmethod
    def create(cls, *args: ExecArg):
        """Decorates a function to turn it into a testing function"""

        def wrapper(func: Callable) -> TestScenario:
            name = func.__name__
            sig = inspect.signature(func)
            if not all(fp.kind in POSITIONAL_ARGS for fp in sig.parameters.values()):
                raise TypeError(f"input arguments of wrapped function {name!r} must all be positional")
            if len(sig.parameters) > len(args):
                raise TypeError(f"wrapped function {name!r} has too many input arguments per decorator config")
            if len(sig.parameters) < len(args):
                raise TypeError(f"wrapped function {name!r} does not have enough input arguments decorator config")
            return TestScenario(func, list(args))

        return wrapper

    def data(self, *params) -> TestCase:
        """Produces a test case from the current testing scenario"""
        field_ids = [id(a) for a in self.exec_args if isinstance(a, Param)]
        field_count = len(field_ids)
        param_count = len(params)
        if param_count != field_count:
            raise ValueError(
                f"test data for {self.wrapped_func.__name__!r} expected {field_count} fields "
                f"but instead found {param_count}",
            )
        params = dict(zip(field_ids, params))
        return TestCase(self, params)


@dataclass
class TestCase:
    """A test case is the testing scenario with specific data parameters"""
    #: Parent test scenario
    test_scenario: TestScenario
    #: Decorated parameters of the wrapped test scenario
    params: dict[int, Any]

    def execute(self, ctx: ApplicationContext, mod: ModuleType) -> TestCaseResult:
        """Executes the test case with the specified module"""
        try:
            exec_args = [
                arg.get_value(self, mod)
                for arg in self.test_scenario.exec_args
            ]
            self.test_scenario.wrapped_func(*exec_args)
        except:  # noqa
            traceback_cls = Traceback if ctx.show_stack_trace else BriefTraceback
            suppressed_modules = [unittest, pytest, importlib.import_module('nbnursery')]
            traceback = traceback_cls(suppress=suppressed_modules)
            return TestCaseResult(self, 'mistake', traceback)
        else:
            return TestCaseResult(self, 'accepted')

    def do_skip(self) -> TestCaseResult:
        """Returns the result as if the test was skipped"""
        return TestCaseResult(self, 'skipped')


@dataclass
class TestCaseResult:
    """The result from executing a test case."""
    #: Parent test case
    parent: TestCase
    #: Judgement status
    judgement: Literal['accepted', 'mistake', 'skipped']
    #: Rich traceback object
    rich_traceback: Traceback = None

    @property
    def is_accepted(self) -> bool:
        return self.judgement == 'accepted'

    def rich_message(self, test_no: int) -> RenderableType:
        """Properly formatted rich message of the test case result"""
        if self.judgement == 'accepted':
            label = Text("Correct", style="deep_sky_blue1")
        elif self.judgement == 'mistake':
            label = Text(" MISTAKE FOUND ", style="bold black on red1")
        elif self.judgement == 'skipped':
            label = Text("Skipped", style="grey23")
        else:
            label = assert_never(self.judgement)

        heading = Text.assemble(f"Case #{test_no}: ", label)
        if self.rich_traceback is None:
            return heading
        else:
            return Group(heading, Padding(self.rich_traceback, (0, 4)))


@dataclass
class TestGroup:
    """A group of test cases with the associated score weight"""
    #: Name of the test group
    name: str
    #: Score weight of the test group
    score_weight: int
    #: Collection of test cases
    all_test_cases: list[TestCase]

    def execute(self, ctx: ApplicationContext, mod: ModuleType) -> TestGroupResult:
        """Executes the test group with the specified module"""
        is_accepted = True
        tc_results = []
        for test_case in self.all_test_cases:
            if not is_accepted and not ctx.force_grade_all:
                tc_results.append(test_case.do_skip())
                continue
            result = test_case.execute(ctx, mod)
            is_accepted = is_accepted and result.is_accepted
            tc_results.append(result)
        return TestGroupResult(self, is_accepted, tc_results)


@dataclass
class TestGroupResult:
    """The result from executing a test group"""
    #: Parent test group
    parent: TestGroup
    #: Boolean indicating whether the execution of the test group has passed
    is_accepted: bool
    #: Collection of test case results
    tc_results: list[TestCaseResult]

    @property
    def skipped_testcases(self) -> int:
        """Number of test cases skipped from execution"""
        return sum(tc_result is None for tc_result in self.tc_results)

    @property
    def score_earned(self) -> int:
        """Score earned"""
        return self.is_accepted * self.parent.score_weight

    def serialize(self) -> dict:
        """Obtains a JSON-serializable python object summary of this test group result"""
        return {
            'group_name': self.parent.name,
            'score_weight': self.parent.score_weight,
            'score_earned': self.score_earned,
            'is_accepted': self.is_accepted,
            'sub_results': [tc_result.judgement for tc_result in self.tc_results],
        }

    def rich_message(self) -> RenderableType:
        """Properly formatted rich message of the test group result"""
        rich_body = []
        if not self.parent.all_test_cases:
            rich_body.append(Text("🤷 Empty test cases", style="orange1"))
        for test_no, tc_result in enumerate(self.tc_results, start=1):
            rich_body.append(tc_result.rich_message(test_no))
        if self.is_accepted:
            rich_body.append(Text("🎉 Congratulations!", style="gold1"))
        elif self.skipped_testcases > 0:
            unit = inflect_engine.plural("test", self.skipped_testcases)
            rich_body.append(Text(f"🔧 Skipping {self.skipped_testcases} remaining {unit}", style="orange_red1"))
        else:
            rich_body.append(Text("🔧 Some mistake found, try again", style="orange_red1"))
        return Padding(Group(*rich_body), (0, 4, 1, 4))


@dataclass
class TestSuite:
    """A collection of test groups"""
    test_groups: list[TestGroup]

    def execute(self, ctx: ApplicationContext, mod: ModuleType) -> TestSuiteResult:
        """Executes the test suite with the specified module"""
        tg_results = []
        for test_group in self.test_groups:
            ctx.console.print(rich_time(), "Grading the question:", Text(test_group.name, style="bold cyan1"))
            result = test_group.execute(ctx, mod)
            tg_results.append(result)
            ctx.console.print(result.rich_message())
        return TestSuiteResult(tg_results)


@dataclass
class TestSuiteResult:
    """Keeps track of grading a collection of test groups"""
    tg_results: list[TestGroupResult] = field(default_factory=list)

    @property
    def total_weight(self) -> int:
        return sum(tg_result.parent.score_weight for tg_result in self.tg_results)

    @property
    def score_earned(self) -> int:
        return sum(tg_result.score_earned for tg_result in self.tg_results)

    @property
    def is_perfect(self) -> bool:
        return all(tg_result.is_accepted for tg_result in self.tg_results)

    def serialize(self) -> dict:
        """Obtains a JSON-serializable python object summary of test suite result"""
        return {
            'total_weight': self.total_weight,
            'score_earned': self.score_earned,
            'test_groups': [
                tg_result.serialize()
                for tg_result in self.tg_results
            ],
        }

    def rich_score(self) -> RenderableType:
        """Rich formatted final score"""
        style = "bold bright_green" if self.is_perfect else "bold orange1"
        return Text.assemble(
            Text("Final score: ", style="bold"),
            Text(f"{self.score_earned}/{self.total_weight}", style=style),
        )
