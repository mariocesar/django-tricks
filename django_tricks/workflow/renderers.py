from graphviz import Digraph


class GraphVizRenderer:
    def __init__(self, states):
        self.states = states

    def render(self, state=None):
        dot = Digraph()

        for node, props in self.states.items():
            attrs = {}

            if props['starts']:
                attrs['shape'] = 'diamond'
                attrs['style'] = 'filled'
                attrs['color'] = 'lightgray'
            elif props['ends']:
                attrs['shape'] = 'diamond'
                attrs['style'] = 'filled'
                attrs['color'] = 'lightgray'

            if node.state == state:
                attrs['style'] = 'filled'
                attrs['color'] = 'blue'
                attrs['fontcolor'] = 'white'

            dot.node(node.state, node.label, **attrs)

            for transition in props['transitions']:
                dot.edge(node.state, transition.to_state, label=transition.label)

        return dot
