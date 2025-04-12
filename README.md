# Инструкция по проверке проекта CDC с Debezium и PostgreSQL

## Проверка работоспособности

1. Поднять инфраструктуру
```
docker compose up -d
```

2. Создать таблицы
```
docker exec -it postgres psql -U postgres-user customers -c "
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    product_name VARCHAR(100),
    quantity INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"
```

3. Создать коннектор
```
curl -X PUT -H 'Content-Type: application/json' --data @connector-truncate.json http://localhost:8083/connectors/pg-connector/config |jq
```

4. Добавить данные в БД
```
docker exec -it postgres psql -U postgres-user customers -c "
INSERT INTO users (name, email) VALUES 
  ('Алексей Смирнов', 'alex@test.com'),
  ('Мария Иванова', 'maria@test.com');

INSERT INTO orders (user_id, product_name, quantity) VALUES
  (1, 'Монитор', 2),
  (2, 'Клавиатура', 1);"
```

5. Считать данные из топиков
```
python kafka_consumer.py
```
