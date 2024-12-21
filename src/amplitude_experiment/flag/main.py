import json
import logging
import time

from amplitude_experiment.flag import FlagConfigStreamApi, FlagConfigStreamer
from amplitude_experiment.flag.flag_config_storage import FlagConfigStorage, InMemoryFlagConfigStorage
from amplitude_experiment.flag.flag_config_updater import DummyUpdater, FlagConfigUpdaterFallbackRetryWrapper

if __name__ == '__main__':
    logger = logging.Logger("a")
    api = FlagConfigStreamApi('server-tUTqR62DZefq7c73zMpbIr1M5VDtwY8T', 'https://skylab-stream.stag2.amplitude.com', 1500, 1000 * 5, 0)
    storage = InMemoryFlagConfigStorage()
    # streamer = FlagConfigStreamer(api, storage, None, None, logger)

    dummy1 = DummyUpdater("dummy 1")
    # dummy1.start_fail = True
    dummy1.fail = True
    dummy2 = DummyUpdater("dummy 2")
    dummy2.start_fail = True
    streamer = FlagConfigUpdaterFallbackRetryWrapper(dummy1, dummy2, logger)

    print("start")
    streamer.start(print)
    # print(storage.get_flag_configs())
    time.sleep(20)

    streamer.stop()
    print("done")