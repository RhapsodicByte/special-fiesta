import asyncio
import requests
from bs4 import BeautifulSoup
#mport schedule
import yaml
from telegram import Bot
from telegram.error import TelegramError
from pytz import timezone
from datetime import datetime, timedelta

def load_config():
    with open('config.yaml', 'r') as stream:
        return yaml.safe_load(stream)

config = load_config()

def get_checktoday_data(pin, lastName):
    url = "https://drugtestcheck.com/"

    # Set up session for maintaining cookies
    session = requests.Session()

    # Set headers
    headers = {
        'User-Agent': 'Python/3.x Requests/2.26.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Referer': 'https://drugtestcheck.com/',
        'Origin': 'https://drugtestcheck.com',
    }

    # Set login data
    login_data = {
        'lang': 'en',
        'callInCode': pin,
        'lastName': lastName
    }

    try:
        # Send POST request
        response = session.post(url, headers=headers, data=login_data)
        response.raise_for_status()

        # Parse response
        soup = BeautifulSoup(response.text, 'html.parser')
        result_form = soup.find('form', id='en-result')

        if result_form:
            # Find the reply label
            reply = result_form.find('label', attrs={'for': 'reply'})

            if reply:
                return reply.text.strip()

    except requests.RequestException as e:
        print(f"An error occurred: {e}")

    return None

async def send_telegram(message, bot_token, chat_id, receiver_name):
    try:
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message)
        print(f"Telegram message sent successfully to {receiver_name}.")
    except TelegramError as e:
        print(f"Failed to send Telegram message to {receiver_name}: {e}")

async def job():
    bot_token = config['telegram']['bot_token']

    for receiver in config['receivers']:
        message = get_checktoday_data(receiver['pin'], receiver['lastName'])
        if message:
            print(f"Today's check for {receiver['name']} is: {message}")
            await send_telegram(
                message,
                bot_token,
                receiver['chat_id'],
                receiver['name']
            )
        else:
            print(f"Failed to retrieve check for {receiver['name']}.")

async def schedule_checker():
    config_tz = timezone(config['schedule']['time_zone'])
    while True:
        now = datetime.now(config_tz)
        schedule_times = config['schedule']['times']

        for schedule_time in schedule_times:
            schedule_time = datetime.strptime(schedule_time, "%H:%M").time()
            schedule_datetime = config_tz.localize(datetime.combine(now.date(), schedule_time))

            if now <= schedule_datetime < now + timedelta(minutes=1):
                await job()
                break

        await asyncio.sleep(60)

# Run jobs
if __name__ == '__main__':
    print(f"Starting CheckToday Personalized Telegram Notifier...")
    print(f"Using time zone: {config['schedule']['time_zone']}")

    asyncio.run(schedule_checker())
