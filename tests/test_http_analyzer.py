"""Unit test for modules/http_analyzer/http_analyzer.py"""
from ..modules.http_analyzer.http_analyzer import Module
import configparser

# dummy params used for testing
profileid = 'profile_192.168.1.1'
twid = 'timewindow1'
uid = 'CAeDWs37BipkfP21u8'
timestamp = 1635765895.037696


def do_nothing(*args):
    """Used to override the print function because using the self.print causes broken pipes"""
    pass


def create_http_analyzer_instance(outputQueue):
    """Create an instance of http_analyzer.py
    needed by every other test in this file"""
    config = configparser.ConfigParser()
    http_analyzer = Module(outputQueue, config, 6380)
    # override the self.print function to avoid broken pipes
    http_analyzer.print = do_nothing
    return http_analyzer


def test_check_suspicious_user_agents(outputQueue, database):
    http_analyzer = create_http_analyzer_instance(outputQueue)
    # create a flow with suspicious user agent
    host = '147.32.80.7'
    uri = '/wpad.dat'
    user_agent = 'CHM_MSDN'
    assert (
        http_analyzer.check_suspicious_user_agents(
            uid, host, uri, timestamp, user_agent, profileid, twid
        )
        == True
    )


def test_check_multiple_google_connections(outputQueue, database):
    http_analyzer = create_http_analyzer_instance(outputQueue)
    # {"ts":1635765765.435485,"uid":"C7mv0u4M1zqJBHydgj",
    # "id.orig_h":"192.168.1.28","id.orig_p":52102,"id.resp_h":"216.58.198.78",
    # "id.resp_p":80,"trans_depth":1,"method":"GET","host":"google.com","uri":"/",
    # "version":"1.1","user_agent":"Wget/1.20.3 (linux-gnu)","request_body_len":0,"response_body_len":219,
    # "status_code":301,"status_msg":"Moved Permanently","tags":[],"resp_fuids":["FGhwTU1OdvlfLrzBKc"],
    # "resp_mime_types":["text/html"]}
    host = 'google.com'
    # uri = '/'
    request_body_len = 0
    for i in range(4):
        found_detection = http_analyzer.check_multiple_empty_connections(
            uid, host, timestamp, request_body_len, profileid, twid
        )
    assert found_detection == True


def test_check_incompatible_user_agent(outputQueue, database):
    """
    tests get_user_agent_info and check_incompatible_user_agent
    """
    http_analyzer = create_http_analyzer_instance(outputQueue)
    # set the mac vendor
    safari_ua = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) '
        'Version/15.3 Safari/605.1.15'
    )
    # add os_type , os_name and agent_name to the db
    http_analyzer.get_user_agent_info(safari_ua, profileid)

    intel_oui = '00:13:20'
    MAC_info = {'Vendor': 'Intel Corp', 'MAC': 'FF:FF:FF' + intel_oui}
    database.add_mac_addr_to_profile(profileid, MAC_info)

    assert (
        http_analyzer.check_incompatible_user_agent(
            'google.com', '/images', timestamp, profileid, twid, uid
        )
        == True
    )


def test_extract_info_from_UA(outputQueue):
    http_analyzer = create_http_analyzer_instance(outputQueue)
    # use another profile, because the default
    # one already has a ua in the db
    profileid = 'profile_192.168.1.2'
    server_bag_ua = 'server-bag[macOS,11.5.1,20G80,MacBookAir10,1]'
    assert (
        http_analyzer.extract_info_from_UA(server_bag_ua, profileid)
        == '{"user_agent": "macOS,11.5.1,20G80,MacBookAir10,1", "os_name": "macOS", "os_type": "macOS11.5.1", "browser": ""}'
    )


def test_check_multiple_UAs(outputQueue):
    http_analyzer = create_http_analyzer_instance(outputQueue)
    safari_ua = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) '
        'Version/15.3 Safari/605.1.15'
    )
    mozilla_ua = 'Mozilla/5.0 (X11; Fedora;Linux x86; rv:60.0) Gecko/20100101 Firefox/60.0'

    # old ua
    cached_ua = {'os_type': 'Fedora', 'os_name': 'Linux'}
    # current ua
    user_agent = mozilla_ua
    # should set evidence
    assert (
        http_analyzer.check_multiple_UAs(
            cached_ua, user_agent, timestamp, profileid, twid, uid
        )
        == False
    )
    # in this case we should alert
    user_agent = safari_ua
    assert (
        http_analyzer.check_multiple_UAs(
            cached_ua, user_agent, timestamp, profileid, twid, uid
        )
        == True
    )