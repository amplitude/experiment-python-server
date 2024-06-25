from .remote.client import RemoteEvaluationClient
from .remote.config import RemoteEvaluationConfig
from .local.client import LocalEvaluationClient
from .local.config import LocalEvaluationConfig

remote_evaluation_instances = {}
local_evaluation_instances = {}


class Experiment:
    """Provides factory methods for storing instances of Client"""

    @staticmethod
    def initialize_remote(api_key: str, config: RemoteEvaluationConfig = None) -> RemoteEvaluationClient:
        """
        Initializes a remote evaluation client.
            Parameters:
                api_key (str): The Amplitude API Key
                config (RemoteEvaluationConfig): Optional Config

            Returns:
                A remote evaluation client.
        """
        if remote_evaluation_instances.get(api_key) is None:
            remote_evaluation_instances[api_key] = RemoteEvaluationClient(api_key, config)
        return remote_evaluation_instances[api_key]

    @staticmethod
    def initialize_local(api_key: str, config: LocalEvaluationConfig = None) -> LocalEvaluationClient:
        """
        Initialize a local evaluation client. A local evaluation client can evaluate local flags or experiments for a
        user without requiring a remote call to the amplitude evaluation server. In order to best leverage local
        evaluation, all flags, and experiments being evaluated server side should be configured as local.
            Parameters:
                api_key (str): The Amplitude API Key
                config (RemoteEvaluationConfig): Optional Config

            Returns:
                A local evaluation client.
        """
        if local_evaluation_instances.get(api_key) is None:
            local_evaluation_instances[api_key] = LocalEvaluationClient(api_key, config)
        return local_evaluation_instances[api_key]
