import marshal
import types
import os

def extract_strings(code_obj):
    strings = []
    for const in code_obj.co_consts:
        if isinstance(const, str):
            strings.append(const)
        elif isinstance(const, types.CodeType):
            strings.extend(extract_strings(const))
    return strings

paths = [
    'src/store_intel/api/__pycache__/funnel.cpython-312.pyc',
    'src/store_intel/analytics/__pycache__/funnel.cpython-312.pyc',
]

for p in paths:
    if os.path.exists(p):
        try:
            with open(p, 'rb') as f:
                f.read(16)
                code = marshal.load(f)
                print(f"{p} strings:")
                print(extract_strings(code))
        except Exception as e:
            print(e)
