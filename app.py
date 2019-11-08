from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import paho.mqtt.client as mqtt
import time

app = Flask(__name__)

# *********************************************************************
# MQTT 組態設定

MQTT_SERVER = "soldier.cloudmqtt.com"
MQTT_USERNAME = "xxx"
MQTT_PASSWORD = "xxx"
MQTT_PORT = 12571
MQTT_ALIVE = 60
MQTT_TOPIC = "Door/Lock"

# *********************************************************************
line_bot_api = LineBotApi('xxx')
handler = WebhookHandler('xxx')

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(msg.topic + " " + msg.payload.decode("utf-8"))

def mqtt_publish(msg):
    client_id = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
    client = mqtt.Client(client_id)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, 60)
    client.publish(MQTT_TOPIC, msg, qos=0, retain=False)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):    
    if event.message.text == '開門':
        confirm_template_message = TemplateSendMessage(
            alt_text='確定要開門嗎？',
            template=ConfirmTemplate(
                text='確定要開門嗎？',
                actions=[                
                    MessageAction(
                        label='是',
                        text='是'
                    ),
                    MessageAction(
                        label='否',
                        text='否'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, confirm_template_message)

    if event.message.text == '警鈴':
        mqtt_publish('alert')

    if event.message.text == '是':
        mqtt_publish('open')


if __name__ == "__main__":
    app.run()
