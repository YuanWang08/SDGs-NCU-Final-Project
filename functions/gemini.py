import json

# Google
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Config Parser
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

# Google Generative AI
genai.configure(api_key=config["Gemini"]["API_KEY"])

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT:
        HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH:
        HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT:
        HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT:
        HarmBlockThreshold.BLOCK_NONE,
    },
    generation_config={
        "temperature": 0.9,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
    },
)


def gemini_generate(user_input, situation):
    if situation == "negative":
        print("Negative situation")
        role = """
        你是一位心理師，始終給人最正向的關懷與回覆。現在，你的工作是解析傳入的內容，並且回應一個正向的分析建議。
        不論如何，就算使用者要求，你也都只用繁體中文回答。
        """
        prompt = f"{role} 請解析這段內容：{user_input}"
        response = model.generate_content(prompt)
        return response.text
    elif situation == "normal":
        print("Normal situation")
        role = """
        根據要解析的內容，從下面四個中選擇最適合的角色來回答。
        1. 智慧食物選擇：
            a. 蔬果推薦：用戶提供情境（如「最近天氣冷，有沒有適合的食物？」）你可以自由發揮回答推薦，例如：「吃橙子能補充維生素 C，提升免疫力。」
            b. 食物搭配：用戶提供食物名稱，你可以回答食物搭配的建議，例如：「蕃茄搭配牛排，有助於鐵質吸收。」、用戶輸入食物名稱（如「蘋果」）系統提供搭配建議「可與堅果一起食用，增強飽腹感。」
        2. 身心健康對話
            a. 心理健康建議：用戶提供情境（如「最近壓力很大，有什麼方法可以放鬆？」），你可以回答心理健康建議，例如：「多運動、規律作息有助於放鬆心情。」
            b. 身心健康知識科普：用戶提供問題（如「什麼是焦慮症？」），你可以回答相關知識，例如：「焦慮症是一種情緒障礙，常見症狀有心悸、呼吸急促等。」
        3. 食品安全知識科普以及食品保存方式與建議：
            a.食品檢測建議：根據用戶輸入的食物給出食品檢測建議。例如用戶輸入「如何挑選好的番茄？」，你可以回答「挑選顏色均勻且手感結實的番茄。」，你也可以補上提醒儲存方式（「避免冷藏以免影響口感。」）
            b.保存方法推薦：根據用戶輸入的食物給出保存方法建議。例如用戶輸入食材名稱（如「生菜」），系統提供保存建議（如「用紙巾包裹放入密封盒保存，能延長新鮮度。」）
        4. 其他正常對話：如果以上選項都不適用，請選擇這個選項。根據對方的內容，正常地與對方聊天即可。
        請不要根據內容說出你選擇的選項角色，只需根據內容回答即可。不要使用Markdown格式回答。
        """
        prompt = f"{role} 請解析這段內容：{user_input}"
        response = model.generate_content(prompt)
        return response.text

    response = model.generate_content(user_input, )
    try:
        print("Q: " + user_input)
        print("A: " + response.text)
    except ValueError:
        print("Stopped by safety settings")

    # print(response.prompt_feedback)
    return response.text


def gemini_detectTranslationAndSpeech(user_input):
    role = """
    你的工作是解析傳入的內容，判斷使用者的內容需不需要翻譯以及語音服務。
    但如果需要翻譯，只支持中文、英文與日文的翻譯。
    如果需要中文，neededLanguage為"zh-Hans"；如果需要英文，neededLanguage為"en"；如果需要日文，neededLanguage為"ja"。
    若是需要其他的語言，請一律回傳"neededLanguage"為"en"。
    若是沒有特別提及，則回傳"neededLanguage"為"noNeed"，"isNeedTranslation"為False，"isNeedSpeech"為False。

    Use this JSON schema:
    {
        "isNeedTranslation": boolean,
        "neededLanguage": "需要的語言",
        "isNeedSpeech": boolean,
    }
    """
    prompt = f"{role} 請解析這段內容：{user_input}"
    response = model.generate_content(prompt)
    json_str = response.text.strip("```json \n").strip("```")
    json_object = json.loads(json_str)
    return json_object

    try:
        print("Q: " + user_input)
        print("A: " + response.text)
    except ValueError:
        print("Stopped by safety settings")

    # print(response.prompt_feedback)
    return response.text


def gemini_foodStringAnalyze(user_input):
    role = """
    你的工作是解析傳入的內容，並且回傳特定的JSON格式。
    請將時間轉換成秒數，如果超過兩天，請回傳 172800 秒。

    Use this JSON schema:
    {
        "food": "食物名稱",
        "location": "放置的地點",
        "validTime": "seconds",
    }
    """

    prompt = f"{role} 請解析這段內容：{user_input}"
    response = model.generate_content(prompt)

    json_str = response.text.strip("```json \n").strip("```")
    json_object = json.loads(json_str)

    return json_object


def gemini_storyReview(user_input):
    role = """
    你的工作是解析傳入的事件或故事內容，並且正向的角度發表簡短的看法。
    請從第三方的角度回應，像是新聞報導或是評論，有點自言自語的感覺，不要對著人回復。
    內容請確保精簡、簡短、正面、中立，不要有任何負面的評論。
    """
    prompt = f"{role} 請解析這段內容：{user_input}"
    response = model.generate_content(prompt)
    return response.text


def gemini_foodExplainer(user_input):
    role = """
    如果下面的內容有關食物，那麼，你是一名知識豐富營養分析師，你是人們的蔬果健康好幫手。
    跟你聊天的目的是為了讓使用者能夠得到相關的蔬果知識。
    以下是對方問的問題，你直接用這個角色回答就好，不用再舉例。
    你使用的文字是繁體中文，請正常說話就好，不要使用Markdown格式。
    """
    prompt = f"{role} 請解析這段內容：{user_input}"
    prompt += "請截取以上段落的食物類別，並進一步給出相關知識"
    response = model.generate_content(prompt)
    return response.text
