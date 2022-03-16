"""Helps loading Jupyter notebook as a module"""
from __future__ import annotations

import io
import os
import sys
from dataclasses import dataclass, field
from types import ModuleType

from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell
from nbformat import NotebookNode, read
from rich.console import Console
from rich.padding import Padding
from rich.syntax import Syntax
from rich.text import Text

from aibuilders_exam.helpers import code_contains_identifier, rich_time

__all__ = ['NotebookLoader']


@dataclass
class NotebookLoader:
    """Jupyter notebooks module loader.

    This class is adapted from the following URL:
    https://jupyter-notebook.readthedocs.io/en/4.x/examples/Notebook/rstversions/Importing%20Notebooks.html
    """
    #: Whether to add created module to sys.modules
    add_sys_modules: bool = False
    #: Whether to interpret notebook's terminal bang command
    interpret_ipython_cmd: bool = False
    #: Interactive shell object
    shell: InteractiveShell = field(default_factory=InteractiveShell.instance)
    #: Rich console object
    console: Console = field(default_factory=Console)
    #: Show skip cells
    show_skip_cells: bool = False

    def load_module(self, fullname: str, path: str | bytes | os.PathLike) -> ModuleType:
        """Imports a notebook as a module.

        Args:
            fullname: Full name of the module
            path: Path to notebook file
        """
        self.console.print(
            rich_time(),
            "Loading notebook from path",
            repr(os.fspath(path)),
        )
        mod = self._prepare_module(fullname, path)
        nb = self._read_notebook(path)

        # Extra work to ensure that magics that would affect the user_ns
        # actually affect the notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__

        try:
            for cell in nb.cells:
                # Skip non-code cells
                if cell.cell_type != 'code':
                    continue
                # Transform the input to executable Python
                code = self.shell.input_transformer_manager.transform_cell(cell.source)
                # Skip code execution if it contains get_ipython() and that it is not allowed
                if not self.interpret_ipython_cmd and code_contains_identifier(code, 'get_ipython'):
                    core_message = Text.assemble(
                        "Skipping a cell with ipython shell ",
                        Text("(!)", style="grey42"),
                        " or magic ",
                        Text("(%)", style="grey42"),
                        " commands",
                    )
                    if self.show_skip_cells:
                        self.console.print(rich_time(), Text.assemble(core_message, ":"))
                        syntax_object = Syntax(cell.source, "py3", dedent=True, background_color="default")
                        self.console.print(Padding(syntax_object, (1, 4)))
                    else:
                        self.console.print(rich_time(), core_message)
                    continue
                # Run the code in the module
                # TODO: Capture output with contextlib.redirect_stdout
                # https://docs.python.org/3/library/contextlib.html#contextlib.redirect_stdout
                exec(code, mod.__dict__)
        finally:
            self.shell.user_ns = save_user_ns

        self.console.print(rich_time(), "Notebook loaded into module", repr(fullname))
        return mod

    def _read_notebook(self, path: str | bytes | os.PathLike) -> NotebookNode:
        with io.open(path, 'r', encoding='utf-8') as f:
            nb = read(f, as_version=4)
        return nb

    def _prepare_module(self, fullname: str, path: str | bytes | os.PathLike) -> ModuleType:
        mod = ModuleType(fullname)
        mod.__file__ = os.fspath(path)
        mod.__loader__ = self
        mod.__dict__['get_ipython'] = get_ipython
        if self.add_sys_modules:
            sys.modules[fullname] = mod
        return mod
