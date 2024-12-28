import mysql.connector
import redis
import datetime
import math
import random

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


def insertStory(cursor, storyToStore):
    # 獲取當前時間
    current_time = datetime.datetime.now()

    # 執行插入操作
    cursor.execute(
        "INSERT INTO story_record (story_content, record_time) VALUES (%s, %s)",
        (storyToStore, current_time))
    print(
        f"New story record inserted at {current_time}. Story: {storyToStore}")


def saveStoryToDatabase(storyToStore):
    db_conn, db_cursor = connect_mysql(db_config)

    # 嘗試將故事記錄插入MySQL數據庫
    try:
        insertStory(db_cursor, storyToStore)
        db_conn.commit()
    except mysql.connector.Error as err:
        print(f"Error inserting a story: {err}")
        db_conn.rollback()

    db_conn.close()


def getRandomStory():
    db_conn, db_cursor = connect_mysql(db_config)

    # 獲取故事記錄數量
    db_cursor.execute("SELECT COUNT(*) FROM story_record")
    total_records = db_cursor.fetchone()[0]

    # 獲取隨機故事
    random_index = math.floor(random.random() * total_records)
    db_cursor.execute(
        "SELECT story_content FROM story_record LIMIT 1 OFFSET %s",
        (random_index, ))
    random_story = db_cursor.fetchone()[0]

    db_conn.close()
    return random_story
