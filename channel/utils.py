# channel/utils.py - вычислительные функции для удобства вынесены в отдельный файл

import random

#SEGMENT_PROCESS_TIME = 2 # Время сборки сегмента
SEGMENT_SIZE = 120  # 120 байт
ERROR_PROBABILITY = 0.10  # 10% ошибка
LOSS_PROBABILITY = 0.015  # 1.5% потеря
#LOSS_PROBABILITY = 1  # 100% потеря для отладки

GENERATOR_POLY = "1011"  # Порождающий полином для (7,4)-кода


def xor(a, b):
    return ''.join(['0' if i == j else '1' for i, j in zip(a, b)])


def modulo2_division(dividend, divisor):
    pick = len(divisor)
    tmp = dividend[0:pick]

    for i in range(pick, len(dividend)):
        if tmp[0] == '1':
            tmp = xor(divisor, tmp)[1:] + dividend[i]
        else:
            tmp = tmp[1:] + dividend[i]

    if tmp[0] == '1':
        tmp = xor(divisor, tmp)
    else:
        tmp = xor('0' * pick, tmp)

    return tmp


def encode_bitstring(bitstring):
    # Добавляем 3 нуля (n-k = 3)
    extended = bitstring + '000'
    remainder = modulo2_division(extended, GENERATOR_POLY)
    # Кодовое слово = исходные биты + остаток
    codeword = bitstring + remainder[-3:]  # Берем последние 3 бита остатка
    return codeword


def decode_bitstring(codeword):
    syndrome = modulo2_division(codeword, GENERATOR_POLY)[-3:]  # Берем последние 3 бита

    if syndrome == '000':
        return codeword[:4]  # Ошибок нет

    print(f"Декодирование слова {codeword}, синдром: {syndrome}")

    # Таблица синдромов для (7,4) кода
    error_positions = {
        '001': 6,  # Ошибка в 7-м бите
        '010': 5,  # Ошибка в 6-м бите
        '100': 4,  # Ошибка в 5-м бите
        '011': 3,  # Ошибка в 4-м бите
        '110': 2,  # Ошибка в 3-м бите
        '111': 1,  # Ошибка в 2-м бите
        '101': 0  # Ошибка в 1-м бите
    }

    if syndrome in error_positions:
        pos = error_positions[syndrome]
        # Инвертируем ошибочный бит
        corrected = codeword[:pos] + ('1' if codeword[pos] == '0' else '0') + codeword[pos + 1:]
        return corrected[:4]

    # Возвращаем codeword
    return codeword[:4]


def bits_to_text(bits):
    # Дополняем до полной кратности 8
    if len(bits) % 8 != 0:
        bits += '0' * (8 - len(bits) % 8)

    byte_strings = [bits[i:i + 8] for i in range(0, len(bits), 8)]
    byte_list = [int(b, 2) for b in byte_strings]

    try:
        return bytes(byte_list).decode('utf-8', errors='replace')
    except:
        return "[DECODING ERROR]"



def text_to_bits(text):
    return ''.join(f'{byte:08b}' for byte in text.encode('utf-8'))


def make_mistake(bits):
    # Разбиваем на 7-битные кодовые слова для внесения ошибок
    segments = [bits[i:i + 7] for i in range(0, len(bits), 7)]

    result = []
    for segment in segments:
        if len(segment) < 7:
            result.append(segment)
            continue

        if random.random() < ERROR_PROBABILITY:
            idx = random.randint(0, 6)  # Выбираем любой из 7 битов
            modified = segment[:idx] + ('1' if segment[idx] == '0' else '0') + segment[idx + 1:]
            result.append(modified)
        else:
            result.append(segment)

    return ''.join(result)