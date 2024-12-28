import mysql.connector
import redis
import hashlib
import datetime
import math

# 資料庫配置
db_config = {
    'user': 'root',
    'password': 'my-secret-pw',
    'host': 'localhost',
    'port': 3300,
    'database': 'test_db',
    'autocommit': True,  # Ensures immediate commit
    'connection_timeout': 1200,  # Set an appropriate timeout
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_general_ci'
}

# Redis 配置
redis_config = {'host': 'localhost', 'port': 6379, 'db': 0}


def connect_mysql(db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("Make a MySQL Database connection.")
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        exit(1)


def connect_redis(config):
    try:
        conn = redis.StrictRedis(**config)
        conn.ping()  # 測試連接
        print("Redis connected.")
        return conn
    except redis.ConnectionError as err:
        print(f"Error: {err}")
        exit(1)


def insertFoodRecord(cursor, newFoodObject):
    # 獲取當前時間
    current_time = datetime.datetime.now()

    # 插入食物記錄
    cursor.execute(
        "INSERT INTO food_record (food, location, record_time, validTime) "
        "VALUES (%s, %s, %s, %s)",
        (newFoodObject['food'], newFoodObject['location'], current_time,
         newFoodObject['validTime']))
    print(
        f"New food record '{newFoodObject['food']}' inserted at {current_time}."
    )


def saveFoodRecordToDatabase(newFoodObject):
    db_conn, db_cursor = connect_mysql(db_config)
    redis_conn = connect_redis(redis_config)

    # 嘗試將食物記錄插入MySQL數據庫
    try:
        insertFoodRecord(db_cursor, newFoodObject)
        db_conn.commit()
    except mysql.connector.Error as err:
        print(f"Error inserting a food record: {err}")
        db_conn.rollback()

    # 將食物記錄保存到Redis
    food_id = hashlib.md5(
        newFoodObject['food'].encode()).hexdigest()  # 使用MD5來產生唯一的食物ID

    food_data = {
        'food': newFoodObject['food'],
        'location': newFoodObject['location'],
        'record_time': str(datetime.datetime.now()),  # 儲存為字符串格式
        'validTime': newFoodObject['validTime']
    }

    try:
        # 使用Redis哈希表儲存食物記錄
        redis_conn.hmset(food_id, food_data)
        # 設置有效時間（秒），因為 validTime 已經是秒數，直接設置過期時間
        redis_conn.expire(food_id, newFoodObject['validTime'])
        print(
            f"Food record '{newFoodObject['food']}' saved to Redis with ID {food_id}. It will expire in {newFoodObject['validTime']} seconds."
        )
    except redis.RedisError as err:
        print(f"Error saving to Redis: {err}")

    db_conn.close()
    redis_conn.close()


def getAllFoodRecordsFromRedis(redis_conn):
    all_available_food = []

    # 使用 SCAN 命令遍歷 Redis 中的所有鍵
    cursor = 0
    while True:
        cursor, keys = redis_conn.scan(cursor, match='*')  # 這裡的 '*' 是匹配所有鍵
        for key in keys:
            # 使用 HGETALL 獲取每個鍵的所有欄位和值
            food_data = redis_conn.hgetall(key)
            if food_data:
                # 如果哈希表不為空，將其添加到 all_available_food 中
                all_available_food.append(food_data)

        # 如果 cursor 為 0，表示遍歷完成
        if cursor == 0:
            break

    return all_available_food


def formatFoodRecords(all_food_records):
    formatted_food_list = []

    # 使用 enumerate() 為每條食物記錄添加數字排序
    for idx, food_record in enumerate(all_food_records, 1):
        food = food_record.get(b'food', b'').decode('utf-8')
        location = food_record.get(b'location', b'').decode('utf-8')
        valid_time_seconds = int(food_record.get(b'validTime', 0))

        # 轉換 validTime 由秒轉為小時並無條件進位
        valid_time_hours = math.ceil(valid_time_seconds / 3600)

        # 格式化成所需的字串，並將每條記錄添加到列表
        formatted_food_list.append(
            f"{idx}. {food}/{location}/{valid_time_hours}小時")

    # 返回所有記錄，並確保每條記錄換行
    return "\n".join(formatted_food_list)


def getAvailableFoodRecords():
    # 連接 Redis
    redis_conn = connect_redis(redis_config)

    # 獲取所有食物記錄
    allAvailableFood = getAllFoodRecordsFromRedis(redis_conn)

    # 格式化所有食物記錄
    formatted_food_str = "💖現有的愛心食物：\n" + formatFoodRecords(allAvailableFood)

    return formatted_food_str
