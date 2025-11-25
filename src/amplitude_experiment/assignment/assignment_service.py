from amplitude import Amplitude, BaseEvent
from ..assignment.assignment import Assignment
from ..assignment.assignment import DAY_MILLIS
from ..assignment.assignment_filter import AssignmentFilter
from ..util import hash_code

FLAG_TYPE_MUTUAL_EXCLUSION_GROUP = "mutual-exclusion-group"
FLAG_TYPE_HOLDOUT_GROUP = "holdout-group"


def to_event(assignment: Assignment, send_evaluated_props: bool) -> BaseEvent:
    """
    @deprecated Assignment tracking is deprecated. Use Exposure tracking.
    """
    event = BaseEvent(event_type='[Experiment] Assignment', user_id=assignment.user.user_id,
                      device_id=assignment.user.device_id, event_properties={}, user_properties={})

    # If send_evaluated_props is True, populate event with all relevant user attributes
    if send_evaluated_props:
        user_attributes = [
            "country", "city", "region", "dma", "language",
            "platform", "version", "os", "device_manufacturer",
            "device_brand", "device_model", "carrier", "library", "ip_address"
        ]
        for attr in user_attributes:
            setattr(event, attr, getattr(assignment.user, attr, None))
        event.user_properties = assignment.user.user_properties

    set_props = {}
    unset_props = {}

    for flag_key in sorted(assignment.results):
        variant = assignment.results[flag_key]
        if variant.key is None:
            continue
        # Get variant metadata
        version: int = variant.metadata.get('flagVersion') if variant.metadata is not None else None
        segment_name: str = variant.metadata.get('segmentName') if variant.metadata is not None else None
        flag_type: str = variant.metadata.get('flagType') if variant.metadata is not None else None
        default: bool = False
        if variant.metadata is not None and variant.metadata.get('default') is not None:
            default = variant.metadata.get('default')
        # Set event properties
        event.event_properties[flag_key + '.variant'] = variant.key
        if version is not None and segment_name is not None:
            event.event_properties[flag_key + '.details'] = f"v{version} rule:{segment_name}"
        # Build user properties
        if flag_type == FLAG_TYPE_MUTUAL_EXCLUSION_GROUP:
            continue
        elif default:
            unset_props[f'[Experiment] {flag_key}'] = '-'
        else:
            set_props[f'[Experiment] {flag_key}'] = variant.key

    # Set user properties and insert id
    event.user_properties['$set'] = set_props
    event.user_properties['$unset'] = unset_props
    event.insert_id = f'{event.user_id} {event.device_id} {hash_code(assignment.canonicalize())} {int(assignment.timestamp / DAY_MILLIS)}'

    return event


class AssignmentService:
    """
    @deprecated Assignment tracking is deprecated. Use ExposureService with Exposure tracking instead.
    """
    def __init__(self, amplitude: Amplitude, assignment_filter: AssignmentFilter, send_evaluated_props: bool):
        self.amplitude = amplitude
        self.assignmentFilter = assignment_filter
        self.send_evaluated_props = send_evaluated_props

    def track(self, assignment: Assignment):
        if self.assignmentFilter.should_track(assignment):
            self.amplitude.track(to_event(assignment, self.send_evaluated_props))
