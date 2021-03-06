from datetime import datetime
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import requests



def tick():
    resp = requests.post("https://chatbotpytest.herokuapp.com/startSession").json()
    print(resp)
    print('Tick! The time is: %s' % datetime.now())


if __name__ == '__main__':
    scheduler = AsyncIOScheduler(timezone="Asia/Calcutta")
    scheduler.add_job(tick, 'interval', minutes=1)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass