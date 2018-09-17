from urllib.parse import urlparse
import socket
import json

import requests

from parsedmarc import __version__


class SplunkError(RuntimeError):
    """Raised when a Splunk API error occurs"""


class HECClient(object):
    """A client for a Splunk HTTP Events Collector (HEC)"""

    # http://docs.splunk.com/Documentation/Splunk/latest/Data/AboutHEC
    # http://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTinput#services.2Fcollector

    def __init__(self, url, access_token, index="dmarc",
                 source="parsedmarc", verify=True):
        """
        Initializes the HECClient
        Args:
            url (str): The URL of the HEC
            access_token (str): The HEC access token
            index (str): The name of the index
            source (str): The source name
            verify (bool): Verify SSL certificates
        """
        url = urlparse(url)
        self.url = "{0}://{1}/services/collector/event/1.0".format(url.scheme,
                                                                   url.netloc)
        self.access_token = access_token.lstrip("Splunk ")
        self.index = index
        self.host = socket.getfqdn()
        self.source = source
        self.session = requests.Session()
        self.session.verify = verify
        self._common_data = dict(host=self.host, source=self.source,
                                 index=self.index)

        self.session.headers = {
            "User-Agent": "parsedmarc/{0}".format(__version__),
            "Authorization": "Splunk {0}".format(self.access_token)
        }

    def save_aggregate_reports_to_splunk(self, aggregate_reports):
        """
        Saves aggregate DMARC reports to Splunk

        Args:
            aggregate_reports (list): A list of aggregate report dictionaries
            to save in Splunk

        """
        if type(aggregate_reports) == dict:
            aggregate_reports = [aggregate_reports]

        json_str = ""
        for report in aggregate_reports:
            data = self._common_data.copy()
            data["sourcetype"] = "dmarc_aggregate"
            data["event"] = report.copy()
            json_str += "{0}\n".format(json.dumps(data))

        try:
            response = self.session.post(self.url, json=json_str).json()
        except Exception as e:
            raise SplunkError(e.__str__())
        if response["code"] != 0:
            raise SplunkError(response["text"])

    def save_forensic_reports_to_splunk(self, aggregate_reports):
        """
        Saves forensic DMARC reports to Splunk

        Args:
            aggregate_reports (list):  A list of forensic report dictionaries
            to save in Splunk

        """
        if type(aggregate_reports) == dict:
            aggregate_reports = [aggregate_reports]

        json_str = ""
        for report in aggregate_reports:
            data = self._common_data.copy()
            data["sourcetype"] = "dmarc_forensic"
            data["event"] = report.copy()
            json_str += "{0}\n".format(json.dumps(data))

        try:
            response = self.session.post(self.url, json=json_str).json()
        except Exception as e:
            raise SplunkError(e.__str__())
        if response["code"] != 0:
            raise SplunkError(response["text"])
