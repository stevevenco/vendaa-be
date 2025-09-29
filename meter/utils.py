def validate_meter_no(meter_no):
    _meter_no = meter_no[:-1][::-1]
    _idx = 0
    sum_list = []
    for digit in _meter_no:
        if _idx % 2 == 0:
            double = str(int(digit)*2)
            if len(double) == 2:
                sum_list.append(int(double[0]))
                sum_list.append(int(double[1]))
            else: sum_list.append(int(double))
        else:
            sum_list.append(int(digit))
        _idx += 1
    digit_sum = sum(sum_list)
    luhn = (10 - (digit_sum % 10))
    check_digit = int(meter_no[-1])
    if luhn == 10:
        luhn = 0

    if luhn != check_digit:
        return False
    return True


def format_token(token: str) -> str:
    """
    Formats a token string by adding a dash every 4 characters.
    e.g: 1234567812340987 -> 1234-5678-1234-0987
    """
    if not isinstance(token, str):
        return token
    return '-'.join([token[i:i+4] for i in range(0, len(token), 4)])


def get_token_class_and_subclass(token_type: str):
    """
    Returns the token class and subclass based on the token type.
    """
    token_map = {
        'mgtk': ('MGTK', 'MGTK (1)'),
        'kct': ('KCT', 'KCT (2)'),
        'fr': ('FR', 'FR (3)'),
        'cwe': ('CWE', 'CWE (4)'),
        'frt': ('FRT', 'FRT (5)'),
        'cwt': ('CWT', 'CWT (6)'),
        'frc': ('FRC', 'FRC (7)'),
        'cwc': ('CWC', 'CWC (8)'),
        'kvt': ('KVT', 'KVT (9)'),
        'kvc': ('KVC', 'KVC (10)'),
        'kvtc': ('KVTC', 'KVTC (11)'),
        'kvtcr': ('KVTCR', 'KVTCR (12)'),
    }
    return token_map.get(token_type, (None, None))