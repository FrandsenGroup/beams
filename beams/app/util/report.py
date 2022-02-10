
import sentry_sdk
import logging
import traceback

from app.resources import resources


def get_exception_stack(e: Exception):
    return ''.join(traceback.format_exception(type(e), e, e.__traceback__))


def init_reporting():
    sentry_sdk.init(
        "https://ff7cf26a5b3d4d2ab1ff98320448fa04@o1139782.ingest.sentry.io/6196236",
        max_breadcrumbs=50,
        traces_sample_rate=1.0,
        attach_stacktrace=True,
        release="beams@0.1.0",
        environment="development",
        send_default_pii=True
    )

    logging.getLogger('matplotlib').setLevel(logging.ERROR)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    file = logging.FileHandler(resources.QT_LOG_FILE)
    file.setLevel(logging.DEBUG)
    logger.addHandler(file)

    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO)
    logger.addHandler(stream)


def close():
    client = sentry_sdk.Hub.current.client

    if client is not None:
        client.close(timeout=2.0)


def log_debug(m):
    try:
        logging.getLogger(__name__).debug(m)
    except Exception as ie:
        print(get_exception_stack(ie))
        print(m)


def log_info(m):
    try:
        logging.getLogger(__name__).info(m)
    except Exception as ie:
        print(get_exception_stack(ie))
        print(m)


def log_exception(e):
    try:
        logging.getLogger(__name__).error(get_exception_stack(e))
    except Exception as ie:
        print(get_exception_stack(ie))
        print(get_exception_stack(e))


def report_info(m):
    try:
        sentry_sdk.capture_message(m)
    except Exception as ie:
        log_info(m)
        log_exception(ie)


def report_exception(e, prompt=False):
    try:
        sentry_sdk.capture_exception(e)
    except Exception as ie:
        log_exception(e)
        log_exception(ie)
