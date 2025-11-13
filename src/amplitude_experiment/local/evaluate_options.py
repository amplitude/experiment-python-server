from typing import Optional, Set


class EvaluateOptions:
    """
    Options for evaluating variants for a user.
    """
    def __init__(self, flag_keys: Optional[Set[str]] = None, tracks_exposure: Optional[bool] = None):
        """
        Initialize EvaluateOptions.
        
        Args:
            flag_keys: The flags to evaluate with the user. If None, all flags are evaluated.
            tracks_exposure: Whether to track exposure event for the evaluation.
        """
        self.flag_keys = flag_keys
        self.tracks_exposure = tracks_exposure

