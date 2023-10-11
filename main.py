import re


def tokenizer(input_source_code):
    current = 0
    tokens = []

    while current < len(input_source_code):
        char = input_source_code[current]

        if char == '(':
            tokens.append({
                'type': 'paren',
                'value': '('
            })
            current += 1
            continue

        if char == ')':
            tokens.append({
                'type': 'paren',
                'value': ')'
            })
            current += 1
            continue

        _WHITESPACE = '\s'
        if re.match(_WHITESPACE, char):
            current += 1
            continue

        _NUMBERS = '[0-9]'
        if re.match(_NUMBERS, char):
            value = ''

            while re.match(_NUMBERS, char):
                value += char
                current += 1
                char = input_source_code[current]

            tokens.append({
                'type': 'number',
                'value': value
            })
            continue

        if char == '"':
            value = ''
            current += 1
            char = input_source_code[current]

            while char != '"':
                value += char
                current += 1
                char = input_source_code[current]

            current += 1

            tokens.append({
                'type': 'string',
                'value': value
            })
            continue

        _LETTERS = '[a-z]'
        if re.match(_LETTERS, char, re.IGNORECASE):
            value = ''

            while re.match(_LETTERS, char, re.IGNORECASE):
                value += char
                current += 1
                char = input_source_code[current]

            tokens.append({
                'type': 'name',
                'value': value
            })
            continue

        raise TypeError('I dont know what this character is: ' + char)

    return tokens


def parser(tokens):
    current = 0

    def walk():
        nonlocal current
        token = tokens[current]

        if token['type'] == 'number':
            current += 1
            return {
                'type': 'NumberLiteral',
                'value': token['value']
            }

        if token['type'] == 'string':
            current += 1
            return {
                'type': 'StringLiteral',
                'value': token['value']
            }

        if token['type'] == 'paren' and token['value'] == '(':
            current += 1
            token = tokens[current]

            node = {
                'type': 'CallExpression',
                'name': token['value'],
                'params': []
            }

            current += 1

            while (token['type'] != 'paren') or (token['type'] == 'paren' and token['value'] != ')'):
                node['params'].append(walk())
                token = tokens[current]

            current += 1

            return node

        raise TypeError(token['type'])

    ast = {
        'type': 'Program',
        'body': []
    }

    while current < len(tokens):
        ast['body'].append(walk())

    return ast


def traverser(ast, visitor):
    def traverse_array(array, parent):
        for child in array:
            traverse_node(child, parent)

    def traverse_node(node, parent):
        methods = visitor.get(node['type'])

        if methods and methods.get('enter'):
            methods['enter'](node, parent)

        if node['type'] == 'Program':
            traverse_array(node['body'], node)
        elif node['type'] == 'CallExpression':
            traverse_array(node['params'], node)

        if methods and methods.get('exit'):
            methods['exit'](node, parent)

    traverse_node(ast, None)


def transformer(ast):
    new_ast = {
        'type': 'Program',
        'body': []
    }

    ast['_context'] = new_ast['body']

    def visit_number_literal(node, parent):
        parent['_context'].append({
            'type': 'NumberLiteral',
            'value': node['value']
        })

    def visit_string_literal(node, parent):
        parent['_context'].append({
            'type': 'StringLiteral',
            'value': node['value']
        })

    def visit_call_expression(node, parent):
        expression = {
            'type': 'CallExpression',
            'callee': {
                'type': 'Identifier',
                'name': node['name']
            },
            'arguments': []
        }

        node['_context'] = expression['arguments']

        if parent['type'] != 'CallExpression':
            expression = {
                'type': 'ExpressionStatement',
                'expression': expression
            }

        parent['_context'].append(expression)

    visitor = {
        'NumberLiteral': {
            'enter': visit_number_literal
        },
        'StringLiteral': {
            'enter': visit_string_literal
        },
        'CallExpression': {
            'enter': visit_call_expression
        }
    }

    traverser(ast, visitor)

    return new_ast


def code_generator(node):
    if node['type'] == 'Program':
        return '\n'.join([code_generator(child) for child in node['body']])

    if node['type'] == 'ExpressionStatement':
        return code_generator(node['expression']) + ';'

    if node['type'] == 'CallExpression':
        callee = code_generator(node['callee'])
        arguments = ', '.join([code_generator(arg) for arg in node['arguments']])
        return f'{callee}({arguments})'

    if node['type'] == 'Identifier':
        return node['name']

    if node['type'] == 'NumberLiteral':
        return node['value']

    if node['type'] == 'StringLiteral':
        return f'"{node["value"]}"'

    raise TypeError(node['type'])


def compiler(input_source_code):
    tokens = tokenizer(input_source_code)
    ast = parser(tokens)
    new_ast = transformer(ast)
    output_source_code = code_generator(new_ast)
    return output_source_code


# Example usage
input_code = '(add 2 (subtract 4 2))'
compiled_code = compiler(input_code)
print(compiled_code)
