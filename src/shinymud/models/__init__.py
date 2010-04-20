def to_bool(val):
    bool_states = {'true': True, 'false': False}
    if not val:
        return None
    val = val.strip().lower()
    return bool_states.get(val)
