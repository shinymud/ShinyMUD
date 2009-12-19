

def to_bool(val):
    bool_states = {'true': True, 'false': False}
    exception_message = 'Expected true or false: got %s.\n' % str(val)
    if not val:
        raise Exception(exception_message)
    val = val.strip().lower()
    if val in bool_states:
        return bool_states.get(val)
    else:
        raise Exception(exception_message)
