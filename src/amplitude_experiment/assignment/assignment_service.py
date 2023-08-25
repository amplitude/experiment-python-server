from amplitude import Amplitude, BaseEvent
from ..assignment.assignment import Assignment
from ..assignment.assignment import DAY_MILLIS
from ..assignment.assignment_filter import AssignmentFilter
from ..util import hash_code

FLAG_TYPE_MUTUAL_EXCLUSION_GROUP = "mutual-exclusion-group"
FLAG_TYPE_HOLDOUT_GROUP = "holdout-group"


def to_event(assignment: Assignment) -> BaseEvent:
    event = BaseEvent(event_type='[Experiment] Assignment', user_id=assignment.user.user_id,
                      device_id=assignment.user.device_id, event_properties={}, user_properties={})
    for key in sorted(assignment.results):
        event.event_properties[key + '.variant'] = assignment.results[key].variant['key']

    set_props = {}
    unset_props = {}

    for key in sorted(assignment.results):
        if assignment.results[key].type == FLAG_TYPE_MUTUAL_EXCLUSION_GROUP:
            continue
        elif assignment.results[key].is_default_variant:
            unset_props[f'[Experiment] {key}'] = '-'
        else:
            set_props[f'[Experiment] {key}'] = assignment.results[key].variant['key']

    event.user_properties['$set'] = set_props
    event.user_properties['$unset'] = unset_props

    event.insert_id = f'{event.user_id} {event.device_id} {hash_code(assignment.canonicalize())} {int(assignment.timestamp / DAY_MILLIS)}'

    return event


class AssignmentService:
    def __init__(self, amplitude: Amplitude, assignment_filter: AssignmentFilter):
        self.amplitude = amplitude
        self.assignmentFilter = assignment_filter

    def track(self, assignment: Assignment):
        if self.assignmentFilter.should_track(assignment):
            self.amplitude.track(to_event(assignment))
