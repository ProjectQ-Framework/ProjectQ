# -*- coding: utf-8 -*-
#   Copyright 2020 ProjectQ-Framework (www.projectq.ch)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Helper module to parse expressions
"""

import math
from numbers import Number
import operator

from pyparsing import (Literal, Word, Group, Forward, alphas, alphanums, Regex,
                       CaselessKeyword, Suppress, delimitedList,
                       pyparsing_common)

# ==============================================================================

EXPR_STACK = []


def push_first(toks):
    """
    Push first token on top of the stack.

    Args:
        toks (pyparsing.Tokens): Pyparsing tokens
    """
    EXPR_STACK.append(toks[0])


def push_unary_minus(toks):
    """
    Push a unary minus operation on top of the stack if required.

    Args:
        toks (pyparsing.Tokens): Pyparsing tokens
    """
    if toks[0] == '-':
        EXPR_STACK.append('unary -')


# ==============================================================================


class ExprParser:
    """
    Expression parser

    Grammar:
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
    """
    def __init__(self):
        # pylint: disable = too-many-locals
        self.var_dict = dict()

        # use CaselessKeyword for e and pi, to avoid accidentally matching
        # functions that start with 'e' or 'pi' (such as 'exp'); Keyword
        # and CaselessKeyword only match whole words
        e_const = CaselessKeyword("E").addParseAction(lambda: math.e)
        pi_const = (CaselessKeyword("PI")
                    | CaselessKeyword("π")).addParseAction(lambda: math.pi)
        # fnumber = Combine(Word("+-"+nums, nums) +
        #                    Optional("." + Optional(Word(nums))) +
        #                    Optional(e + Word("+-"+nums, nums)))
        # or use provided pyparsing_common.number, but convert back to str:
        # fnumber = ppc.number().addParseAction(lambda t: str(t[0]))
        fnumber = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?")
        fnumber = pyparsing_common.number
        cname = Word(alphas + "_", alphanums + '_')
        int_v = pyparsing_common.integer

        plus, minus, mult, div = map(Literal, "+-*/")
        lpar, rpar, lbra, rbra = map(Suppress, "()[]")
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")

        expr = Forward()
        expr_list = delimitedList(Group(expr))

        # add parse action that replaces the function identifier with a (name,
        # number of args) tuple
        def insert_fn_argcount_tuple(toks):
            fn_name = toks.pop(0)
            num_args = len(toks[0])
            toks.insert(0, (fn_name, num_args))

        var_expr = (cname + (lbra + int_v + rbra)[...]).addParseAction(
            self._eval_var_expr)

        fn_call = (cname + lpar - Group(expr_list) +
                   rpar).setParseAction(insert_fn_argcount_tuple)
        atom = (addop[...] +
                ((fn_call | pi_const | e_const | var_expr | fnumber
                  | cname).setParseAction(push_first)
                 | Group(lpar + expr + rpar))).setParseAction(push_unary_minus)

        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left
        # exponents, instead of left-to-right that is, 2^3^2 = 2^(3^2), not
        # (2^3)^2.
        factor = Forward()
        factor <<= atom + (expop + factor).setParseAction(push_first)[...]
        term = factor + (multop + factor).setParseAction(push_first)[...]
        expr <<= term + (addop + term).setParseAction(push_first)[...]
        self.bnf = expr

    def parse(self, expr):
        """
        Parse an expression.

        Args:
            expr (str): Expression to evaluate
        """
        return self.bnf.parseString(expr, parseAll=True)

    def set_var_dict(self, var_dict):
        """
        Set the internal variable dictionary.

        Args:
            var_dict (dict): Dictionary of variables with their corresponding
                value for substitution.
        """
        self.var_dict = var_dict

    def _eval_var_expr(self, toks):
        """
        Evaluate an expression containing a variable.

        Name matching keys in the internal variable dictionary have their
        values substituted.

        Args:
            toks (pyparsing.Tokens): Pyparsing tokens
        """
        if len(toks) == 1:
            return self.var_dict[toks[0]]

        value, index = toks
        value = self.var_dict[value]

        if isinstance(value, list):
            return value[index]

        if isinstance(value, int):
            # Might be faster than (value >> index) & 1
            return int(bool(value & (1 << index)))

        # TODO: Properly handle other types...
        return value


# map operator symbols to corresponding arithmetic operations
EPSILON = 1e-12
opn = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "^": operator.pow,
}

fn = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "exp": math.exp,
    "abs": abs,
    "trunc": int,
    "round": round,
    "sgn": lambda a: -1 if a < -EPSILON else 1 if a > EPSILON else 0,
    "all": lambda *a: all(a),
    "float": float,
    "int": int,
    "bool": bool,
}


def evaluate_stack(stack):
    """
    Evaluate a stack of operations.

    Args:
        stack (list): Expression stack

    Returns:
        Result of evaluating the operation at the top of the stack.
    """
    # pylint: disable=invalid-name

    op, num_args = stack.pop(), 0
    if isinstance(op, tuple):
        op, num_args = op

    if isinstance(op, Number):
        return op

    if op == "unary -":
        return -evaluate_stack(stack)

    if op in "+-*/^":
        # note: operands are pushed onto the stack in reverse order
        op2 = evaluate_stack(stack)
        op1 = evaluate_stack(stack)
        return opn[op](op1, op2)

    if op in fn:
        # note: args are pushed onto the stack in reverse order
        args = reversed([evaluate_stack(stack) for _ in range(num_args)])
        return fn[op](*args)

    # try to evaluate as int first, then as float if int fails
    try:
        return int(op)
    except ValueError:
        return float(op)


_parser = ExprParser()


def eval_expr(expr_str, var_dict=None):
    """
    Evaluate a mathematical expression.

    Args:
        expr_str (str): Expression to evaluate
        var_dict (dict): Dictionary of variables with their corresponding
            value for substitution.

    Returns:
        Result of evaluation.
    """
    # pylint: disable = global-statement
    global EXPR_STACK
    EXPR_STACK = []

    _parser.set_var_dict(var_dict if var_dict else dict())
    _parser.parse(expr_str)
    return evaluate_stack(EXPR_STACK[:])
