import re
import numpy as np

from bingo.symbolic_regression.agraph.agraph import AGraph
from bingo.symbolic_regression.agraph.operator_definitions import *

operators = {"+", "-", "*", "/", "^"}
precedence = {"+": 0, "-": 0, "*": 1, "/": 1, "^": 2}
operator_map = {"+": ADDITION, "-": SUBTRACTION, "*": MULTIPLICATION,
                "/": DIVISION, "^": POWER, "X": VARIABLE, "C": CONSTANT}
var_or_const_pattern = re.compile(r"([XC])_(\d+)")


def convert_to_postfix(infix_tokens):  # based on Shunting-yard algorithm
    # can use function version on wikipedia for sin, cos, etc.
    # https://en.wikipedia.org/wiki/Shunting-yard_algorithm
    stack = []  # index -1 = top
    output = []
    for token in infix_tokens:
        if token in operators:
            while len(stack) > 0 and stack[-1] in operators and precedence[stack[-1]] >= precedence[token]:
                output.append(stack.pop())
            stack.append(token)
        elif token == "(":
            stack.append(token)
        elif token == ")":
            while stack[-1] != "(":
                if len(stack) == 0:
                    raise RuntimeError("Mismatched parenthesis")
                output.append(stack.pop())
            stack.pop()  # get rid of "("
        else:
            output.append(token)

    for token in stack:
        if token == "(":
            raise RuntimeError("Mismatched parenthesis")
        output.append(token)

    return output


def postfix_to_agraph(postfix_tokens):
    stack = []  # -1 = top (the data structure, not a command_array)
    command_array = []
    i = 0
    for token in postfix_tokens:
        if token in operators:
            operands = stack.pop(), stack.pop()
            command_array.append([operator_map[token], operands[1], operands[0]])
            stack.append(i)
            i += 1
        else:
            match = var_or_const_pattern.fullmatch(token)
            if match:
                groups = match.groups()
                command_array.append([operator_map[groups[0]], int(groups[1]), int(groups[1])])
            stack.append(i)
            i += 1

    if len(stack) > 1:
        raise RuntimeError("Error evaluating postfix expression")
    return command_array


if __name__ == '__main__':
    # expression = "a+b*(c^d-e)^(f+g*h)-i"
    expression = "X_0 + X_1 + C_0 + C_1".split(" ")
    # expression = "(A + B) * (C + D)".replace(" ", "")
    # expression = "(a+b)"
    # infix = list(expression)
    postfix = convert_to_postfix(expression)
    print(postfix)
    command_array = postfix_to_agraph(postfix)
    print(command_array)
    test_graph = AGraph()
    test_graph.command_array = np.array(command_array, dtype=int)
    print(test_graph)
