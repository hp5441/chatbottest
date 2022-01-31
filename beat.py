from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler(timezone="Asia/Calcutta")

@sched.scheduled_job('interval', minutes=3)
def timed_job():
    print('app is up')