from amplitude import Amplitude, BaseEvent
from typing import List
from .exposure import Exposure
from .exposure_filter import ExposureFilter
from ..util import hash_code

FLAG_TYPE_MUTUAL_EXCLUSION_GROUP = "mutual-exclusion-group"


def to_exposure_events(exposure: Exposure, ttl_millis: int) -> List[BaseEvent]:
    """
    Convert an Exposure to a list of Amplitude events (one per flag).
    """
    events = []
    canonicalized = exposure.canonicalize()
    for flag_key in exposure.results:
        variant = exposure.results[flag_key]

        track_exposure = variant.metadata.get('trackExposure') if variant.metadata is not None else True
        if track_exposure is False:
            continue

        is_default = variant.metadata.get('default') if variant.metadata is not None else False
        if is_default:
            continue

        # Determine user properties to set and unset.
        set_props = {}
        unset_props = {}
        flag_type = variant.metadata.get('flagType') if variant.metadata is not None else None
        if flag_type != FLAG_TYPE_MUTUAL_EXCLUSION_GROUP:
            if variant.key:
                set_props[f'[Experiment] {flag_key}'] = variant.key
            elif variant.value:
                set_props[f'[Experiment] {flag_key}'] = variant.value

        # Build event properties.
        event_properties = {}
        event_properties['[Experiment] Flag Key'] = flag_key
        if variant.key:
            event_properties['[Experiment] Variant'] = variant.key
        elif variant.value:
            event_properties['[Experiment] Variant'] = variant.value
        if variant.metadata:
            event_properties['metadata'] = variant.metadata

        # Build event.
        event = BaseEvent(
            event_type='[Experiment] Exposure',
            user_id=exposure.user.user_id,
            device_id=exposure.user.device_id,
            event_properties=event_properties,
            user_properties={
                '$set': set_props,
                '$unset': unset_props,
            },
            insert_id=f'{exposure.user.user_id} {exposure.user.device_id} {hash_code(flag_key + " " + canonicalized)} {int(exposure.timestamp / ttl_millis)}'
        )
        if exposure.user.groups:
            event.groups = exposure.user.groups

        events.append(event)

    return events


class ExposureService:
    def __init__(self, amplitude: Amplitude, exposure_filter: ExposureFilter):
        self.amplitude = amplitude
        self.exposure_filter = exposure_filter

    def track(self, exposure: Exposure):
        if self.exposure_filter.should_track(exposure):
            events = to_exposure_events(exposure, self.exposure_filter.ttl_millis)
            for event in events:
                self.amplitude.track(event)

