"""
Unit Tests for Regex Parser (Member A)
======================================
Tests AST construction for valid regexes and error handling for malformed syntax.
"""

import pytest
from backend.automata_engine.regex_parser.parser import (
    RegexParser,
    RegexNode,
    RegexNodeType,
    RegexSyntaxError,
)


@pytest.fixture
def parser():
    return RegexParser()


def test_parser_literals_and_concat(parser):
    ast = parser.parse("ab")
    assert ast.type == RegexNodeType.CONCAT
    assert ast.left.type == RegexNodeType.LITERAL
    assert ast.left.value == "a"
    assert ast.right.type == RegexNodeType.LITERAL
    assert ast.right.value == "b"


def test_parser_alternation(parser):
    ast = parser.parse("a|b")
    assert ast.type == RegexNodeType.UNION
    assert ast.left.value == "a"
    assert ast.right.value == "b"


def test_parser_kleene_star(parser):
    ast = parser.parse("a*")
    assert ast.type == RegexNodeType.STAR
    assert ast.child.value == "a"


def test_parser_plus_and_question(parser):
    ast = parser.parse("a+b?")
    assert ast.type == RegexNodeType.CONCAT
    assert ast.left.type == RegexNodeType.PLUS
    assert ast.left.child.value == "a"
    assert ast.right.type == RegexNodeType.QUESTION
    assert ast.right.child.value == "b"


def test_parser_grouping_precedence(parser):
    # (a|b)*abb
    ast = parser.parse("(a|b)*abb")
    assert ast.type == RegexNodeType.CONCAT
    # Check rightmost is literal 'b'
    assert ast.right.value == "b"


def test_parser_epsilon_representations(parser):
    # empty parentheses
    ast1 = parser.parse("()")
    assert ast1.type == RegexNodeType.EPSILON

    # literal epsilon character
    ast2 = parser.parse("ε")
    assert ast2.type == RegexNodeType.EPSILON

    # alternation with epsilon: a|()
    ast3 = parser.parse("a|()")
    assert ast3.type == RegexNodeType.UNION
    assert ast3.right.type == RegexNodeType.EPSILON


def test_parser_escapes(parser):
    ast = parser.parse(r"\*\|\+\?")
    assert ast.type == RegexNodeType.CONCAT
    # Should parse escaped characters as literals
    literals = []
    curr = ast
    while curr.type == RegexNodeType.CONCAT:
        literals.append(curr.right.value)
        curr = curr.left
    literals.append(curr.value)
    assert literals[::-1] == ["*", "|", "+", "?"]


@pytest.mark.parametrize(
    "invalid_pattern,expected_message",
    [
        ("", "cannot be empty"),
        ("(a|b", "Unbalanced parenthesis"),
        ("a)", "Unexpected closing parenthesis"),
        ("*a", "Dangling operator '*'"),
        ("+b", "Dangling operator '+'"),
        ("?c", "Dangling operator '?'"),
        ("a|", "Empty alternation branch after '|'"),
        ("|b", "Empty alternation branch before '|'"),
        ("a||b", "Empty alternation branch between '||'"),
        ("a++", "Multiple repeat operators"),
        ("a**", "Multiple repeat operators"),
        (r"abc\\"[0:4], "Dangling escape character"),
    ],
)
def test_parser_syntax_errors(parser, invalid_pattern, expected_message):
    with pytest.raises(RegexSyntaxError) as exc_info:
        parser.parse(invalid_pattern)
    assert expected_message in str(exc_info.value)
    assert exc_info.value.position >= 0
