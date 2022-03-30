
import requests

from app.util import report


def get_latest_release_version():
    release_url = "https://api.github.com/repos/FrandsenGroup/beams/releases/latest"
    release_key = "tag_name"

    try:
        response = requests.get(release_url)

        if response.status_code != requests.codes.ok:
            report.report_info(response.content)
            return
        else:
            return response.json()[release_key]

    except requests.exceptions.ConnectionError:
        raise BeamsNetworkError("Not connected to the internet.")
    except Exception as e:
        report.report_exception(e)
        raise BeamsNetworkError("An error occurred retrieving the latest release version of beams.") from e


class BeamsNetworkError(Exception):
    def __init__(self, *args, **kwargs):
        super(BeamsNetworkError, self).__init__(args, kwargs)
