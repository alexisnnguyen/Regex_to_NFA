import json

# Authors: Alexis Nguyen and Katherine Vu
# Description: Converts a regular expression into an NFA. Takes in a regex through the command line
#              and converts it into an NFA by first converting it into an AST. The output will be in
#              a JSON file.
#

# This class takes the regex and recursively turns it into an AST
class Make_AST:
    # Initialization of the parser, sets current index to 0
    def __init__(self, regex):
        self.regex = regex
        self.current_index = 0

    # Enter the parsing
    def parse(self):
        return self.read_Exp()

    # For OR, Starts by builing a concatenation until a | is found so it may build an OR
    def read_Exp(self):
        left = self.parse_concatenation() # Calls concatenation
        while self.current_index < len(self.regex) and self.regex[self.current_index] == '|':
            self.current_index += 1  # Consume '|' by incrementing current index
            right = self.parse_concatenation() # Calls concatenation on the right of OR
            left = {'type': 'Or', 'operands': [left, right]}
        return left

    # For CONCAT, Starts by processing a * until it encounters a | or ()
    def parse_concatenation(self):
        left = self.parse_star() # Calls * on itself
        while self.current_index < len(self.regex) and self.regex[self.current_index] not in '|)':
            right = self.parse_star()
            left = {'type': 'Concatenation', 'operands': [left, right]}
        return left

    # For *, Starts by processing a leaf until it finds a * 
    def parse_star(self):
        leaf = self.parse_leaf()
        while self.current_index < len(self.regex) and self.regex[self.current_index] == '*':
            self.current_index += 1  # Consume '*'
            leaf = {'type': 'Star', 'operand': leaf}
        return leaf

    # For leaves and ()
    def parse_leaf(self):
        # Save the current character and then increment the current index
        if self.current_index < len(self.regex):
            current_char = self.regex[self.current_index]
            self.current_index += 1

            if current_char.isalnum(): # If it is a character then it is a leaf
                return {'type': 'Leaf', 'value': current_char}
            elif current_char == '(': # If it is an open parenthesis then parse as a new expression
                expr = self.read_Exp()
                if self.current_index < len(self.regex) and self.regex[self.current_index] == ')':
                    self.current_index += 1  # Consume ')'
                    return expr
                else: # Error in syntax, extra closed parenthesis
                    raise ValueError('Invalid regular expression: unmatched parentheses')
            elif current_char == '.': # Wildcard/Epsilon
                return {'type': 'AnyChar'}
            else: # Error in syntax
                raise ValueError(f'Invalid regular expression at \'{current_char}\'')
        else: # Error in syntax
            raise ValueError('Invalid regular expression')

# Prints the AST to check if it is parsing correctly, will delete later
def print_ast(node, indent=0):
    if node is not None:
        print('  ' * indent, f'{node["type"]}: {node.get("value", "")}')
        if 'operands' in node:
            for operand in node['operands']:
                print_ast(operand, indent + 1)
        elif 'operand' in node:
            print_ast(node['operand'], indent + 1)
            
# This class is the logic to turn the AST into an NFA
class NFA:
    state_array = [f'q{i}' for i in range(101)] # Array of 100 unused states initialized

    def __init__(self, states, alphabet, transitions, start_state, accept_states, current_state):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = accept_states
        self.current_state = current_state
        
    def leaf_nfa(self, symbol):
        # Create an NFA for a single symbol
        states = [self.state_array[self.current_state], self.state_array[self.current_state + 1]]
        alphabet = {symbol}
        transitions = {self.state_array[self.current_state]: {symbol: [self.state_array[self.current_state + 1]]}}
        start_state = self.state_array[self.current_state]
        accept_states = {self.state_array[self.current_state + 1]}

        return NFA(states, alphabet, transitions, start_state, accept_states, self.current_state + 2)

    def concatenate_nfa(self, nfa1, nfa2):
        states = nfa1.states + nfa2.states
        alphabet = nfa1.alphabet.union(nfa2.alphabet)
        transitions = nfa1.transitions.copy()
        
        for state, transitions in nfa2.transitions.items():
            if state in transitions:
                transitions[state] += nfa2.transitions[state]
            else:
                transitions[state] = nfa2.transitions[state]
    
        start_state = nfa1.start_state
        accept_states = nfa2.accept_states

        for state in nfa1.accept_states:
            transitions[state] = {'': [nfa2.start_state]}

        return NFA(states, alphabet, transitions, start_state, accept_states, self.current_state)

    def or_nfa(self, nfa1, nfa2):
        # Create an NFA for the choice (OR) operation
        states = nfa1.states + nfa2.states
        alphabet = nfa1.alphabet.union(nfa2.alphabet)
        transitions = {'q0': {'': [nfa1.start_state, nfa2.start_state]}}
        
        for state, state_transitions in nfa1.transitions.items():
            transitions[state] = state_transitions
        
        for state, state_transitions in nfa2.transitions.items():
            if state in transitions:
                transitions[state].update(state_transitions)
            else:
                transitions[state] = state_transitions
        
        for state in nfa1.accept_states:
            transitions[state] = {'': ['q_accept']}
        
        for state in nfa2.accept_states:
            transitions[state] = {'': ['q_accept']}
        
        accept_states = {'q_accept'}

        return NFA(states, alphabet, transitions, 'q0', accept_states, self.current_state)

    def star_nfa(self, nfa):
        # Create an NFA for the star (closure) operation
        states = nfa.states + ['q_accept']
        alphabet = nfa.alphabet
        transitions = {'q0': {'': [nfa.start_state, 'q_accept']}}
        
        for state, state_transitions in nfa.transitions.items():
            transitions[state] = state_transitions
        
        for state in nfa.accept_states:
            transitions[state] = {'': [nfa.start_state, 'q_accept']}
        
        accept_states = {'q_accept'}

        return NFA(states, alphabet, transitions, 'q0', accept_states, self.current_state)

    def ast_to_nfa(self, ast):
        if ast['type'] == 'Leaf':
            return self.leaf_nfa(ast['value'])
        elif ast['type'] == 'Concatenation':
            nfa1 = self.ast_to_nfa(ast['operands'][0])
            nfa2 = self.ast_to_nfa(ast['operands'][1])
            return self.concatenate_nfa(nfa1, nfa2)
        elif ast['type'] == 'Or':
            nfa1 = self.ast_to_nfa(ast['operands'][0])
            nfa2 = self.ast_to_nfa(ast['operands'][1])
            return self.or_nfa(nfa1, nfa2)
        elif ast['type'] == 'Star':
            nfa = self.ast_to_nfa(ast['operand'])
            return self.star_nfa(nfa)

# Main
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Convert regular expressions to AST in JSON format.')
    parser.add_argument('regex', type=str, help='The regular expression to convert.')

    args = parser.parse_args()

    regex_parser = Make_AST(args.regex)
    
    try:
        ast_root = regex_parser.parse()
        # Printing
        print('AST:')
        print_ast(ast_root)   
        
        # Convert AST to NFA
        nfa_instance = NFA(states=[], alphabet=set(), transitions={}, start_state='', accept_states=set(), current_state=0)
        nfa = nfa_instance.ast_to_nfa(ast_root)

        # Now, you can use/print the NFA properties as needed
        print(f'States: {nfa.states}')
        print(f'Alphabet: {nfa.alphabet}')
        print(f'Transitions: {nfa.transitions}')
        print(f'Start State: {nfa.start_state}')
        print(f'Accept States: {nfa.accept_states}')
        
    except ValueError as e:
        print(f'Error: {e}')