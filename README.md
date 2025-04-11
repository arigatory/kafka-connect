# Инструкция по запуску и настройке проекта CDC с Debezium и PostgreSQL

## Содержание
1. [Запуск проекта через Docker Compose](#запуск-проекта-через-docker-compose)
2. [Описание компонентов](#описание-компонентов)
3. [Настройка Debezium Connector](#настройка-debezium-connector)
4. [Проверка работоспособности](#проверка-работоспособности)

---

## Запуск проекта через Docker Compose

1. **Убедитесь, что у вас установлены:**
   - Docker
   - Docker Compose
   - curl (для тестирования API)
   - jq (для форматирования JSON)

2. **Склонируйте репозиторий (если есть) или создайте файлы:**
   - `docker-compose.yml` (из вашего примера)
   - `connector.json` (конфигурация Debezium)

3. **Запустите сервисы:**
   ```bash
   docker-compose up -d
   ```

4. **Дождитесь инициализации всех компонентов** (2-3 минуты)

---

## Описание компонентов

### 1. Apache Kafka (KRaft режим)
- **kafka-0, kafka-1, kafka-2**: Три брокера Kafka в режиме KRaft (без Zookeeper)
- **Назначение**: Хранение и обработка потоковых данных изменений из PostgreSQL
- **Порты**: 
  - 9094-9096: внешние подключения
  - 9092: внутренняя коммуникация

### 2. PostgreSQL
- **Контейнер**: `postgres` с образом debezium/postgres
- **Назначение**: Исходная база данных, изменения которой отслеживаются
- **Настройки**:
  - Пользователь: `postgres-user`
  - Пароль: `postgres-pw`
  - БД: `customers`

### 3. Kafka Connect
- **Контейнер**: `kafka-connect` с Debezium
- **Назначение**: Прием изменений из PostgreSQL и отправка в Kafka
- **Порт**: 8083 (REST API)

### 4. Schema Registry
- **Контейнер**: `schema-registry`
- **Назначение**: Управление схемами данных Avro
- **Порт**: 8081

### 5. Kafka UI
- **Контейнер**: `ui`
- **Назначение**: Визуальный интерфейс для мониторинга Kafka
- **Порт**: 8085

### 6. Prometheus + Grafana
- **Назначение**: Мониторинг метрик Kafka и Connect
- **Порты**:
  - Prometheus: 9090
  - Grafana: 3000

---

## Настройка Debezium Connector

Ваша конфигурация (`connector.json`) включает следующие ключевые параметры:

```json
{
  "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
  "database.hostname": "postgres",
  "database.port": "5432",
  "database.user": "postgres-user",
  "database.password": "postgres-pw",
  "database.dbname": "customers",
  "database.server.name": "customers",
  "table.include.list": "public.users,public.orders",
  "transforms": "unwrap",
  "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
  "transforms.unwrap.drop.tombstones": "false",
  "transforms.unwrap.delete.handling.mode": "rewrite",
  "topic.prefix": "customers",
  "topic.creation.enable": "true",
  "topic.creation.default.replication.factor": "-1",
  "topic.creation.default.partitions": "-1",
  "skipped.operations": "none"
}
```

### Ключевые параметры:
1. **table.include.list** - отслеживаемые таблицы (`users` и `orders`)
2. **transforms.unwrap** - преобразование сложной структуры Debezium в плоскую
3. **topic.prefix** - префикс для топиков (`customers.public.users`)
4. **skipped.operations** - не пропускать никакие операции (все отслеживать)

### Регистрация коннектора:
```bash
curl -X PUT -H 'Content-Type: application/json' \
  --data @connector.json \
  http://localhost:8083/connectors/pg-connector/config | jq
```

---

## Проверка работоспособности

### 1. Проверка статуса коннектора
```bash
curl -s http://localhost:8083/connectors/pg-connector/status | jq
```

**Ожидаемый результат:** `"state": "RUNNING"`

### 2. Проверка списка топиков
```bash
docker exec -it kafka-0 /opt/bitnami/kafka/bin/kafka-topics.sh \
  --list --bootstrap-server localhost:9092
```

**Должны отобразиться:**
- `customers.public.users`
- `customers.public.orders`

### 3. Тестирование с данными

**Добавьте тестовые данные в PostgreSQL:**
```bash
docker exec -it postgres psql -U postgres-user customers -c \
  "INSERT INTO users (name, email) VALUES ('Тестовый пользователь', 'test@example.com');"
```

**Проверьте сообщение в топике:**
```bash
docker exec -it kafka-0 /opt/bitnami/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic customers.public.users \
  --from-beginning
```

### 4. Проверка через Kafka UI
Откройте в браузере: `http://localhost:8085`

Проверьте:
1. Наличие кластера `kraft`
2. Топики с префиксом `customers`
3. Сообщения в топиках

### 5. Графический мониторинг
Откройте Grafana: `http://localhost:3000`
- Логин/пароль по умолчанию: admin/admin
- Проверьте дашборды с метриками Kafka

---

## Устранение проблем

1. **Коннектор не запускается**:
   - Проверьте логи: `docker logs kafka-connect`
   - Убедитесь, что PostgreSQL доступен из контейнера Connect

2. **Нет данных в топиках**:
   - Проверьте, что в таблицах есть данные
   - Убедитесь, что коннектор отслеживает нужные таблицы

3. **Ошибки подключения**:
   - Проверьте сеть Docker: `docker network inspect custom_network`
   - Убедитесь, что все сервисы в одной сети