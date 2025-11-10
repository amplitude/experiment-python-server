"""
The official Amplitude Experiment Python Server SDK
.. include:: ../../README.md
"""

from .remote.client import RemoteEvaluationClient
from .remote.config import RemoteEvaluationConfig
from .variant import Variant
from .user import User
from .version import __version__
from .factory import Experiment
from .cookie import AmplitudeCookie
from .local.client import LocalEvaluationClient
from .local.config import LocalEvaluationConfig
from .server_zone import ServerZone
from .assignment import AssignmentConfig
from .cohort.cohort_sync_config import CohortSyncConfig
