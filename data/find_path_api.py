import requests
import polyline
import math

def get_route_coordinates(points):
    """
    Получает координаты маршрута между несколькими точками, используя OSRM API,
    и возвращает координаты маршрута и его длину.

    Args:
        points (list): Список кортежей (долгота, широта), представляющих точки маршрута.

    Returns:
        tuple: Кортеж (list, float), где:
            - list: Список кортежей (широта, долгота), представляющих координаты маршрута,
                    упрощенный до максимальной длины 100.
            - float: Длина маршрута в километрах.
              Возвращает (None, None), если маршрут не найден или произошла ошибка.
    """
    try:
        # Формируем строку координат для URL запроса
        coordinates_string = ';'.join([f'{lon},{lat}' for lon, lat in points])

        # Формируем URL для запроса к OSRM API
        url = f'http://router.project-osrm.org/route/v1/foot/{coordinates_string}?overview=full'

        # Отправляем GET-запрос
        response = requests.get(url)
        response.raise_for_status()  # Проверяем на наличие HTTP-ошибок (4xx или 5xx)

        # Преобразуем JSON-ответ в словарь
        data = response.json()

        # Извлекаем закодированную геометрию маршрута
        if 'routes' in data and len(data['routes']) > 0:
            route_geometry = data['routes'][0]['geometry']
            route_distance = data['routes'][0]['distance'] / 1000  # distance is in meters, convert to km


            # Декодируем геометрию Polyline
            route_coordinates = polyline.decode(route_geometry)

            # Упрощаем маршрут, если он длиннее 100
            if len(route_coordinates) > 100:
                route_coordinates = simplify_route(route_coordinates, 100)

            return route_coordinates, route_distance
        else:
            print("Маршрут не найден.")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        return None, None
    except ValueError as e:
        print(f"Ошибка при декодировании JSON: {e}")
        return None, None
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return None, None


def simplify_route(route, max_length):
    """
    Упрощает маршрут, уменьшая количество точек до max_length.
    Использует равномерное прореживание точек.  Более продвинутые методы
    упрощения (например, Ramer-Douglas-Peucker)  могут давать лучшие результаты,
    но требуют большего количества кода и зависимостей.

    Args:
        route (list): Список кортежей (широта, долгота), представляющих маршрут.
        max_length (int): Максимальная длина упрощенного маршрута.

    Returns:
        list: Упрощенный список координат.
    """
    if len(route) <= max_length:
        return route

    indices_to_keep = [int(i * (len(route) - 1) / (max_length - 1)) for i in range(max_length)]
    simplified_route = [route[i] for i in indices_to_keep]
    return simplified_route


def calculate_distance(point1, point2):
    """
    Вычисляет расстояние между двумя точками (широта, долгота) в километрах,
    используя формулу гаверсинуса.

    Args:
        point1 (tuple): Кортеж (широта, долгота) первой точки.
        point2 (tuple): Кортеж (широта, долгота) второй точки.

    Returns:
        float: Расстояние между двумя точками в километрах.
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    R = 6371  # Радиус Земли в километрах

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

