from celery import shared_task


@shared_task
def nightly_rollup():
    return "done"
