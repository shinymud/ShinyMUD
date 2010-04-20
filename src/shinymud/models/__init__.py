def to_bool(val):
    """Take a string representation of true or false and convert it to a boolean
    value. Returns a boolean value or None, if no corresponding boolean value
    exists.
    """
    bool_states = {'true': True, 'false': False}
    if not val:
        return None
    if isinstance(val, bool):
        return val
    val = val.strip().lower()
    return bool_states.get(val)
