from typing import Optional


class EvaluateOptions:
    """
    Options for evaluating variants for a user.
    """
    def __init__(self, tracks_exposure: Optional[bool] = None):
        """
        Initialize EvaluateOptions.
        
        Args:
            tracks_exposure: Whether to track exposure event for the evaluation.
        """
        self.tracks_exposure = tracks_exposure

