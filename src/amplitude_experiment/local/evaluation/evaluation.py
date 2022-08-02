from .libevaluation_interop import libevaluation_interop_symbols


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
    return str(result, 'utf-8')
