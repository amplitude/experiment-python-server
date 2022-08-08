from .remote.client import RemoteEvaluationClient
from .remote.config import RemoteEvaluationConfig
from .local.client import LocalEvaluationClient
from .local.config import LocalEvaluationConfig

remote_evaluation_instances = {}
local_evaluation_instances = {}
default_instance = '$default_instance'


class Experiment:
    """Provides factory methods for storing singleton instance of Client"""

    @staticmethod
    def initialize_remote(api_key: str, config: RemoteEvaluationConfig = None) -> RemoteEvaluationClient:
        """
        Initializes a singleton Client. This method returns a default singleton instance, subsequent calls to
        init will return the initial instance regardless of input.
            Parameters:
                api_key (str): The Amplitude API Key
                config (RemoteEvaluationConfig): Optional Config

            Returns:
                The remote evaluation client.
        """
        if remote_evaluation_instances.get(default_instance) is None:
            remote_evaluation_instances[default_instance] = RemoteEvaluationClient(api_key, config)
        return remote_evaluation_instances[default_instance]

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
                The local evaluation client.
        """
        if local_evaluation_instances.get(default_instance) is None:
            local_evaluation_instances[default_instance] = LocalEvaluationClient(api_key, config)
        return local_evaluation_instances[default_instance]
