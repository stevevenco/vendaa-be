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