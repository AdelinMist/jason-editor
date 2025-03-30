def highlight_is_valid(val):
    """
    Returns CSS based on value.
    """
    if isinstance(val, bool):
        color = 'darkgreen' if bool(val) else 'darkred'
    else:
        color = 'darkgreen' if val.lower() == 'true' else 'darkred'
    return 'background-color: {}'.format(color)