from typing import List, Optional


class FetchOptions:
    def __init__(
        self,
        tracksAssignment: Optional[bool] = None,
        tracksExposure: Optional[bool] = None,
        flagKeys: Optional[List[str]] = None,
    ):
        """
        Fetch Options
            Parameters:
                tracksAssignment (Optional[bool]): Whether to track the assignment. The default None uses the server's default behavior (track the assignment event).
                tracksExposure (Optional[bool]): Whether to track the exposure. The default None uses the server's default behavior (don't track the exposure event).
                flagKeys (Optional[List[str]]): Specific flag keys to evaluate and set variants for.
        """
        self.tracksAssignment = tracksAssignment
        self.tracksExposure = tracksExposure
        self.flagKeys = flagKeys

    def __str__(self):
        return (f"FetchOptions(tracksAssignment={self.tracksAssignment}, "
                f"tracksExposure={self.tracksExposure}, flagKeys={self.flagKeys})")
