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
        ("a^b", "only supported at pattern boundaries"),
        ("a$b", "only supported at pattern boundaries"),
        ("[a-z", "Unterminated character class"),
        (r"a\1b", "Backreferences"),
        ("(?=abc)def", "Lookaround assertions"),
    ],
)
def test_parser_syntax_errors(parser, invalid_pattern, expected_message):
    with pytest.raises(RegexSyntaxError) as exc_info:
        parser.parse(invalid_pattern)
    assert expected_message in str(exc_info.value)
    assert exc_info.value.position >= 0


def test_parser_boundary_anchors(parser):
    """Verify ^ at start and $ at end are parsed as anchors."""
    ast1 = parser.parse("^abc$")
    assert ast1.has_start_anchor is True
    assert ast1.has_end_anchor is True

    ast2 = parser.parse("^hello")
    assert ast2.has_start_anchor is True
    assert ast2.has_end_anchor is False

    ast3 = parser.parse("world$")
    assert ast3.has_start_anchor is False
    assert ast3.has_end_anchor is True

    ast_empty = parser.parse("^$")
    assert ast_empty.has_start_anchor is True
    assert ast_empty.has_end_anchor is True
    assert ast_empty.type == RegexNodeType.EPSILON

    # Escaped anchors should be treated as literal characters
    ast_esc = parser.parse(r"\^abc\$")
    assert ast_esc.has_start_anchor is False
    assert ast_esc.has_end_anchor is False


def test_parser_character_classes(parser):
    """Verify [a-z], [0-9], and [^a] character class parsing."""
    ast_range = parser.parse("[a-c]")
    assert ast_range.type == RegexNodeType.UNION

    ast_digits = parser.parse(r"[\d]")
    assert ast_digits.type == RegexNodeType.UNION

    ast_neg = parser.parse("[^a]")
    assert ast_neg.type == RegexNodeType.UNION


def test_parser_dot_and_shorthand_escapes(parser):
    r"""Verify dot '.' and shorthands \d, \w, \s expand properly."""
    ast_dot = parser.parse("a.b")
    assert ast_dot.type == RegexNodeType.CONCAT

    ast_d = parser.parse(r"\d+")
    assert ast_d.type == RegexNodeType.PLUS

    ast_w = parser.parse(r"\w*")
    assert ast_w.type == RegexNodeType.STAR


def test_realistic_simplified_patterns_with_classes_and_anchors(parser):
    """Test 5 realistic simplified patterns using classes, shorthands, and anchors."""
    realistic_patterns = [
        r"^[a-z]+@[a-z]+\.[a-z]+$",    # Email pattern
        r"^\d\d\d-\d\d\d\d$",          # Phone number pattern
        r"^user_[a-zA-Z0-9]+$",        # Username pattern
        r"^https?://[a-z0-9]+$",       # URL prefix pattern
        r"^[0-9]+(\.[0-9]+)?$",        # Float decimal pattern
    ]
    for pattern in realistic_patterns:
        ast = parser.parse(pattern)
        assert ast.has_start_anchor is True
        assert ast.has_end_anchor is True
        assert ast.type is not None
