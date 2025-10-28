from typing import Optional
class FetchOptions:
    def __init__(self, tracksAssignment: Optional[bool] = None, tracksExposure: Optional[bool] = None):
        """
        Fetch Options
            Parameters:
                tracksAssignment (Optional[bool]): Whether to track the assignment. The default None means track the assignment event.
                tracksExposure (Optional[bool]): Whether to track the exposure. The default None means don't track the exposure event.
        """
        self.tracksAssignment = tracksAssignment
        self.tracksExposure = tracksExposure

    def __str__(self):
        return f"FetchOptions(tracksAssignment={self.tracksAssignment}, tracksExposure={self.tracksExposure})"
