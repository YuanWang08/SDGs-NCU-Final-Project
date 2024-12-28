import requests
import librosa

# Azure
from azure.core.credentials import AzureKeyCredential

# Azure Text Analytics
from azure.ai.textanalytics import TextAnalyticsClient

# Azure Translation
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import InputTextItem
from azure.core.exceptions import HttpResponseError
import azure.cognitiveservices.speech as speechsdk

# Config Parser
import configparser

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


def azure_sentiment(user_input):
    text_analytics_client = TextAnalyticsClient(
        endpoint=config["AzureLanguage"]["END_POINT"],
        credential=analyticsCredential)
    documents = [user_input]
    response = text_analytics_client.analyze_sentiment(
        documents, show_opinion_mining=True, language="zh")
    # print(response)
    docs = [doc for doc in response if not doc.is_error]
    return_string = ""
    postivieScore = docs[0].confidence_scores.positive
    if (postivieScore > 0.8):
        return_string += "💪非常正向！"
    elif (postivieScore > 0.6):
        return_string += "👍挺正向的！"
    elif (postivieScore > 0.4):
        return_string += "🧐挺中性的！"
    else:
        return_string += "🙂嗯..."

    return return_string, postivieScore


def azure_computer_vision(image_data):
    endpoint = 'https://eastus.api.cognitive.microsoft.com/'
    uri_base = endpoint + 'computervision/imageanalysis:analyze'
    subscription_key = '49f16aac5bac4185b894e9385bf05fe4'

    params = {
        'api-version': '2023-04-01-preview',
        'language': 'en',
        'features':
        'tags,read,caption,denseCaptions,smartCrops,objects,people',
    }

    headers = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    response = requests.post(uri_base,
                             headers=headers,
                             params=params,
                             data=image_data)

    response.raise_for_status()
    analysis = response.json()

    result_cmvs = ""
    dense_captions = [
        item['text']
        for item in analysis.get('denseCaptionsResult', {}).get('values', [])
    ]
    for caption in dense_captions:
        result_cmvs += caption

    return result_cmvs


def azure_translate(user_input, target_language):
    try:
        target_languages = [target_language]
        input_text_elements = [user_input]
        response = text_translator.translate(body=input_text_elements,
                                             to_language=target_languages)
        translation = response[0] if response else None
        return translation.translations[0].text
    except HttpResponseError as exception:
        print(f"Error Code: {exception.error}")
        print(f"Message: {exception.error.message}")


def azure_speech(translatedMessage, inputLanguage):
    # The language of the voice that speaks.
    speech_config.speech_synthesis_voice_name = "en-CA-ClaraNeural"

    if inputLanguage == "en":
        speech_config.speech_synthesis_voice_name = "en-CA-ClaraNeural"
    elif inputLanguage == "ja":
        speech_config.speech_synthesis_voice_name = "zh-CN-XiaohanNeural"
    elif inputLanguage == "zh-Hans":
        speech_config.speech_synthesis_voice_name = "ja-JP-NanamiNeural"

    file_name = "outputaudio.wav"
    file_config = speechsdk.audio.AudioOutputConfig(filename="static/" +
                                                    file_name)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=file_config)

    # Receives a text from console input and synthesizes it to wave file.
    result = speech_synthesizer.speak_text_async(translatedMessage).get()
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(
            "Speech synthesized for text [{}], and the audio was saved to [{}]"
            .format(translatedMessage, file_name))
        audio_duration = round(
            librosa.get_duration(path="static/outputaudio.wav") * 1000)
        print(audio_duration)
        return audio_duration
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(
            cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(
                cancellation_details.error_details))
