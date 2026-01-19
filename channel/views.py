import random
import time

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json
from channel.utils import (text_to_bits, bits_to_text,
                    encode_bitstring, decode_bitstring,
                    make_mistake, LOSS_PROBABILITY)
import requests

def forward_to_transfer_server(endpoint, data):
    # В тестовом режиме работаем без транспортного уровня:
    # не делаем реальных HTTP-запросов, только логируем "отправку".
    if getattr(settings, "TEST_MODE", False):
        if endpoint == "transferAck":
            target = getattr(settings, "TRANSFER_ACK_URL", "/transferAck")
            print(f"[TEST_MODE] Передача квитанции: отправлено (без подключения) -> {target}")
        else:
            target = getattr(settings, "TRANSFER_SEGMENT_URL", "/transferSegment")
            print(f"[TEST_MODE] Передача сегмента: отправлено (без подключения) -> {target}")
        print(f"[TEST_MODE] Payload: {data}")
        return True

    try:
        if endpoint == "transferAck":
            print(f"Передача квитанции. POST запрос на {endpoint} транспортного уровня")
            requests.post(
                f"{settings.TRANSFER_ACK_URL}",
                json=data,
                timeout=5
            )
        else:
            print(f"Передача сегмента. POST запрос на {endpoint} транспортного уровня")
            requests.post(
                f"{settings.TRANSFER_SEGMENT_URL}",
                json=data,
                timeout=5
            )
        return True
    except requests.RequestException as ex:
        print(f"Ошибка при отправке {data} на /{endpoint}: {ex}")
        return False

@swagger_auto_schema(
    method='post',
    operation_id="processSegment",
    operation_description="Обработка сегмента от транспортного уровня",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['sender', 'messageId', 'segmentIndex', 'totalSegments', 'payload'],
        properties={
            'sender': openapi.Schema(type=openapi.TYPE_STRING, description='Отправитель', example='земля-станция01'),
            'messageId': openapi.Schema(type=openapi.TYPE_STRING, description='ID сообщения', example='сообщение-001'),
            'segmentIndex': openapi.Schema(type=openapi.TYPE_INTEGER, description='Индекс сегмента', example=0),
            'totalSegments': openapi.Schema(type=openapi.TYPE_INTEGER, description='Всего сегментов', example=5),
            'payload': openapi.Schema(type=openapi.TYPE_STRING, description='Полезная нагрузка', example='Привет сегмент 0'),
        },
    ),
    responses={
        200: openapi.Response(description="Сегмент обработан", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sender': openapi.Schema(type=openapi.TYPE_STRING),
                'messageId': openapi.Schema(type=openapi.TYPE_STRING),
                'segmentIndex': openapi.Schema(type=openapi.TYPE_INTEGER),
                'totalSegments': openapi.Schema(type=openapi.TYPE_INTEGER),
                'payload': openapi.Schema(type=openapi.TYPE_STRING),
                'segment_lost': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'original_bit_length': openapi.Schema(type=openapi.TYPE_INTEGER),
                'restored_bit_length': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )),
        204: openapi.Response(description="Сегмент потерян"),
        400: openapi.Response(description="Ошибка при вводе данных"),
        500: openapi.Response(description="Ошибка сервера"),
        502: openapi.Response(description="Ошибка при отправке данных на сервер"),
    }
)
@api_view(['POST'])
def process_segment(request):
    try:
        # Проверка JSON на входе
        required_fields = ['sender', 'messageId', 'segmentIndex', 'totalSegments', 'payload']
        missing_fields = [field for field in required_fields if
                          field not in request.data or request.data[field] in [None, '']]
        if missing_fields:
            return Response({"error": f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        original_data = {
            "sender": request.data.get('sender', ''),
            "messageId": request.data.get('messageId', ''),
            "segmentIndex": request.data.get('segmentIndex', 0),
            "totalSegments": request.data.get('totalSegments', 0),
            "payload": request.data.get('payload', '')
        }
        print(f"-------- Передача сегмента {original_data['segmentIndex']} из {original_data['totalSegments']} --------")

        # Возможная потеря сегмента с LOSS_PROBABILITY
        if random.random() < LOSS_PROBABILITY:
            print(f"****** Сегмент {original_data['segmentIndex']} потерян! ******")
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Преобразование всех полей в JSON-строку
        combined_data = json.dumps(original_data, ensure_ascii=False)

        print(combined_data)

        # Перевод JSON-строки в битовую строку
        # text_to_bits описан в utils.py
        bits = text_to_bits(combined_data)

        print(f"Битовая строка: {bits}")

        # Кодирование 4-битных групп циклическим кодом (7,4)
        # encode_bitstring описан в utils.py
        encoded = ''
        for i in range(0, len(bits), 4):
            chunk = bits[i:i + 4]
            encoded += encode_bitstring(chunk)

        # Внесение ошибки
        # make_mistake описан в utils.py
        corrupted = make_mistake(encoded)

        # Декодирование по 7-битным группам
        # decode_bitstring описан в utils.py
        decoded_bits = ''
        for i in range(0, len(corrupted), 7):
            codeword = corrupted[i:i + 7]
            if len(codeword) == 7:
                decoded_bits += decode_bitstring(codeword)

        # Перевод битов в JSON
        # bits_to_text описан в utils.py
        restored_json = bits_to_text(decoded_bits)
        restored_data = json.loads(restored_json)

        # Передаём восстановленные данные на другой сервер
        if not forward_to_transfer_server("transferSegment", restored_data):
            return Response({"message": f"Не удалось отправить данные на сервер транспортного уровня"},
                            status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            "sender": restored_data.get("sender", ""),
            "messageId": restored_data.get("messageId", ""),
            "segmentIndex": restored_data.get("segmentIndex", 0),
            "totalSegments": restored_data.get("totalSegments", 0),
            "payload": restored_data.get("payload", ""),
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='post',
    operation_id="processAck",
    operation_description="Обработка квитанции без изменений.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['lastConfirmedSegment', 'messageId'],
        properties={
            'messageId': openapi.Schema(type=openapi.TYPE_STRING, description='ID сообщения', example='сообщение-001'),
            'lastConfirmedSegment': openapi.Schema(type=openapi.TYPE_INTEGER, description='Последний полученный сегмент', example=0),
        },
    ),
    responses={
        200: openapi.Response(description="Квитанция передана", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'messageId': openapi.Schema(type=openapi.TYPE_STRING),
                'lastConfirmedSegment': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        )),
        204: openapi.Response(description="Квитанция потеряна"),
        400: openapi.Response(description="Ошибка при вводе данных"),
        500: openapi.Response(description="Ошибка сервера"),
        502: openapi.Response(description="Ошибка при передаче квитанции на сервер"),
    }
)
@api_view(['POST'])
def process_ack(request):
    try:
        # Проверка JSON на входе
        required_fields = ['messageId', 'lastConfirmedSegment']
        missing_fields = [field for field in required_fields if
                          field not in request.data or request.data[field] in [None, '']]
        if missing_fields:
            return Response({"error": f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        ack = {
            "messageId": request.data.get('messageId', ''),
            "lastConfirmedSegment": request.data.get('lastConfirmedSegment', 0),
        }

        print("Передача квитанции.")

        # Возможная потеря квитанции с LOSS_PROBABILITY
        if random.random() < LOSS_PROBABILITY:
            print("****** Квитанция потеряна! ******")
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Передаём ACK на другой сервер
        if not forward_to_transfer_server("transferAck", ack):
            return Response({"message": f"Не удалось отправить данные на сервер транспортного уровня"},
                            status=status.HTTP_502_BAD_GATEWAY)

        return Response(ack, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)