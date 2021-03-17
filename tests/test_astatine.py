# stdlib
import ast
import sys
from types import ModuleType

# 3rd party
import pytest
from coincidence import AdvancedDataRegressionFixture, check_file_regression
from pytest_regressions.file_regression import FileRegressionFixture

# this package
from astatine import (
		get_docstring_lineno,
		get_toplevel_comments,
		is_type_checking,
		kwargs_from_node,
		mark_text_ranges
		)

docstring_ast: ModuleType

try:
	# 3rd party
	import typed_ast.ast3 as docstring_ast  # type: ignore
except ImportError:
	docstring_ast = ast


@pytest.mark.parametrize(
		"source",
		[
				pytest.param("#! /usr/bin/env python3", id="shebang"),
				pytest.param("# coding=utf-8", id="coding1"),
				pytest.param("# -*- coding: utf-8 -*-", id="coding2"),
				pytest.param("#! /usr/bin/env python3\n# -*- coding: utf-8 -*-", id="coding_shebang"),
				pytest.param(
						"#! /usr/bin/env python3\n# -*- coding: utf-8 -*-\n\nimport foo\nprint('hello everyone!')\n",
						id="code_a"
						),
				pytest.param(
						'#! /usr/bin/env python3\n# -*- coding: utf-8 -*-\n\n"""\nA docstring\n"""\n# a comment',
						id="docstring"
						),
				]
		)
def test_get_toplevel_comments(source: str, file_regression: FileRegressionFixture):
	check_file_regression(get_toplevel_comments(source), file_regression)


@pytest.mark.parametrize(
		"source, expected",
		[
				pytest.param("if False:\n\tpass", True, id="False"),
				pytest.param(
						"from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n\tpass",
						True,
						id="TYPE_CHECKING",
						),
				pytest.param(
						"import typing\nif typing.TYPE_CHECKING:\n\tpass",
						True,
						id="typing.TYPE_CHECKING",
						),
				pytest.param(
						"import typing\nimport foo\nif typing.TYPE_CHECKING or foo.BAR:\n\tpass",
						True,
						id="BoolOp",
						),
				pytest.param(
						"import sys\nif sys.version_info < (3, 10):\n\tpass",
						False,
						id="sys.version_info",
						),
				]
		)
def test_is_type_checking(source: str, expected: bool):
	tree = ast.parse(source)

	class Visitor(ast.NodeVisitor):

		def visit_If(self, node: ast.If):
			print(node, node.test)
			assert is_type_checking(node) is expected

	Visitor().visit(tree)


def parse_and_get_child(source: str, child: int) -> ast.AST:
	node = docstring_ast.parse(source)  # type: ignore
	return node.body[child]


@pytest.mark.parametrize(
		"node, expected",
		[
				pytest.param(
						parse_and_get_child("class F:\n\t'''\n\tA Docstring\n\t'''", 0),
						2,
						id="class",
						),
				pytest.param(
						parse_and_get_child(
								"import collections\nimport typing\n\nclass F:\n\t'''\n\tA Docstring\n\t'''", 2
								),
						5,
						id="class_with_imports",
						),
				pytest.param(
						parse_and_get_child(
								"# coding=utf-8\nimport collections\nimport typing\n\nclass F:\n\t'''\n\tA Docstring\n\t'''",
								2
								),
						6,
						id="class_with_imports_and_comments",
						),
				pytest.param(
						parse_and_get_child("def foo():\n\t'''\n\tA Docstring\n\t'''", 0),
						2,
						id="function",
						),
				pytest.param(
						parse_and_get_child(
								"import collections\nimport typing\n\ndef foo():\n\t'''\n\tA Docstring\n\t'''", 2
								),
						5,
						id="function_with_imports",
						),
				pytest.param(
						parse_and_get_child(
								"# coding=utf-8\nimport collections\nimport typing\n\ndef foo():\n\t'''\n\tA Docstring\n\t'''",
								2
								),
						6,
						id="function_with_imports_and_comments",
						),
				],
		)
def test_get_docstring_lineno(node: ast.AST, expected: int):
	assert get_docstring_lineno(node) == expected  # type: ignore


@pytest.mark.parametrize(
		"source",
		[
				pytest.param("#! /usr/bin/env python3", id="shebang"),
				pytest.param("# coding=utf-8", id="coding1"),
				pytest.param("# -*- coding: utf-8 -*-", id="coding2"),
				pytest.param("#! /usr/bin/env python3\n# -*- coding: utf-8 -*-", id="coding_shebang"),
				pytest.param(
						"#! /usr/bin/env python3\n# -*- coding: utf-8 -*-\n\nimport foo\nprint('hello everyone!')\n",
						id="code_a"
						),
				pytest.param(
						'#! /usr/bin/env python3\n# -*- coding: utf-8 -*-\n\n"""\nA docstring\n"""\n# a comment',
						id="docstring"
						),
				pytest.param("if False:\n\tpass", id="False"),
				pytest.param(
						"from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n\tpass",
						id="TYPE_CHECKING",
						),
				pytest.param(
						"import typing\nif typing.TYPE_CHECKING:\n\tpass",
						id="typing.TYPE_CHECKING",
						),
				pytest.param(
						"import typing\nimport foo\nif typing.TYPE_CHECKING or foo.BAR:\n\tpass",
						id="BoolOp",
						),
				pytest.param(
						"import sys\nif sys.version_info < (3, 10):\n\tpass",
						id="sys.version_info",
						),
				pytest.param(
						"class F:\n\t'''\n\tA Docstring\n\t'''",
						id="class",
						),
				pytest.param(
						"import collections\nimport typing\n\nclass F:\n\t'''\n\tA Docstring\n\t'''",
						id="class_with_imports",
						),
				pytest.param(
						"# coding=utf-8\nimport collections\nimport typing\n\nclass F:\n\t'''\n\tA Docstring\n\t'''",
						id="class_with_imports_and_comments",
						),
				pytest.param(
						"def foo():\n\t'''\n\tA Docstring\n\t'''",
						id="function",
						),
				pytest.param(
						"import collections\nimport typing\n\ndef foo():\n\t'''\n\tA Docstring\n\t'''",
						id="function_with_imports",
						),
				pytest.param(
						"# coding=utf-8\nimport collections\nimport typing\n\ndef foo():\n\t'''\n\tA Docstring\n\t'''",
						id="function_with_imports_and_comments",
						),
				]
		)
def test_mark_text_ranges(source: str, advanced_data_regression: AdvancedDataRegressionFixture):
	tree = ast.parse(source)

	mark_text_ranges(tree, source)

	for child in ast.walk(tree):
		if hasattr(child, "last_token"):
			assert child.end_lineno  # type: ignore
			assert child.end_col_offset is not None  # type: ignore

			if hasattr(child, "lineno"):
				assert child.lineno
				assert child.col_offset is not None

	# TODO: check the output


def demo_function(arg1, arg2, arg3):
	pass


@pytest.mark.parametrize(
		"source, posarg_names,  expects",
		[
				("foo(1, 2, 3)", ("arg1", "arg2", "arg3"), {"arg1": 1, "arg2": 2, "arg3": 3}),
				("foo(1, 2, 3)", demo_function, {"arg1": 1, "arg2": 2, "arg3": 3}),
				]
		)
def test_kwargs_from_node(source, posarg_names, expects):
	tree = ast.parse(source)
	node = tree.body[0].value

	result = kwargs_from_node(node, posarg_names)

	if sys.version_info >= (3, 8):
		assert {k: v.value for k, v in result.items()} == expects
	else:
		assert {k: v.n for k, v in result.items()} == expects
