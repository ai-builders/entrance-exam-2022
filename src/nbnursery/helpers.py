"""Miscellaneous helper functions"""
from __future__ import annotations

import ast
import datetime as dt
from dataclasses import dataclass, field

import click
import inflect
from pygments.token import Comment, Keyword, Name, Number, Operator, String, Text as TextToken, Token
from rich.console import Console, ConsoleOptions, RenderResult, RenderableType
from rich.constrain import Constrain
from rich.highlighter import ReprHighlighter
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.theme import Theme
from rich.traceback import Traceback
from typing_extensions import NoReturn

__all__ = [
    'inflect_engine', 'code_contains_identifier', 'assert_never',
    'rich_time', 'BriefTraceback', 'validate_pos',
]

inflect_engine = inflect.engine()


########################
# Abstract Syntax Tree #
########################

@dataclass
class _IdentifierSearcher(ast.NodeVisitor):
    id_name: str
    result: bool = field(init=False, default=False)

    def visit_Name(self, node):
        if node.id == self.id_name:
            self.result = True
        self.generic_visit(node)


def code_contains_identifier(code: ast.AST | str, id_name: str) -> bool:
    """Finds whether a given Python abstract syntax tree contains the specified identifier name.
    """
    tree = compile(code, '<string>', 'exec', ast.PyCF_ONLY_AST)
    finder = _IdentifierSearcher(id_name)
    finder.visit(tree)
    return finder.result


##########
# Typing #
##########

def assert_never(x: NoReturn) -> NoReturn:
    """Helping function to ensure exhaustive covering of sum types in conditional statements.
    Taken from https://github.com/python/typing/issues/735.
    """
    raise TypeError(f"Invalid value: {x!r}")


###################
# Rich Formatting #
###################

def rich_time(time: dt.time = None) -> RenderableType:
    """Formats the timestamp with rich formatting.
    Defaults to current time if the input argument is not provided.
    """
    if time is None:
        time = dt.datetime.now().time()
    time = time.isoformat('seconds')
    return Text.assemble(f"[{time}]", style="spring_green4")


class BriefTraceback(Traceback):
    """Rich-enabled traceback coloring with stack trace"""

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        theme = self.theme
        background_style = theme.get_background_style()
        token_style = theme.get_style_for_token

        traceback_theme = Theme(
            {
                "pretty": token_style(TextToken),
                "pygments.text": token_style(Token),
                "pygments.string": token_style(String),
                "pygments.function": token_style(Name.Function),
                "pygments.number": token_style(Number),
                "repr.indent": token_style(Comment) + Style(dim=True),
                "repr.str": token_style(String),
                "repr.brace": token_style(TextToken) + Style(bold=True),
                "repr.number": token_style(Number),
                "repr.bool_true": token_style(Keyword.Constant),
                "repr.bool_false": token_style(Keyword.Constant),
                "repr.none": token_style(Keyword.Constant),
                "scope.border": token_style(String.Delimiter),
                "scope.equals": token_style(Operator),
                "scope.key": token_style(Name),
                "scope.key.special": token_style(Name.Constant) + Style(dim=True),
            },
            inherit=False,
        )

        highlighter = ReprHighlighter()
        stack = self.trace.stacks[0]
        if stack.syntax_error is not None:
            with console.use_theme(traceback_theme):
                yield Constrain(
                    Panel(
                        self._render_syntax_error(stack.syntax_error),
                        style=background_style,
                        border_style="traceback.border.syntax_error",
                        expand=True,
                        padding=(0, 1),
                        width=self.width,
                    ),
                    self.width,
                )
            yield Text.assemble(
                (f"{stack.exc_type}: ", "traceback.exc_type"),
                highlighter(stack.syntax_error.msg),
            )
        elif stack.exc_value:
            yield Text.assemble(
                (f"{stack.exc_type}: ", "traceback.exc_type"),
                highlighter(stack.exc_value),
            )
        else:
            yield Text.assemble((f"{stack.exc_type}", "traceback.exc_type"))


#################
# Click Helpers #
#################

def validate_pos(ctx, param, value):
    """Callback function for click parameters to ensure the value is positive"""
    if value is None or value > 0:
        return value
    raise click.BadParameter("value must be positive")
