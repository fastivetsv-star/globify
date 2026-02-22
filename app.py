from flask import Flask, render_template

app = Flask(__name__)

# 1. Головна сторінка
@app.route("/")
def home():
    return render_template("index.html")

# 2. Сторінка з книгами
@app.route("/books")
def books_list():
    # список книг
    library = [
        {"title": "Гаррі Поттер", "author": "Дж. Роулінг", "rating": 10},
        {"title": "Відьмак", "author": "Анджей Сапковський", "rating": 9},
        {"title": "Дюна", "author": "Френк Герберт", "rating": 8}
    ]
    return render_template("books.html", books=library)

@app.route("/films")
def films_list():
    # список фільмів
    library1 = [
        {"title": "Людина Паук", "author": "Стен Ли", "rating": 8},
        {"title": "Прокляття Аннабель", "author": "Гари Доберман", "rating": 9},
        {"title": "Дюна", "author": "Джеймс Ван", "rating": 7}
    ]
    return render_template("films.html", films=library1)
# 3. Контакти
@app.route("/contacts")
def contacts():
    return "<h1>Моя пошта: fastivetsv@gmail.com</h1><p><a href='/'>Назад</a></p>"

if __name__ == "__main__":
    app.run(debug=True)