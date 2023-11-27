# Created to test the functionality of the AST

# This class is the parsing logic for the AST i.e. takes the regex and recursively turns it into an AST
class MakeAST:
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

# Main
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert regular expressions to AST in JSON format.')
    parser.add_argument('regex', type=str, help='The regular expression to convert.')

    args = parser.parse_args()
    
    regex_parser = MakeAST(args.regex)
    
    try:
        ast_root = regex_parser.parse()
        # Printing
        print('AST:')
        print_ast(ast_root)   
        
    except ValueError as e:
        print(f'Error: {e}')