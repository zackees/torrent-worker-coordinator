"""
Common code for integration tests.
"""

# flake8: noqa: E402
# pylint: disable=wrong-import-position,too-many-public-methods,unused-import,self-assigning-variable

import contextlib
import os
import sys
import threading
import time

import uvicorn

# from androidmonitor_backend.testing.db_test_env import db_test_env_init
from uvicorn.main import Config

# no androidmonitor_backend.* imports allowed


# no androidmonitor_backend.* imports allowed

# Change set the DB_URL environment variable to a temporary sqlite database.
# This needs to be done before importing the app.
HERE = os.path.dirname(os.path.abspath(__file__))

# DB_URL = db_test_env_init()
# os.environ["ALLOW_DB_CLEAR"] = "1"
# os.environ["SHOW_DB_URL"] = "1"

# if debugger is attached
if sys.gettrace():
    TIMEOUT = 1000000
else:
    TIMEOUT = 5  # seconds

# # androidmonitor_backend.* allowed.
# from androidmonitor_backend.settings import API_ADMIN_KEY, CLIENT_API_KEYS
# from androidmonitor_backend.types import ClientLogQuery, DeviceInfo, LogInfo, UserQuery
# from androidmonitor_backend.util import current_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
# TEST_MP4 = os.path.join(HERE, "test.mp4")
# TEST_JSON = os.path.join(HERE, "test.json")
# TEST_V05_JSON = os.path.join(HERE, "test.v05.json")

APP_NAME = "torrent_worker_coordinator.app:app"
HOST = "localhost"
PORT = 4424  # Arbitrarily chosen.

# CLIENT_API_KEYS = CLIENT_API_KEYS
# current_datetime = current_datetime  #

# URL = f"http://{HOST}:{PORT}"
# ENDPOINT_ADD_UID = f"{URL}/v1/add_uid"
# ENDPOINT_REUSE_UID = f"{URL}/v1/reuse_uid"
# ENDPOINT_GETINFO_JSON = f"{URL}/v1/info/json"
# ENDPOINT_CLIENT_REGISTER = f"{URL}/v1/client_register"
# ENDPOINT_IS_CLIENT_REGISTERED = f"{URL}/v1/is_client_registered"
# ENDPOINT_LIST_UIDS = f"{URL}/v1/list/uids"
# ENDPOINT_LOGGED_IN = f"{URL}/v1/logged_in/operator"
# ENDPOINT_UPLOAD = f"{URL}/v1/upload"
# ENDPOINT_LIST_UPLOADS = f"{URL}/v1/list/uploads"
# ENDPOINT_DOWNLOAD_VIDEO = f"{URL}/v1/download/video"
# ENDPOINT_DB_DUMP_SCHEMA = f"{URL}/db/schema"
# ENDPOINT_CLIENT_SETTINGS = f"{URL}/v1/client_settings"
# ENDPOINT_APK_UPDATE = f"{URL}/apk/update"
# ENDPOINT_APK_UPDATE_DEBUG = f"{URL}/apk/update/debug"
# ENDPOINT_REPORT_CRASH = f"{URL}/v1/report/crash"
# ENDPOINT_QUERY_CRASH_REPORT = f"{URL}/query/crashes"
# ENDPOINT_QUERY_RECENT_CRASH_REPORT = f"{URL}/query/crashes/recent"
# ENDPOINT_CLEAR = f"{URL}/clear"
# ENDPOINT_LIST_USERS = f"{URL}/list/users"
# ENDPOINT_QUERY_STATS = f"{URL}/query/stats"
# ENDPOINT_QUERY_USERS = f"{URL}/query/users"
# ENDPOINT_LIST_LOG_IDS = f"{URL}/list/logs"
# ENDPOINT_UPLOAD_LOG = f"{URL}/v1/upload/log"
# ENDPOINT_QUERY_CLIENT_LOGS = f"{URL}/query/client_logs"


# Surprisingly uvicorn does allow graceful shutdowns, making testing hard.
# This class is the stack overflow answer to work around this limitiation.
# Note: Running this in python 3.8 and below will cause the console to spew
# scary warnings during test runs:
#   ValueError: set_wakeup_fd only works in main thread
class ServerWithShutdown(uvicorn.Server):
    """Adds a shutdown method to the uvicorn server."""

    def install_signal_handlers(self):
        pass


@contextlib.contextmanager
def run_server_in_thread():
    """
    Useful for testing, this function brings up a server.
    It's a context manager so that it can be used in a with statement.
    """
    config = Config(
        APP_NAME,
        host=HOST,
        port=PORT,
        log_level="info",
        use_colors=False,
    )
    server = ServerWithShutdown(config=config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        while not server.started:
            time.sleep(1e-3)
        # info = request_get_info(api_key=API_ADMIN_KEY)
        # assert (
        #     info["DB_URL"] == DB_URL
        # ), f"DB_URL is {info['DB_URL']}, expected {DB_URL}"
        yield
    finally:
        server.should_exit = True
        thread.join()


# def request_logged_in(api_key: str) -> bool:
#     """Test the logged_in endpoint."""
#     headers = {
#         "Accept": "application/json",
#         "x-api-admin-key": api_key,
#     }
#     response = requests.get(ENDPOINT_LOGGED_IN, headers=headers, timeout=TIMEOUT)
#     response.raise_for_status()
#     response_data = response.json()
#     return response_data.get("ok")


# def request_db_dump_schema(api_key: str) -> dict[str, Any]:
#     """Test the db_dump_schema endpoint."""
#     headers = {
#         "Accept": "application/json",
#         "x-api-admin-key": api_key,
#     }
#     response = requests.get(ENDPOINT_DB_DUMP_SCHEMA, headers=headers, timeout=TIMEOUT)
#     response.raise_for_status()
#     return response.json()


# def request_list_uids(
#     api_key: str, start: str | None = None, end: str | None = None
# ) -> dict[str, str]:
#     """Test the list_uids endpoint."""
#     headers = {
#         "Accept": "application/json",
#         "x-api-key": api_key,
#         "Content-Type": "application/json",
#     }
#     payload = {}
#     if start is not None:
#         payload["start"] = start
#     if end is not None:
#         payload["end"] = end
#     payload_json = json.dumps({"start": start, "end": end})
#     response = requests.post(
#         ENDPOINT_LIST_UIDS, headers=headers, data=payload_json, timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     response_data = response.json()
#     # Check that the UID was added to the list
#     return response_data


# def request_get_info(api_key: str) -> dict:
#     """Test the getinfo endpoint."""
#     headers = {
#         "Accept": "application/json",
#         "x-api-admin-key": api_key,
#     }
#     response = requests.get(ENDPOINT_GETINFO_JSON, headers=headers, timeout=TIMEOUT)
#     response.raise_for_status()
#     content = response.json()
#     return content


# def request_add_uid(api_key: str) -> str:
#     """Test the add_uid endpoint."""
#     headers = {
#         "accept": "application/json",
#         "x-api-admin-key": api_key,
#     }
#     response = requests.get(ENDPOINT_ADD_UID, headers=headers, timeout=TIMEOUT)
#     response.raise_for_status()
#     response_data = response.json()
#     assert response_data.get("ok")
#     uid = response_data.get("uid", "")
#     assert uid, "Expected UID to be returned"
#     return uid


# def request_list_users(api_key: str, uids: list[str]) -> dict[str, str]:
#     """Test the list_users endpoint."""
#     headers = {
#         "accept": "application/json",
#         "x-api-admin-key": api_key,
#     }
#     data = {
#         "uids": uids,
#     }
#     response = requests.post(
#         ENDPOINT_LIST_USERS, headers=headers, json=data, timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     response_data = response.json()
#     return response_data


# def request_reuse_uid(api_key: str, uid: str) -> None:
#     """Test the reuse_uid endpoint."""
#     headers = {
#         "accept": "application/json",
#         "x-api-admin-key": api_key,
#     }
#     data = {
#         "uid": uid,
#     }
#     response = requests.post(
#         ENDPOINT_REUSE_UID, headers=headers, json=data, timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     response_data = response.json()
#     assert response_data.get("ok")


# def request_is_client_registerd(token: str) -> bool:
#     """Test the is_client_registered endpoint."""
#     headers = {"x-client-token": token}
#     response = requests.get(
#         ENDPOINT_IS_CLIENT_REGISTERED, headers=headers, timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     response_data = response.json()
#     return response_data.get("is_registered")


# def request_list_logs(api_admin_key: str, uid: str) -> list[LogInfo]:
#     """Test the list_logs endpoint."""
#     headers = {
#         "accept": "application/json",
#         "x-api-admin-key": api_admin_key,
#     }
#     uid = uid.replace("-", "")
#     endpoint = f"{ENDPOINT_LIST_LOG_IDS}/{uid}"
#     response = requests.get(endpoint, headers=headers, timeout=TIMEOUT)
#     response.raise_for_status()
#     response_data = response.json()
#     out: list[LogInfo] = []
#     for item in response_data:
#         loginfo = LogInfo(**item)
#         out.append(loginfo)
#     return out


# def request_query_logs(api_admin_key: str, query: ClientLogQuery) -> list[LogInfo]:
#     """Test the query_logs endpoint."""
#     headers = {
#         "accept": "application/json",
#         "x-api-admin-key": api_admin_key,
#     }
#     response = requests.post(
#         ENDPOINT_QUERY_CLIENT_LOGS, headers=headers, json=query.dict(), timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     response_data = response.json()
#     out: list[LogInfo] = []
#     for item in response_data:
#         loginfo = LogInfo(**item)
#         out.append(loginfo)
#     return out


# def request_upload_log(client_token: str, log: str) -> str:
#     """Test the upload_log endpoint."""
#     headers = {
#         "accept": "application/json",
#         "x-client-token": client_token,
#     }
#     endpoint = f"{ENDPOINT_UPLOAD_LOG}"
#     response = requests.post(
#         endpoint, headers=headers, files={"log_str": (None, log)}, timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     response_data = response.text
#     return response_data


# def request_client_register(
#     client_api_key: str, uid: str, device_info: DeviceInfo | None = None
# ) -> str:
#     """Handles registering a client with the server."""
#     # Register the UID with the server
#     headers = {
#         "accept": "application/json",
#         "x-uid": uid,
#         "x-client-api-key": client_api_key,
#     }
#     body = None
#     if device_info is not None:
#         body = json.dumps(device_info.dict())
#     response = requests.post(
#         ENDPOINT_CLIENT_REGISTER, headers=headers, data=body, timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     response_data = response.json()
#     assert response_data.get("ok")
#     assert response_data.get("error") is None
#     token = response_data.get("token")
#     assert token, "Expected token to be returned"
#     return token


# def request_upload(token: str, vidpath: str, jsonpath: str) -> dict[str, Any]:
#     """Test the upload endpoint."""
#     assert os.path.exists(vidpath), f"Video file {vidpath} does not exist"
#     assert os.path.exists(jsonpath), f"JSON file {jsonpath} does not exist"
#     headers = {
#         "accept": "application/json",
#         "x-client-token": token,
#     }
#     json_fd = open(jsonpath, "rb")  # pylint: disable=consider-using-with
#     vid_fd = open(vidpath, "rb")  # pylint: disable=consider-using-with
#     try:
#         files = {
#             "metadata": (
#                 os.path.basename(jsonpath),
#                 json_fd,
#                 "application/json",
#             ),
#             "vidfile": (
#                 os.path.basename(vidpath),
#                 vid_fd,
#                 "video/mp4",
#             ),
#         }
#         response = requests.post(
#             ENDPOINT_UPLOAD, headers=headers, files=files, timeout=TIMEOUT
#         )
#         response.raise_for_status()
#         return response.json()
#     finally:
#         json_fd.close()
#         vid_fd.close()


# def request_report_crash(
#     token: str,
#     app_version: str,
#     device_api_version: str,
#     device_model: str,
#     device_make: str,
#     mode: str,
#     stack_trace: str | None,
#     crash_message: str,
#     thread_name: str,
#     crash_file: str,
#     crash_line: int,
# ) -> str:
#     """Test the report_crash endpoint."""
#     headers = {"x-client-token": token}

#     # Prepare the request payload
#     crash_report = {
#         "app_version": app_version,
#         "device_api_version": device_api_version,
#         "device_model": device_model,
#         "device_make": device_make,
#         "mode": mode,
#         "stack_trace": stack_trace,
#         "crash_message": crash_message,
#         "thread_name": thread_name,
#         "crash_file": crash_file,
#         "crash_line": crash_line,
#     }

#     response = requests.post(
#         ENDPOINT_REPORT_CRASH,
#         headers=headers,
#         json=crash_report,
#         timeout=TIMEOUT,
#     )
#     response.raise_for_status()
#     response_data = response.text
#     return response_data


# def request_download(api_admin_key: str, vid: int) -> bytes:
#     """Test the download endpoint."""
#     url = f"{ENDPOINT_DOWNLOAD_VIDEO}/{vid}"
#     headers = {"accept": "application/json", "x-api-admin-key": api_admin_key}
#     response = requests.get(url, headers=headers, timeout=TIMEOUT)
#     response.raise_for_status()
#     result = response.content
#     assert result, "Expected video to be returned"
#     return result


# def request_list_uploads(api_admin_key: str, uid: str) -> dict[str | int, Any]:
#     """Test the list_uploads endpoint."""
#     headers = {
#         "accept": "application/json",
#         "x-api-admin-key": api_admin_key,
#         "Content-Type": "application/json",
#     }
#     data = {
#         "uid": uid,
#         # TODO: Test these too.
#         # "start": "2023-04-18T21:18:32.232Z",
#         # "end": "2023-04-18T21:18:32.232Z",
#         # "appname": "*",
#         # "count": 100
#     }
#     response = requests.post(
#         ENDPOINT_LIST_UPLOADS, headers=headers, data=json.dumps(data), timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     result = response.json()
#     return result


# def request_client_settings(
#     token: str,
#     app_version: str,
#     device_api_version: str,
#     device_model: str,
#     device_make: str,
# ) -> dict[str, Any]:
#     """Tests the client_settings endpoint"""
#     headers = {
#         "accept": "application/json",
#         "x-client-token": token,
#     }
#     data = {
#         "appVersion": app_version,
#         "deviceApiVersion": device_api_version,
#         "deviceModel": device_model,
#         "deviceMake": device_make,
#     }
#     response = requests.post(
#         ENDPOINT_CLIENT_SETTINGS,
#         headers=headers,
#         data=json.dumps(data),
#         timeout=TIMEOUT,
#     )
#     response.raise_for_status()
#     result = response.json()
#     return result


# def request_apk_update(release_or_debug: str) -> dict[str, Any]:
#     """Tests the apk_update endpoint"""
#     assert release_or_debug in ("release", "debug")
#     endpoint = (
#         ENDPOINT_APK_UPDATE
#         if release_or_debug == "release"
#         else ENDPOINT_APK_UPDATE_DEBUG
#     )
#     headers = {
#         "accept": "application/json",
#     }
#     response = requests.get(endpoint, headers=headers, timeout=TIMEOUT)
#     response.raise_for_status()
#     result = response.json()
#     return result


# def request_query_stats(
#     api_admin_key: str, uids: list[str] | None
# ) -> list[dict[str, str | None]]:
#     """Tests the apk_update endpoint"""
#     headers = {
#         "accept": "application/json",
#         "x-api-admin-key": api_admin_key,
#         "Content-Type": "application/json",
#     }
#     data = {
#         "uids": uids,
#     }
#     response = requests.post(
#         ENDPOINT_QUERY_STATS, headers=headers, data=json.dumps(data), timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     result = response.json()
#     return result


# def request_db_clear(api_admin_key) -> None:
#     """Tests the apk_update endpoint"""
#     headers = {"x-api-admin-key": api_admin_key}
#     response = requests.delete(ENDPOINT_CLEAR, headers=headers, timeout=TIMEOUT)
#     response.raise_for_status()


# def request_query_users(api_admin_key, query: UserQuery) -> list[dict[str, str]]:
#     """Tests the apk_update endpoint"""
#     # do a post operation
#     headers = {
#         "accept": "application/json",
#         "x-api-admin-key": api_admin_key,
#         "Content-Type": "application/json",
#     }
#     json_query = query.json()
#     response = requests.post(
#         ENDPOINT_QUERY_USERS, headers=headers, data=json_query, timeout=TIMEOUT
#     )
#     response.raise_for_status()
#     result = response.json()
#     # assert result is list
#     assert isinstance(result, list)
#     return result
