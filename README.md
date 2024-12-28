# SDGs-NCU-Final-Project AI 身心食安對話精靈

組員：王暐元、陳柏衡、王亦丞、黃以得、許紹元

這是一個 LineBot 對話機器人，他是你的心理師、也是你的營養師、更是一位分享家

他提供：智慧食物選擇、影像分析支持、身心健康對話、食安解惑、心理諮商、剩食分享平台、正能量漂流瓶、自訂偏好語言、一鍵開啟多語言、一鍵開啟語音回復

SDGs：終結貧窮（SDG 1）、消除飢餓（SDG 2）、健康與福祉（SDG 3）、保育海洋生物（SDG 14）、保育陸域生物（SDG 15）

## 如何啟用 How to Start？

1. 先將資料夾載下來
2. 進入資料夾目錄，輸入"docker compose up -d"，建立 mysql 與 redis 的映像
3. 申請 Azure Token，將 config.ini.example 補上(移除.example)
4. 申請 LineBot 帳號，填上 CHANNEL_ACCESS_TOKEN & CHANNEL_SECRET
5. 申請並填上 Gemini API Key
6. 將 Deploy 的 URL 換成自己的端口(Maybe Ngrok)
7. 輸入"python app.py"執行，需要安裝的套件都列在 requirements.txt
