import sqlite3
from typing import Iterator

# Создаём коннектор - подключение к БД
conn = sqlite3.connect('my_database.db')

# Создание курсора для выполнения SQL-запросов
cursor = conn.cursor()


# Создаём таблицу `users` для хранения информации о пользователях.
q_create_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        email TEXT
    );"""

cursor.execute(q_create_table)

# Сохраняем изменения в базе данных
conn.commit()

# Добавляем новую запись в таблицу `users`.

q_insert = "INSERT INTO users (name, age, email) VALUES (?, ?, ?);"
cursor.execute(q_insert,("John Doe", 25, "johndoe@example.com"))

# Сохраняем изменения
conn.commit()


# Получаем и выводим все записи из таблицы `users`.
cursor.execute("SELECT * FROM users;")
conn.commit()
# Курсор - это итератор?
print("Курсор - это итератор?", isinstance(cursor, Iterator))
# Курсор - это итератор? True

print(cursor.fetchall())  # [(1, 'John Doe', 25, 'johndoe@example.com')]
print(cursor.fetchall())  # []

# То же самое с помощью цикла for
cursor.execute("SELECT * FROM users;")

for row in cursor:
    print(row)
conn.commit()