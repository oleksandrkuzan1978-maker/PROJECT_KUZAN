import pandas as pd
import sqlite3
#Тема
# Создаём словарь с данными
data = {
    'column1': ['value1', 'value2', 'value3'],
    'column2': ['value1', 'value2', 'value3'],
    'column3': ['value1', 'value2', 'value3'],
}

# Преобразуем словарь в DataFrame
df = pd.DataFrame(data)

# Выводим таблицу
print(df)

#   column1 column2 column3
# 0  value1  value1  value1
# 1  value2  value2  value2
# 2  value3  value3  value3


# 1. Создаём подключение к СУБД SQLite
conn = sqlite3.connect('students.db')

# 2. `pandas` содержит встроенный метод `to_sql`, благодаря чему
df.to_sql(
    'new_table',   # имя таблицы в БД
    conn,          # подключение к базе
    if_exists='replace',  # заменить таблицу, если она уже существует
    index=False    # не сохранять индекс pandas как отдельный столбец
)

# Выполняем SQL-запрос и сразу получаем DataFrame
df_from_db = pd.read_sql_query(
    'SELECT * FROM new_table',
    conn
)

# Вывод результата
print(df_from_db)

#   column1 column2 column3
# 0  value1  value1  value1
# 1  value2  value2  value2
# 2  value3  value3  value3