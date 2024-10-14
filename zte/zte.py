import hashlib
import re
import requests
import urllib.parse
from jsonpath_ng.ext import parse

from logging import Logger

ZTE_API_BASE = '/goform/'
GET_CMD = 'goform_get_cmd_process'
SET_CMD = 'goform_set_cmd_process'


class ZteModemException(Exception):
    """Raise for my specific kind of exception"""


class ZteConnection:
    """Zte is the class to manage ZTE MC888 device."""

    __logger: Logger
    __host: str
    __url: str
    __password: str
    __ad: str
    __cookie: str

    def __init__(self, logger: Logger, host: str, password: str):
        self.__logger = logger
        self.__host = host
        self.__password = password
        self.__url = "http://" + host + "/"

    def login(self) -> None:
        """Login to ZTE MC888 device."""

        # Collect everything we need from device version call.
        resp = self.__get_device_version()
        self.__logger.debug('login: getDeviceVersion response: %s', str(resp.content))

        query = parse('$.cr_version')
        cr_version = query.find(resp.json())[0].value
        self.__logger.debug('login: crVersion = %s', str(cr_version))

        query = parse('$.wa_inner_version')
        wa_inner_version = query.find(resp.json())[0].value
        self.__logger.debug('login: waInnerVersion = %s', str(wa_inner_version))

        # Collect LD and RD values.
        resp = self.__get_ld()
        query = parse('$.LD')
        ld = query.find(resp.json())[0].value
        self.__logger.debug('login: ld = %s', str(ld))

        resp = self.__get_rd()
        query = parse('$.RD')
        rd = query.find(resp.json())[0].value
        self.__logger.debug('login: rd = %s', str(rd))

        # Calculate password hash (temporary value) and AD (persistent).
        password_hash = ZteConnection.__calculate_password_hash(self.__password, ld)
        self.__ad = ZteConnection.__calculate_ad(cr_version, wa_inner_version, rd)
        self.__logger.debug('login: ad = %s', self.__ad)

        # Send login command.
        resp = self.__send_login_command(password_hash, self.__ad)
        if (result := resp.json()['result']) != '0':
            raise ZteModemException("Non-successful login result: ", result)
        self.__logger.debug('login: http response: %s, body: %s', str(resp.status_code), str(resp.content))

        # Save login cookie.
        cookie = resp.headers.get("Set-Cookie")
        pattern = re.compile('stok=\".*\"')
        self.__logger.debug('login: cookie header: %s', str(cookie))

        result = pattern.search(cookie)
        self.__cookie = result.group(0)
        self.__logger.debug('login: cookie: %s', str(self.__cookie))

    def get_all_sms(self, unread: bool) -> list:
        """Get the list of all SMS."""

        if unread:
            query = parse("$.messages[?(@.tag == '1' & @.received_all_concat_sms == '1')]")
        else:
            query = parse("$.messages[?(@.received_all_concat_sms == '1')]")

        resp = self.__get_sms_list(0, 500)
        return [match.value for match in query.find(resp.json())]

    def read_all_sms(self) -> list:
        """Read all new SMS."""

        query = parse("$.messages[?(@.tag == '1' & @.received_all_concat_sms == '1')]")

        resp = self.__get_sms_list(0, 500)
        matches = [match.value for match in query.find(resp.json())]

        ids = []
        for message in matches:
            ids.append(message['id'])
        self.__logger.debug('read_all_sms: ids: %s', ';'.join(ids))

        # Mark SMS as read.
        resp = self.__set_sms_read(ids)
        if resp is not None:
            if (result := resp.json()['result']) != 'success':
                raise ZteModemException("Non-successful read SMS result: ", result)

        return matches

    def __get_device_version(self) -> requests.Response:
        """Get ZTE device version."""

        headers = {"Referer": self.__url}
        params = {"isTest": "false", "cmd": "Language%2Ccr_version%2Cwa_inner_version", "multi_data": "1"}

        return requests.get(self.__url + ZTE_API_BASE + GET_CMD, params=params, headers=headers)

    def __get_ld(self) -> requests.Response:
        """Get ZTE device LD."""

        headers = {"Referer": self.__url}
        params = {"isTest": "false", "cmd": "LD"}

        return requests.get(self.__url + ZTE_API_BASE + GET_CMD, params=params, headers=headers)

    def __get_rd(self) -> requests.Response:
        """Get ZTE device RD."""

        headers = {"Referer": self.__url}
        params = {"isTest": "false", "cmd": "RD"}

        return requests.get(self.__url + ZTE_API_BASE + GET_CMD, params=params, headers=headers)

    @staticmethod
    def __calculate_password_hash(password: str, ld: str) -> str:
        """Calculate password hash."""

        prefix_hash = hashlib.sha256(password.encode('utf-8')).hexdigest().upper()
        return hashlib.sha256((prefix_hash + ld.upper()).encode('utf-8')).hexdigest().upper()

    @staticmethod
    def __calculate_ad(cr_version: str, wa_inner_version: str, rd: str) -> str:
        """Calculate AD value for login."""

        prefix_hash = hashlib.sha256((wa_inner_version + cr_version).encode('utf-8')).hexdigest().upper()
        return hashlib.sha256((prefix_hash + rd).encode('utf-8')).hexdigest().upper()

    def __send_login_command(self, password_hash: str, ad: str) -> requests.Response:
        """Send ZTE device login command."""

        headers = {"Origin": self.__url, "Referer": self.__url}
        params = {"isTest": "false", "goformId": "LOGIN", "password": password_hash, "AD": ad}

        return requests.post(self.__url + ZTE_API_BASE + SET_CMD, data=params, headers=headers)

    def __get_sms_list(self, page: int, num_entries: int) -> requests.Response:
        """Send ZTE device get SMS command."""

        headers = {"Referer": self.__url, "Cookie": self.__cookie}
        params = {"isTest": "false", "cmd": "sms_data_total", "page": page, "data_per_page": num_entries,
                  "mem_store": "1", "tags": "10", "order_by": "order+by+id+desc"}
        params_safe = urllib.parse.urlencode(params, safe='+')

        return requests.get(self.__url + ZTE_API_BASE + GET_CMD, params=params_safe, headers=headers)

    def __set_sms_read(self, ids: list) -> requests.Response|None:
        if len(ids) == 0:
            return None

        # Build the full list.
        msg_ids = ''
        for msg_id in ids:
            msg_ids = msg_ids + msg_id + ";"

        headers = {"Origin": self.__url, "Referer": self.__url, "Cookie": self.__cookie}
        params = {"isTest": "false", "goformId": "SET_MSG_READ", "msg_id": msg_ids, "tag": "0", "AD": self.__ad}

        return requests.post(self.__url + ZTE_API_BASE + SET_CMD, data=params, headers=headers)
