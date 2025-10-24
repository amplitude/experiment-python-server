class FetchOptions:
    def __init__(self, tracksAssignment: bool | None = None, tracksExposure: bool | None = None):
        """
        Fetch Options
            Parameters:
                tracksAssignment (bool | None): Whether to track the assignment. The default None means track the assignment event.
                tracksExposure (bool | None): Whether to track the exposure. The default None means don't track the exposure event.
        """
        self.tracksAssignment = tracksAssignment
        self.tracksExposure = tracksExposure

    def __str__(self):
        return f"FetchOptions(tracksAssignment={self.tracksAssignment}, tracksExposure={self.tracksExposure})"
