def extract_asserts(code_str):
    lines = code_str.split('\n')
    asserts = []
    current_assert = ''
    for line in lines:
        if line.startswith('assert'):
            current_assert += line.strip() + '\n'
        elif current_assert:
            asserts.append(current_assert.strip())
            current_assert = ''
    if current_assert:
        asserts.append(current_assert.strip())
    return asserts

if __name__ == "__main__":
    tests1 = ""
    t1 = extract_asserts(tests1)

    tests2 = "assert x == 2"
    t2 = extract_asserts(tests2)

    tests3 = "assert x == 2\nassert y == 3"
    t3 = extract_asserts(tests3)

    tests3 = "assert x == 2\n    and z == 345\nassert y == 3"
    t3 = extract_asserts(tests3)
