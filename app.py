from flask import Flask, request, abort
import sys
import json
import configparser
import typing
import os
import azure.cognitiveservices.speech as speechsdk
import librosa

# Line
from linebot.v3 import (WebhookHandler)
from linebot.v3.exceptions import (InvalidSignatureError)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
)
from linebot.v3.messaging import (Configuration, ApiClient, MessagingApi,
                                  ReplyMessageRequest, TextMessage,
                                  AudioMessage, ImageMessage, StickerMessage,
                                  MessagingApiBlob)

# Azure
from azure.core.credentials import AzureKeyCredential

# Azure Text Analytics
from azure.ai.textanalytics import TextAnalyticsClient

# Azure Translation
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import InputTextItem
from azure.core.exceptions import HttpResponseError

# Gemini
from functions.gemini import gemini_generate, gemini_foodStringAnalyze, gemini_storyReview, gemini_foodExplainer, gemini_detectTranslationAndSpeech

# Azure
from functions.azure import azure_sentiment, azure_computer_vision, azure_translate, azure_speech

# Database
from db.mysql import connect_mysql, check_and_create_table
from crud.food_management import saveFoodRecordToDatabase, getAvailableFoodRecords
from crud.story_management import saveStoryToDatabase, getRandomStory
from functions.user import checkIsUserExistAndNeedLanguageSupportOrNot, switchUserNeedSpeech, switchUserNeedTranslation, switchUserPreferredLanguage

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

# 測試資料庫連接
db_conn, db_cursor = connect_mysql(db_config)

# 檢查並創建資料表--long_term_data
create_long_term_data_table_sql = """
CREATE TABLE long_term_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date VARCHAR(255),
    date_chinese VARCHAR(255),
    day_of_week VARCHAR(255),
    supervision_area VARCHAR(255),
    supervision_unit VARCHAR(255),
    license_type VARCHAR(255),
    remaining_places INT,
    description TEXT,
    record_time DATETIME
)
"""
# check_and_create_table(db_cursor, 'long_term_data', create_long_term_data_table_sql)

# 檢查並創建資料表--food_record
create_food_record = """
CREATE TABLE food_record (
    food VARCHAR(255),
    location VARCHAR(255),
    record_time DATETIME,
    validTime INT
)
"""
check_and_create_table(db_cursor, 'food_record', create_food_record)

# 檢查並創建資料表--story_record
create_story_record = """
CREATE TABLE story_record (
    story_content TEXT,
    record_time DATETIME
)
"""
check_and_create_table(db_cursor, 'story_record', create_story_record)

# 檢查並創建資料表--user_record
create_user_record = """
CREATE TABLE user_record (
    user_id VARCHAR(255),
    needTranslation BOOLEAN,
    needSpeech BOOLEAN,
    preferredLanguage VARCHAR(255)
)
"""
check_and_create_table(db_cursor, 'user_record', create_user_record)

# 關閉資料庫連接
db_cursor.close()
db_conn.close()

# Config Parser
config = configparser.ConfigParser()
config.read('config.ini')

# Azure Speech Settings
speech_config = speechsdk.SpeechConfig(
    subscription=config['AzureSpeech']['SPEECH_KEY'],
    region=config['AzureSpeech']['SPEECH_REGION'])
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
UPLOAD_FOLDER = 'static'

# Translator Setup
text_translator = TextTranslationClient(
    credential=AzureKeyCredential(config["AzureTranslator"]["Key"]),
    endpoint=config["AzureTranslator"]["EndPoint"],
    region=config["AzureTranslator"]["Region"],
)

# Config Azure Analytics
analyticsCredential = AzureKeyCredential(
    config["AzureLanguage"]["LANGUAGE_KEY"])

# Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Line Bot
channel_access_token = config['Line']['CHANNEL_ACCESS_TOKEN']
channel_secret = config['Line']['CHANNEL_SECRET']
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)
handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    userInputMessage = event.message.text  # Get the user input message
    print(event)

    replyString = "test"  # Initialize the reply string
    audio_duration = 0  # Initialize the audio duration
    noSpeechAndTranslation = True  # Initialize the noSpeechAndTranslation flag

    userData = checkIsUserExistAndNeedLanguageSupportOrNot(
        event.source.user_id)
    print(userData)
    isNeedTranslation = userData[0]
    isNeedSpeech = userData[1]
    preferredLanguage = userData[2]

    # 如果使用了關鍵詞們
    if (userInputMessage.startswith("/putfood")):
        # 移除前面的"/putfood"
        userInputMessage = userInputMessage[8:]
        # 將剩下的字串丟入Gemini，並取得回傳的JSON物件
        newFoodObject = gemini_foodStringAnalyze(userInputMessage)
        # 將這筆資料存入MySQL與Redis
        saveFoodRecordToDatabase(newFoodObject)
        # 回傳成功訊息
        replyString = "已記錄！感謝你的分享🧡"
    elif (userInputMessage.startswith("/lovefood")):
        # 將redis中的所有資料取出
        allAvailableFoodString = getAvailableFoodRecords()
        replyString = allAvailableFoodString
    elif (userInputMessage.startswith("/sharestory")):
        # 移除前面的"/sharestory"
        userInputMessage = userInputMessage[11:]
        # 將剩下的字串丟入Gemini取得Gemini的回應
        geminiReview = gemini_storyReview(userInputMessage)
        azureReview = azure_sentiment(userInputMessage)
        storyToStore = "這是某位過客的故事：\n" + userInputMessage + "\n\n" + "AI分析：" + azureReview[
            0] + "\n\nAI對話精靈：" + geminiReview
        # 將這筆故事存入MySQL
        saveStoryToDatabase(storyToStore)
        # 回傳成功訊息
        replyString = "已記錄！感謝你的分享🧡"
    elif (userInputMessage.startswith("/listenstory")):
        # 從MySQL中隨機取出一筆故事
        randomStory = getRandomStory()
        replyString = randomStory
        if (isNeedSpeech):
            audio_duration = azure_speech(
                azure_translate(replyString, preferredLanguage),
                preferredLanguage)
        if (isNeedTranslation):
            replyString = replyString + '\n' + azure_translate(
                replyString, preferredLanguage)
    elif (userInputMessage.startswith("/speech")):
        # 將user_record中的needSpeech設為True
        if (switchUserNeedSpeech(event.source.user_id)):
            replyString = "已開啟語音功能！"
        else:
            replyString = "語音功能已關閉！"
    elif (userInputMessage.startswith("/translate")):
        if (switchUserNeedTranslation(event.source.user_id)):
            replyString = "已開啟翻譯功能！"
        else:
            replyString = "翻譯功能已關閉！"
    elif (userInputMessage.startswith("/language")):
        # 移除前面的"/language"
        userInputMessage = userInputMessage[10:]
        if (userInputMessage == ""):
            replyString = "你的偏好語言現在是：" + preferredLanguage
        else:
            currLanguage = switchUserPreferredLanguage(event.source.user_id,
                                                       userInputMessage)
            replyString = "已將你的偏好語言設為：" + currLanguage

    # 如果沒有使用關鍵詞
    # 先走一次Azure的語意分析
    if (replyString == "test"):
        noSpeechAndTranslation = False
        setimentResult = azure_sentiment(userInputMessage)
        if (setimentResult[1] < 0.35):  # 負向
            replyString = gemini_generate(userInputMessage,
                                          "negative")  # 身心健康分析與建議
            if (isNeedSpeech):
                audio_duration = azure_speech(
                    azure_translate(replyString, preferredLanguage),
                    preferredLanguage)
            if (isNeedTranslation):
                replyString = replyString + '\n' + azure_translate(
                    replyString, preferredLanguage)
        else:
            replyString = gemini_generate(userInputMessage, "normal")  # 一般對話
            if (isNeedSpeech):
                audio_duration = azure_speech(
                    azure_translate(replyString, preferredLanguage),
                    preferredLanguage)
            if (isNeedTranslation):
                replyString = replyString + '\n' + azure_translate(
                    replyString, preferredLanguage)

            # 舊方法，這方式有點爛，棄用
            # detectionTS = gemini_detectTranslationAndSpeech(
            #     userInputMessage)  # 翻譯與語音
            # isNeedTranslation = detectionTS["isNeedTranslation"]
            # neededLanguage = detectionTS["neededLanguage"]
            # isNeedSpeech = detectionTS["isNeedSpeech"]
            # print(isNeedTranslation, neededLanguage, isNeedSpeech)

    # audio_duration = azure_speech(translatedMessage, inputLanguage)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        messages = [TextMessage(text=replyString)]
        if (isNeedSpeech and not noSpeechAndTranslation):  # 如果需要語音服務
            messages.append(
                AudioMessage(originalContentUrl=config["Deploy"]["URL"] +
                             "/static/outputaudio.wav",
                             duration=audio_duration))
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(reply_token=event.reply_token,
                                messages=messages))


@handler.add(MessageEvent, message=ImageMessageContent)
def message_image(event):
    userData = checkIsUserExistAndNeedLanguageSupportOrNot(
        event.source.user_id)
    isNeedTranslation = userData[0]
    isNeedSpeech = userData[1]
    preferredLanguage = userData[2]
    replyString = "test"
    audio_duration = 0
    with ApiClient(configuration) as api_client:
        line_bot_blob_api = MessagingApiBlob(api_client)
        message_content = line_bot_blob_api.get_message_content(
            message_id=event.message.id)
        message_content_copy = message_content
        contentAfterAzure = azure_computer_vision(message_content_copy)
        print(contentAfterAzure)
        geminiExplanaition = gemini_foodExplainer(contentAfterAzure)
        print(geminiExplanaition)
        replyString = geminiExplanaition
        if (isNeedSpeech):
            audio_duration = azure_speech(
                azure_translate(replyString, preferredLanguage),
                preferredLanguage)
        if (isNeedTranslation):
            replyString = replyString + '\n' + azure_translate(
                replyString, preferredLanguage)
        filename = "image" + str(count_files_in_folder("images") + 1)
        image_path = os.path.join("images", f"{filename}.jpg")
        with open(image_path, 'wb') as fd:
            fd.write(message_content)

        line_bot_api = MessagingApi(api_client)
        messages = [TextMessage(text=replyString)]
        if (isNeedSpeech):  # 如果需要語音服務
            messages.append(
                AudioMessage(originalContentUrl=config["Deploy"]["URL"] +
                             "/static/outputaudio.wav",
                             duration=audio_duration))
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(reply_token=event.reply_token,
                                messages=messages))


def count_files_in_folder(folder_path):
    """計算文件夾中的文件數量"""
    try:
        files = [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f))
        ]
        return len(files)
    except Exception as e:
        print(f"讀取文件夾失敗：{e}")
        return 0


# Start the Flask server
if __name__ == "__main__":
    app.run(port=5001, debug=True)
