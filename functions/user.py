import mysql.connector

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


def connect_mysql(db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("Make a MySQL Database connection.")
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        exit(1)


def checkIsUserExistAndNeedLanguageSupportOrNot(user_id):
    # 檢查用戶是否存在，如果用戶不存在，則返回False, False，並創建新的用戶
    # 如果用戶存在，則根據用戶的需求返回是否需要翻譯與語音服務
    db_conn, db_cursor = connect_mysql(db_config)
    db_cursor.execute("SELECT * FROM user_record WHERE user_id = %s",
                      (user_id, ))
    result = db_cursor.fetchone()
    if not result:
        # 用戶不存在，創建新用戶
        db_cursor.execute(
            "INSERT INTO user_record (user_id, needTranslation, needSpeech, preferredLanguage) VALUES (%s, %s, %s, %s)",
            (user_id, False, False, "zh-Hans"))
        db_conn.commit()
        return False, False, "zh-Hans"
    else:
        # 用戶存在，返回用戶需求
        return result[1], result[2], result[3]


def switchUserNeedSpeech(user_id):
    # 切換用戶是否需要語音服務
    # 如果原本是True，則切換為False
    # 如果原本是False，則切換為True
    # 返回切換後的結果
    db_conn, db_cursor = connect_mysql(db_config)
    db_cursor.execute("SELECT needSpeech FROM user_record WHERE user_id = %s",
                      (user_id, ))
    result = db_cursor.fetchone()
    if result[0]:
        db_cursor.execute(
            "UPDATE user_record SET needSpeech = %s WHERE user_id = %s",
            (False, user_id))
        db_conn.commit()
        return False
    else:
        db_cursor.execute(
            "UPDATE user_record SET needSpeech = %s WHERE user_id = %s",
            (True, user_id))
        db_conn.commit()
        return True


def switchUserNeedTranslation(user_id):
    # 切換用戶是否需要翻譯服務
    # 如果原本是True，則切換為False
    # 如果原本是False，則切換為True
    # 返回切換後的結果
    db_conn, db_cursor = connect_mysql(db_config)
    db_cursor.execute(
        "SELECT needTranslation FROM user_record WHERE user_id = %s",
        (user_id, ))
    result = db_cursor.fetchone()
    if result[0]:
        db_cursor.execute(
            "UPDATE user_record SET needTranslation = %s WHERE user_id = %s",
            (False, user_id))
        db_conn.commit()
        return False
    else:
        db_cursor.execute(
            "UPDATE user_record SET needTranslation = %s WHERE user_id = %s",
            (True, user_id))
        db_conn.commit()
        return True


def switchUserPreferredLanguage(user_id, new_language):
    # 切換用戶的首選語言
    # 返回切換後的結果
    db_conn, db_cursor = connect_mysql(db_config)
    print(new_language)
    # 目前支援的語言
    supportLanguages = ["zh-Hans", "en", "ja"]
    # 如果新語言不在支援的語言列表中，則返回原本"en"
    if new_language not in supportLanguages:
        new_language = "en"

    db_cursor.execute(
        "UPDATE user_record SET preferredLanguage = %s WHERE user_id = %s",
        (new_language, user_id))
    db_conn.commit()

    return new_language
