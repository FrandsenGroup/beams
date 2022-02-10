
import sentry_sdk
import logging
import traceback


def get_exception_stack(e: Exception):
    return ''.join(traceback.format_exception(type(e), e, e.__traceback__))


def init_reporting():
    pass


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
