from .libevaluation_interop import libevaluation_interop_symbols
from ctypes import cast, c_char_p

def evaluate(rules: str, user: str) -> str:
    """
    Local evaluation wrapper.
        Parameters:
            rules (str): rules JSON string
            user (str): user JSON string

        Returns:
            Evaluation results with variants in JSON
    """
    result = libevaluation_interop_symbols().contents.kotlin.root.evaluate(rules, user)
    py_result = cast(result, c_char_p).value
    libevaluation_interop_symbols().contents.DisposeString(result)
    return str(py_result, 'utf-8')
