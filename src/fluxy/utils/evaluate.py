import simpleeval
import ast
import operator
import pandas as pd
import numpy as np

from typing import Sequence


class MathEvaluator(simpleeval.EvalWithCompoundTypes):
    """Custom simpleeval evaluator class with compound type support.
    """
    def __init__(self, operators=None, functions=None, names=None,
                 allowed_attrs=None):
        super().__init__(operators, functions, names, allowed_attrs)
        self.operators[ast.Pow] = operator.pow

    def eval(self, expr, previously_parsed=None):
        return super().eval(str(expr), previously_parsed)


def get_math_evaluator_fn(df: pd.DataFrame):
    """This function must be registering the DataFrame columns as variables
    in the evaluator engine before returning the evaluator.
    """
    e = MathEvaluator(names=df)
    return e.eval


