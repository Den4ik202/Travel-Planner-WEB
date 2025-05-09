from requests import get
import os


def get_featureMember_list(json_response: dict) -> dict:
    return json_response.get('response', dict).get('GeoObjectCollection', dict).get('featureMember', dict)


def get_point_list(featureMember_list: dict) -> dict:
    return featureMember_list.get('GeoObject', dict).get('Point', dict)


def get_full_adress(featureMember_list: dict) -> str:
    return featureMember_list.get('GeoObject', dict).get('metaDataProperty', dict).get('GeocoderMetaData', dict).get('text', '')


def get_positin_place(adress: str) -> str:
    response = get(
        url='https://geocode-maps.yandex.ru/1.x/',
        params={
            'apikey': os.getenv("API_KEY_YANDEX_GEOCODER"),
            'geocode': adress,
            'format': 'json'
        }
    )

    if response.status_code == 200:
        json_response = response.json()

        featureMember_list = get_featureMember_list(json_response)
        if not featureMember_list:
            return ''

        point_list = get_point_list(featureMember_list[0])
        full_adress = get_full_adress(featureMember_list[0])

        if not point_list:
            return ''

        return point_list.get('pos', (-1, -1)), full_adress

    return {'error': 'Not Found'}


def get_travel_image(pl_list: list, pt_list: list, theme: str) -> None:
    pl = ''
    for _, coord in enumerate(pl_list):
        pl += f'{coord[1]},{coord[0]},'
    pl = pl[:-1]

    pt = ''
    for _, coord, in enumerate(pt_list):
        pt += f'{coord[0]},{coord[1]},comma~'
    pt = pt[:-6] + 'flag'

    response = get(
        url=f'https://static-maps.yandex.ru/v1?',
        params={
            # 'll': f'{position[0]},{position[1]}',
            'pl': pl,
            'pt': pt,
            'lang': 'ru_RU',
            'theme': theme,
            'apikey': os.getenv("API_KEY_YANDEX_STATIC_MAP")
        }
    )

    return response.content


def get_place_image(position: tuple[float, float], theme: str) -> None:
    response = get(
        url=f'https://static-maps.yandex.ru/v1?',
        params={
            'll': f'{position[0]},{position[1]}',
            'lang': 'ru_RU',
            'z': 11,
            'theme': theme,
            'apikey': os.getenv("API_KEY_YANDEX_STATIC_MAP")
        }
    )

    return response.content
