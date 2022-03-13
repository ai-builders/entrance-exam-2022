"""Core application configuration to pass around the application"""
from __future__ import annotations

from dataclasses import InitVar, dataclass, field

from rich.console import Console

__all__ = ['ApplicationContext']


@dataclass
class ApplicationContext:
    """Application-wide context object"""
    #: Whether to grade every test case in each test group
    #: Set this value to True to keep grading even after encountering the first mistake in each test group
    force_grade_all: bool = False
    #: Whether to always return exit status 0 even mistakes were found during grading
    always_zero_exit: bool = False
    #: Verbosity level of the output
    verbosity: int = field(init=False)
    #: Rich console object
    console: Console = field(init=False)
    #: Number of verbose flag from command line
    verbose: InitVar[int] = 0
    #: Number of quiet flag from command line
    quiet: InitVar[int] = 0
    #: Width of the terminal from the command line
    width: InitVar[int] = None
    #: Height of the terminal from the command line
    height: InitVar[int] = None
    #: Whether to force terminal color output
    force_color: InitVar[bool] = None

    def __post_init__(self, verbose: int, quiet: int, width: int, height: int, force_color: bool):
        self.verbosity = verbose - quiet
        self.console = Console(force_terminal=force_color, quiet=self.verbosity < 0, width=width, height=height)

    @property
    def show_skip_cells(self) -> bool:
        """Whether to display skipped cells while loading a notebook file.
        True if and only if verbosity level is at least 2.
        """
        return self.verbosity >= 2

    @property
    def show_stack_trace(self) -> bool:
        """Whether to show complete stack trace from grading notebook files.
        True if and only if verbosity level is at least 1."""
        return self.verbosity >= 1
