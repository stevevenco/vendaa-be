

FLAG_VALUE_MAP = {
    'Enable': 1,
    'Disable': 0,
    'Set': 1,
    'Reset': 0,
    'Enable Reconnection of Service': 0,
    'Disconnect Service': 1,
    'Post Payment': 0,
    'Pre-Payment': 1,
    'Set': 0,
    'Unset': 1
}

FLAG_INDEX_MAP = {
    'Set Flag CTS Test': 0,
    'Detect Tamper': 1,
    'Disconnect Service': 2,
    'Disconnect On Tamper': 3,
    'Disconnect On Power Limit': 4,
    'Disconnect On Under Frequency': 5,
    'Set Electricity Payment Mode': 6,
    'Set Water Payment Mode': 7,
    'Set Gas Payment Mode': 8,
    'Set Time Payment Mode': 9,
    'Set Commisionning Mode': 10,
    'Enable TI Fallback Power Limit': 11
}

INDEX_VALUE_MAP = {
    'Set Flag CTS Test': ['Set', 'Reset'],
    'Detect Tamper': ['Enable', 'Disable'],
    'Disconnect Service': ['Enable Reconnection of Service', 'Disconnect Service'],
    'Disconnect On Tamper': ['Enable', 'Disable'],
    'Disconnect On Power Limit': ['Enable', 'Disable'],
    'Disconnect On Under Frequency': ['Enable', 'Disable'],
    'Set Electricity Payment Mode': ['Post Payment', 'Pre-Payment'],
    'Set Commissioning Mode': ['Set', 'Unset'],
    'Enable TI Fallback Power Limit': ['Enable', 'Disable']
}


request_body = {
    "meter_number": "",
    "token_type": "mgtk",
    "operation": "Disconnect On Power Limit",
    "action": "Enable"
}




# def get_token_flag(req_doc):
#     token_flag = 0
#     if req_doc.mse_subclass == 'Set Flag (10)':
#         index = 63
#         flag_index = FLAG_INDEX_MAP.get(req_doc.flag_token_type)
#         flag_value = FLAG_VALUE_MAP.get(req_doc.flag_token_value)

#         index_bit = convert_decimal_to_binary(index, 6)
#         flag_index_bit = convert_decimal_to_binary(flag_index, 9)
#         flag_value_bit = convert_decimal_to_binary(flag_value, 1)

#         flag_bit = f'{index_bit}{flag_index_bit}{flag_value_bit}'
#         token_flag = int(flag_bit, 2)
#     return token_flag


# if req_doc.mse_subclass == 'Set Flag (10)':
def get_token_flag(flag_token_type, flag_token_value):
    token_flag = 0
    index = 63
    flag_index = FLAG_INDEX_MAP.get(flag_token_type)
    flag_value = FLAG_VALUE_MAP.get(flag_token_value)

    index_bit = convert_decimal_to_binary(index, 6)
    flag_index_bit = convert_decimal_to_binary(flag_index, 9)
    flag_value_bit = convert_decimal_to_binary(flag_value, 1)

    flag_bit = f'{index_bit}{flag_index_bit}{flag_value_bit}'
    token_flag = int(flag_bit, 2)
    return token_flag


def convert_decimal_to_binary(decimal, bit_size=None):
    binary = bin(decimal).replace("0b", "")
    if bit_size and len(binary) < bit_size:
        padding_size = bit_size - len(binary)
        binary = '0'*padding_size + binary
    return binary