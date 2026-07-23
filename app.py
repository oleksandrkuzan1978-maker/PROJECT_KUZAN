from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    """Показывает главную страницу с формами поиска."""

    return render_template("index.html")


@app.route("/search")
def search():
    """Получает данные, отправленные формой поиска."""

    search_type = request.args.get("search_type", "")
    title = request.args.get("title", "").strip()

    print("=" * 50)
    print("Получены данные из HTML-формы")
    print(f"Тип поиска: {search_type}")
    print(f"Название фильма: {title}")
    print("=" * 50)

    if search_type != "name":
        return """
            <h2>Неизвестный тип поиска</h2>
            <a href="/">Вернуться на главную страницу</a>
        """

    if not title:
        return """
            <h2>Название фильма не введено</h2>
            <a href="/">Вернуться на главную страницу</a>
        """

    return f"""
        <!doctype html>
        <html lang="ru">
        <head>
            <meta charset="utf-8">

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1"
            >

            <title>Результат поиска</title>

            <link
                href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css"
                rel="stylesheet"
            >
        </head>

        <body class="bg-light">

            <nav class="navbar navbar-dark bg-dark">
                <div class="container">
                    <a class="navbar-brand fw-bold" href="/">
                        🎬 Sakila Movie Search
                    </a>
                </div>
            </nav>

            <main class="container py-5">

                <div class="row justify-content-center">

                    <div class="col-12 col-md-8">

                        <div class="card border-0 shadow">

                            <div class="card-body p-4 p-md-5">

                                <h1 class="h3 mb-4">
                                    Данные успешно получены
                                </h1>

                                <div class="alert alert-success">
                                    Flask получил данные из HTML-формы.
                                </div>

                                <p class="mb-2">
                                    <strong>Тип поиска:</strong>
                                    {search_type}
                                </p>

                                <p class="mb-4">
                                    <strong>Название фильма:</strong>
                                    {title}
                                </p>

                                <a
                                    href="/"
                                    class="btn btn-primary"
                                >
                                    Вернуться к поиску
                                </a>

                            </div>

                        </div>

                    </div>

                </div>

            </main>

        </body>
        </html>
    """

#fffffffffffffffffffffffffffffffffffff
if __name__ == "__main__":
    app.run(debug=True)