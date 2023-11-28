import json
import argparse

# Authors: Alexis Nguyen and Katherine Vu
# Description: Converts a regular expression into an NFA. Takes in a regex through the command line
#              and converts it into an NFA by first converting it into an AST. The output will be in
#              a JSON file.
#

# This class takes the regex and checks for proper format
class read_Exp:
    def __init__(self, regex):
        self.regex = regex
        self.current_index = 0
        self.error = 0
    
    def read(self):
        first = 0 # Counter for first parenthesis
        second = 0 # Counter for second parenthesis
        star = 0 # Counter for multiple *'s in a row
        orr = 0 # Counter for multiple |'s in a row
        while self.current_index < len(self.regex):
            if self.regex[self.current_index] == '(':
                first += 1
                self.current_index += 1
            elif self.regex[self.current_index] == ')':
                second += 1
                self.current_index += 1
            elif self.regex[self.current_index] == '*':
                star += 1
                if self.current_index + 1 < len(self.regex):
                    if self.regex[self.current_index + 1] == '*' and star == 1:
                        self.error += 1
                        return self.error # Return if there is an error
                self.current_index += 1
            elif self.regex[self.current_index] == '|':
                orr += 1
                if self.current_index + 1 < len(self.regex):
                    if self.regex[self.current_index + 1] == '|' and orr == 1:
                        self.error += 1
                        return self.error # Return if there is an error
                self.current_index += 1
            else:
                self.current_index += 1
        if first != second:
            self.error += 1
        return self.error # Return 0 if there is no error
        
# This class takes the regex and recursively turns it into an AST
class Make_AST:
    # Initialization of the parser, sets current index to 0
    def __init__(self, regex):
        self.regex = regex
        self.current_index = 0

    # Enter the parsing
    def parse(self):
        return self.or_ast()

    # For OR, Starts by builing a concatenation until a | is found so it may build an OR
    def or_ast(self):
        left = self.concatenation_ast() # Calls concatenation
        while self.current_index < len(self.regex) and self.regex[self.current_index] == '|':
            self.current_index += 1  # Consume '|' by incrementing current index
            right = self.concatenation_ast() # Calls concatenation on the right of OR
            left = {'type': 'Or', 'operands': [left, right]}
        return left

    # For CONCAT, Starts by processing a * until it encounters a | or ()
    def concatenation_ast(self):
        left = self.star_ast() # Calls * on itself
        while self.current_index < len(self.regex) and self.regex[self.current_index] not in '|)':
            right = self.star_ast()
            left = {'type': 'Concatenation', 'operands': [left, right]}
        return left

    # For *, Starts by processing a leaf until it finds a * 
    def star_ast(self):
        leaf = self.leaf_ast() # Calls leaf on itself
        while self.current_index < len(self.regex) and self.regex[self.current_index] == '*':
            self.current_index += 1  # Consume '*'
            leaf = {'type': 'Star', 'operand': leaf}
        return leaf

    # For leaves and ()
    def leaf_ast(self):
        # Save the current character and then increment the current index
        if self.current_index < len(self.regex):
            current_char = self.regex[self.current_index]
            self.current_index += 1

            if current_char.isalnum(): # If it is a character then it is a leaf
                return {'type': 'Leaf', 'value': current_char}
            elif current_char == '(': # If it is an open parenthesis then parse as a new expression
                expr = self.or_ast()
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
class Make_NFA:
    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = accept_states
        self.curr_state = 0 # Counter for new states
        
    # Generates a new state
    def state_generator(self):
        new_state = f'q{self.curr_state}'
        self.curr_state += 1 # Incrementing state counter
        return new_state
        
    def leaf_nfa(self,symbol):
        # Create an NFA for a single symbol
        start_state = self.state_generator() # Create new start state
        accept_state = self.state_generator() # Create new accept state
        states = [start_state, accept_state] # The states are only the start state and accept state
        alphabet = {symbol}
        transitions = {start_state: {symbol: [accept_state]}} # Read symbol, go from current state
                                                              # to the next state
        
        accept_states = {accept_state}

        return Make_NFA(states, alphabet, transitions, start_state, accept_states)

    # Create an NFA for the concatenation operation
    def concatenate_nfa(self, nfa1, nfa2):
        start_state = nfa1.start_state # Create new start state
        states = nfa1.states + nfa2.states # The states are NFA1 union NFA2
        alphabet = nfa1.alphabet.union(nfa2.alphabet) # The alphabet is NFA1 union NFA2
        transitions = nfa1.transitions.copy() # The transitions are just a copy of NFA1

        # Merges the transitions of NFA1 and NFA2 and creates new transitions if its not there
        for state, state_transitions in nfa2.transitions.items():
            if state in transitions:
                for symbol, destinations in state_transitions.items():
                    if symbol in transitions[state]:
                        transitions[state][symbol] += destinations
                    else:
                        transitions[state][symbol] = destinations
            else:
                transitions[state] = state_transitions

        # Updates the transitions so that the accept states of NFA1 goes to start state of NFA2
        for state in nfa1.accept_states:
            if state in transitions and 'ε' in transitions[state]:
                transitions[state]['ε'].append(nfa2.start_state)
            else:
                transitions[state] = {'ε': [nfa2.start_state]}
                
        accept_states = nfa2.accept_states # The accept states of NFA2 are the accept states

        return Make_NFA(states, alphabet, transitions, start_state, accept_states)

    # Create an NFA for the choice (OR) operation
    def or_nfa(self, nfa1, nfa2):
        start_state = self.state_generator() # Create new start state
        accept_state = self.state_generator() # Create new accept state
        states = [start_state] + nfa1.states + nfa2.states + [accept_state] # States are NFA1 states,
        # NFA2 states, new start state, and new end state
        alphabet = nfa1.alphabet.union(nfa2.alphabet) # The alphabet is NFA1 union NFA2
        transitions = {start_state: {'ε': [nfa1.start_state, nfa2.start_state]}} # The transitions
        # must include the new start state to the starts states of NFA1 and NFA2
        
        # Copy transitions from nfa1 to the combined transitions
        for state, state_transitions in nfa1.transitions.items():
            transitions[state] = state_transitions
        
        # Combine transitions from nfa2 into the combined transitions
        for state, state_transitions in nfa2.transitions.items():
            if state in transitions:
                transitions[state].update(state_transitions)
            else:
                transitions[state] = state_transitions
        
        for state in nfa1.accept_states: # Add transition from NFA1's accept states to new one
            transitions[state] = {'ε': [accept_state]}
            
        for state in nfa2.accept_states: # Add transition from NFA2's accept states to new one
            transitions[state] = {'ε': [accept_state]}
        
        accept_states = {accept_state}

        return Make_NFA(states, alphabet, transitions, start_state, accept_states)

    # Create an NFA for the star (closure) operation
    def star_nfa(self,nfa):
        start_state = self.state_generator() # Create new start state
        accept_state = self.state_generator() # Create new accept state
        states = [start_state] + nfa.states + [accept_state] # The NFA's states plus new ones
        alphabet = nfa.alphabet
        transitions = {start_state: {'ε': [nfa.start_state, accept_state]}} # The new start state
        # must go to the old start state and the accept state
        
        # Copy transitions from the original NFA to the combined transitions
        for state, state_transitions in nfa.transitions.items():
            transitions[state] = state_transitions
        
        # Add transitions from the old NFA's accept states to the new one
        for state in nfa.accept_states:
            transitions[state] = {'ε': [nfa.start_state, accept_state]}
        
        accept_states = {accept_state}

        return Make_NFA(states, alphabet, transitions, start_state, accept_states)

    # Makes the NFA using the functions defined above
    def ast_to_nfa(self,ast):
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
    parser = argparse.ArgumentParser(description='Convert regular expressions to AST in JSON format.')
    parser.add_argument('regex', type=str, help='The regular expression to convert.')
    # Load in argument
    args = parser.parse_args()
    
    # Read expression for correct format
    reader = read_Exp(args.regex) 
    p_error = reader.read()

    # Print out error if incorrect format
    if p_error != 0:
        print(f"Invalid regular expression: Expression in incorrect format")
    else:
        # Make AST for regex
        regex_parser = Make_AST(args.regex)
    
        try:
            ast_root = regex_parser.parse() 
            
            # Creates an instance of NFA
            nfa_object = Make_NFA([], set(), {}, None, set())
            
            # Convert AST to NFA
            nfa = nfa_object.ast_to_nfa(ast_root)

            nfa_json = {
                'States': nfa.states,
                'Alphabet': list(nfa.alphabet),
                'Transitions': nfa.transitions,
                'Start State': nfa.start_state,
                'Accept States': list(nfa.accept_states)
            }

            # Save the final NFA information to a JSON file
            with open("final_NFA.json", "w") as json_file:
                json.dump(nfa_json, json_file, indent=1)
            print(f"Check final_NFA.json to check final NFA!")
            
        except ValueError as e:
            print(f'Error: {e}') # Prints the error