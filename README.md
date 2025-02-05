<p align="center">
  <a href="https://amplitude.com" target="_blank" align="center">
    <img src="https://static.amplitude.com/lightning/46c85bfd91905de8047f1ee65c7c93d6fa9ee6ea/static/media/amplitude-logo-with-text.4fb9e463.svg" width="280">
  </a>
  <br />
</p>

[![PyPI version](https://badge.fury.io/py/amplitude-experiment.svg)](https://badge.fury.io/py/amplitude-experiment)

# Experiment Python SDK
Amplitude Python Server SDK for Experiment.

## Installation
```python
pip install amplitude-experiment
```

## Remote Evaluation Quick Start
```python
from amplitude_experiment import Experiment, RemoteEvaluationConfig, RemoteEvaluationClient, User

# (1) Get your deployment's API key
apiKey = 'YOUR-API-KEY'

# (2) Initialize the experiment remote evaluation
experiment = Experiment.initialize_remote(api_key)

# (3) Fetch variants for a user
user = User(
    device_id="abcdefg",
    user_id="user@company.com",
    user_properties={
        'premium': True
    }
)

# (4) Lookup a flag's variant
#
# To fetch synchronous
variants = experiment.fetch(user)
variant = variants['YOUR-FLAG-KEY']
if variant:
    if variant.value == 'on':
        # Flag is on
    else:
        # Flag is off

# To fetch asynchronous
experiment.fetch_async(user, fetch_callback)

def fetch_callback(user, variants):
    variant = variants['YOUR-FLAG-KEY']
    if variant:
        if variant.value == 'on':
            # Flag is on
        else:
            # Flag is off

```

## Local Evaluation Quick Start
```python
# (1) Initialize the local evaluation client with a server deployment key.
experiment = Experiment.initialize_local(api_key)

# (2) Start the local evaluation client.
experiment.start()

# (3) Evaluate a user.
user = User(
    device_id="abcdefg",
    user_id="user@company.com",
    user_properties={
        'premium': True
    }
)
variants = experiment.evaluate(user)
```

# Running Unit Tests Suite
To setup for running test on local, create a `.env` file with following
contents, and replace `{API_KEY}` and `{SECRET_KEY}` (or `{EU_API_KEY}` and `{EU_SECRET_KEY}` for EU data center) for the project in test:

```
API_KEY={API_KEY}
SECRET_KEY={SECRET_KEY}
```

## More Information
Please visit our :100:[Developer Center](https://www.docs.developers.amplitude.com/experiment/sdks/python-sdk/) for more instructions on using our the SDK.

See our [Experiment Python SDK Docs](https://amplitude.github.io/experiment-python-server/) for a list and description of all available SDK methods.

## Need Help?
If you have any problems or issues over our SDK, feel free to [create a github issue](https://github.com/amplitude/experiments-python-server/issues/new) or submit a request on [Amplitude Help](https://help.amplitude.com/hc/en-us/requests/new).
