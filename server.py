from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, redirect, make_response, jsonify, request, send_file
from sqlalchemy import literal
from requests import get, post, put, delete
from flask_restful import Api
import base64
import io
import os
import tempfile
import time
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from dotenv import load_dotenv
from data.yandex_api import get_positin_place, get_travel_image, get_place_image
from data.find_path_api import get_route_coordinates
from data import users_resource, routs_resource, db_session
from data.users import User
from data.routs import Route
from forms.user import LoginForm
from forms.register import RegisterForm

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'TravelPlannerWEB'
api = Api(app)
login_manager = LoginManager()
login_manager.init_app(app)
all_places_position = []
session_flask = {}
theme = 'dark'


@app.route('/', methods=['GET', 'POST'])
def index():
    global all_places_position, session_flask, theme
    all_places_position = []
    session_flask = {}

    if request.method == 'POST':
        theme = 'light' if 'swith_light' in request.form else 'dark'

    return render_template('start.html', theme=theme)

# поиск места


@app.route('/findPlace', methods=['GET', 'POST'])
def findPlace():
    image_bytes = ''
    error = False
    if request.method == 'POST':
        place_adress = request.form['place_adress']
        try:
            position_palce, full_adress = get_positin_place(place_adress)
            position_palce = tuple(
                map(float, position_palce.split()))

            image_bytes = get_place_image(position_palce, theme=theme)
            image_bytes = base64.b64encode(image_bytes).decode('utf-8')

            all_places_position.append((position_palce, full_adress))
        except Exception as _:
            error = True

    return render_template('findPlace.html',
                           places=[i[1] for i in all_places_position],
                           image_bytes=image_bytes,
                           error=error,
                           theme=theme)
# удаление места


@app.route('/findPlace/place/delete/<int:rout_id>')
def deletePlace(rout_id: int):
    global all_places_position

    all_places_position.pop(rout_id - 1)

    return redirect("/findPlace")

# перемещение места вверх


@app.route('/findPlace/place/up/<int:rout_id>')
def upPlace(rout_id: int):
    global all_places_position
    if rout_id != 0:
        rout_id -= 1
        all_places_position[rout_id], all_places_position[rout_id -
                                                          1] = all_places_position[rout_id - 1], all_places_position[rout_id]

    return redirect("/findPlace")

# перемещение места вниз


@app.route('/findPlace/place/down/<int:rout_id>')
def downPlace(rout_id: int):
    global all_places_position
    if rout_id != len(all_places_position):
        rout_id -= 1
        all_places_position[rout_id], all_places_position[rout_id +
                                                          1] = all_places_position[rout_id + 1], all_places_position[rout_id]

    return redirect("/findPlace")

# построение маршрута и вывода всей информации


@app.route('/resultPath')
def findPath():
    path, distance = get_route_coordinates([i[0] for i in all_places_position])

    image_bytes = get_travel_image(
        path, [i[0] for i in all_places_position], theme=theme)
    enicoding_image = base64.b64encode(image_bytes).decode('utf-8')

    session_flask['path'] = path
    session_flask['distance'] = distance
    session_flask['enicoding_image'] = enicoding_image

    return render_template('resultPath.html',
                           image_bytes=enicoding_image,
                           distance=distance,
                           places=[i[1] for i in all_places_position],
                           theme=theme)


# сохранение пути
@app.route('/resultPath/savePlace')
@login_required
def savePlace():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(
        User.name == current_user.name).first()

    path_places = []
    for coord in session_flask['path']:
        path_places.append(str(coord[0]))
        path_places.append(str(coord[1]))

    coordinate_places = []
    for coord, _ in all_places_position:
        coordinate_places.append(str(coord[0]))
        coordinate_places.append(str(coord[1]))

    full_adress_places = []
    for _, full_adress in all_places_position:
        full_adress_places.append(full_adress)

    route = Route(
        path='/'.join(path_places),
        distance=session_flask['distance'],
        enicoding_image=session_flask['enicoding_image'],
        user_id=user.id,
        coordinate_places='/'.join(coordinate_places),
        full_adress_places='/'.join(full_adress_places)
    )

    db_sess.add(route)
    db_sess.commit()
    return redirect("/")


@app.route('/resultPath/savePlacePDF')
def savePlacePDF():
    full_adress_places = [f'Общее расстояние: {session_flask["distance"]}', 'Полный путь:']
    for _, full_adress in all_places_position:
        full_adress_places.append(full_adress)

    encoded_image = session_flask['enicoding_image']
    text = '\n'.join(full_adress_places)
    print('---------------', text)

    try:
        image_bytes = base64.b64decode(encoded_image)
    except Exception as e:
        print(f"Error decoding Base64 image: {e}")
        image_bytes = None  # Или какое-то изображение по умолчанию
        img_height = 0  # чтобы код далее не сломался

    # 3. Создание PDF "в памяти"
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    try:
        # Укажите путь к файлу .ttf, если он не в стандартном месте
        pdfmetrics.registerFont(
            TTFont('DejaVuSans', os.path.join('Font', 'DejaVuSans.ttf')))
    except:
        print("DejaVuSans font not found.  Using a fallback.")

    # 4. Размещение изображения
    if image_bytes:  # Проверяем, что image_bytes не None
        try:
            # Создаем временный файл
            # suffix важен для ReportLab
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_image:
                temp_image.write(image_bytes)
                temp_image_path = temp_image.name

            img = Image.open(temp_image_path)
            img_width, img_height = img.size

            # Масштабирование изображения (пример)
            max_width = 5 * inch  # Максимальная ширина изображения
            if img_width > max_width:
                ratio = max_width / img_width
                img_width = max_width
                img_height *= ratio

            # Центрируем изображение по горизонтали
            x = (letter[0] - img_width) / 2
            y = 7 * inch  # Позиция верхнего края изображения

            # **ИЗМЕНЕНИЕ ЗДЕСЬ:** Передаем путь к временному файлу
            p.drawImage(temp_image_path, x, y, width=img_width,
                        height=img_height, mask='auto')

        except Exception as e:
            p.drawString(100, 700, f"Error loading image: {e}")
            img_height = 0  # чтобы текст все равно корректно располагался.
        finally:
            # Гарантируем удаление временного файла, даже если произошла ошибка
            try:
                # Даем время ReportLab закончить чтение файла (задержка 0.1 секунды)
                time.sleep(0.1)
                os.unlink(temp_image_path)
            except Exception as e:
                # Печатаем ошибку, если не удалось удалить файл
                print(f"Error deleting temporary file: {e}")
                pass
    else:
        img_height = 0  # Чтобы не сломался расчет текста

    # 5. Размещение текста под изображением
    # Располагаем текст под изображением (с отступом)
    text_y = y - 0.5 * inch - img_height
    p.setFillColor(colors.black)  # Цвет текста
    p.setFont("DejaVuSans", 12)  # Шрифт и размер

    # Разбиваем текст на строки, чтобы избежать выхода за границы страницы (очень важно!)
    lines = text.split('\n')  # Разбиваем текст на строки по символу \n
    for line in lines:
        # Разбиваем каждую строку на подстроки, чтобы уместить в ширину страницы
        wrapped_lines = wrap_text(
            p, line, "DejaVuSans", 12, letter[0] - 2 * inch)
        for wrapped_line in wrapped_lines:
            p.drawString(inch, text_y, wrapped_line)
            text_y -= 0.3 * inch  # Уменьшаем координату Y для следующей строки

    # 7. Сохранение PDF и отправка
    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='image_and_text.pdf',
        mimetype='application/pdf'
    )


def wrap_text(canvas, text, fontname, fontsize, maxwidth):
    """Разбивает текст на несколько строк, чтобы он помещался в заданную ширину."""
    lines = []
    words = text.split()
    current_line = ""
    for word in words:
        if canvas.stringWidth(current_line + word, fontname, fontsize) <= maxwidth:
            current_line += word + " "
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)
    return lines


@app.route('/showPlaces')
def showPlaces():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(
        User.name == current_user.name).first()

    routs = db_sess.query(Route).filter(
        user.id == Route.user_id).all()
    
    routs_list = []
    for rout in routs:
        routs_list.append(rout.to_dict(
            only=('distance', 'full_adress_places', 'enicoding_image')))
    
    return render_template('showPlaces.html', routs_list=routs_list, theme=theme)

# вход пользователя


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form, theme=theme)
    return render_template('login.html', title='Авторизация', form=form, theme=theme)

# регестрация пользователя


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают",
                                   theme=theme)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть",
                                   theme=theme)
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')

    return render_template('register.html', title='Регистрация', form=form, theme=theme)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


if __name__ == '__main__':
    db_session.global_init("db/travel_planer_explorer.db")
    db_sess = db_session.create_session()

    api.add_resource(users_resource.UsersListResource, '/api/users')
    api.add_resource(users_resource.UsersResource, '/api/users/<int:user_id>')

    api.add_resource(routs_resource.RoutsListResource, '/api/routs')
    api.add_resource(routs_resource.RoutsResource, '/api/routs/<int:rout_id>')

    load_dotenv()
    port = int(os.environ.get("PORT", 5000))  # Используем переменную окружения PORT или 5000
    app.run(port=port, host='0.0.0.0', debug=True)
