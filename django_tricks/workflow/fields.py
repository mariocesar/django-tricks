from collections import namedtuple, OrderedDict
from functools import wraps
from itertools import chain

from django.db.models import CharField
from django.utils.functional import curry


class DefaultDict(OrderedDict):
    def __init__(self, default_factory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_factory = default_factory

    def __getitem__(self, item):
        if item not in self:
            self.__setitem__(item, self.default_factory())
        return super().__getitem__(item)


class Workflow(CharField):
    State = namedtuple('State', ['state', 'label'])
    Starts = namedtuple('Starts', ['state'])
    Fork = namedtuple('Fork', ['from_state', 'to_state', 'label'])
    Condition = namedtuple('Condition', ['state', 'condition', 'operator'])
    Ends = namedtuple('Ends', ['state'])
    Transition = namedtuple('Transition', ['from_state', 'to_state', 'label'])

    AND = 'AND'
    OR = 'OR'

    def __init__(self, *nodes, **kwargs):
        self.nodes = nodes

        self._tree = DefaultDict(list)
        self._states = DefaultDict(lambda: {
            'starts': False,
            'ends': False,
            'transitions': [],
            'transition_to': [],
            'transition_from': []
        })

        for node in self.nodes:
            self._tree[type(node)].append(node)

        for node in self.nodes:
            if isinstance(node, Workflow.Starts):
                state = self.get_state(node.state)
                self._states[state]['starts'] = True

            elif isinstance(node, Workflow.Ends):
                state = self.get_state(node.state)
                self._states[state]['ends'] = True

            elif isinstance(node, Workflow.Transition):
                from_state = self.get_state(node.from_state)
                to_state = self.get_state(node.to_state)

                if node not in self._states[from_state]['transitions']:
                    self._states[from_state]['transitions'].append(node)

                if to_state not in self._states[from_state]['transition_to']:
                    self._states[from_state]['transition_to'].append(to_state)

                if from_state not in self._states[to_state]['transition_from']:
                    self._states[to_state]['transition_from'].append(from_state)

        kwargs['max_length'] = 255
        kwargs['db_index'] = True
        kwargs['choices'] = self.get_state_choices()
        super().__init__(**kwargs)

    def get_state(self, state_code):
        for state in self._tree[Workflow.State]:
            if state.state == state_code:
                return state
        raise Exception('Unknown state: %s' % state_code)

    def get_states(self):
        return self._tree[Workflow.State]

    def get_starts(self):
        return self._tree[Workflow.Starts]

    def get_forks(self):
        return self._tree[Workflow.Fork]

    def get_conditions(self):
        return chain(self._tree[Workflow.AndCondition], self._tree[Workflow.OrCondition])

    def get_ends(self):
        return self._tree[Workflow.Ends]

    def get_transitions(self):
        return self._tree[Workflow.Transition]

    def get_state_choices(self):
        """Return a choice like list of all available status."""
        choices = list(set(chain(*((step.from_state, step.to_state) for step in self.get_transitions()))))
        return [(choices, choices.title()) for choices in choices]

    @staticmethod
    def before_transition(func):
        """Executed before transition to STATE"""

        def decorator(state):
            @wraps(func)
            def wrapper(self):
                return func(self)

            return wrapper

        return decorator

    @staticmethod
    def after_transition(func):
        """Executed after transition to STATE"""

        def decorator(state):
            @wraps(func)
            def wrapper(self):
                return func(self)

            return wrapper

        return decorator

    def _get_next_states(self, field):
        """Return a choice like list of the available status for the current state."""
        state_position = getattr(self, field.attname)

        return [(transition.to_state, transition.label.title())
                for transition in field.transitions
                if transition.to_state == state_position]

    def contribute_to_class(self, cls, name, virtual_only=False):
        super().contribute_to_class(cls, name, virtual_only)
        setattr(cls, 'get_next_states', curry(self._get_next_states, field=self))

    def validate(self, value, model_instance):
        # TODO: Validate state transitions
        return super().validate(value, model_instance)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        args = []
        return name, path, args, kwargs
