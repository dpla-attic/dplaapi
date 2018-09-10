import pytest
import requests
import logging
from apistar.http import Request
from dplaapi import analytics


@pytest.fixture(scope='function')
def stub_requests_post(monkeypatch, mocker):
    stub = mocker.stub(name='requests_post_stub')
    monkeypatch.setattr(requests, 'post', stub)


def tracker():
    results = {
        'docs': [
            {
                'id': 'a1b2',
                'provider': {'name': 'Partner X'},
                'dataProvider': 'Library of X',
                'sourceResource': {'title': 'Document One'}
            },
            {
                'id': 'c3d4',
                'provider': {'name': 'Partner X'},
                'dataProvider': 'Library of Y',
                'sourceResource': {'title': 'Document Two'}
            }
        ]
    }

    return analytics.GATracker('x',
                               Request(method='GET',
                                       url='http://example.org/'),
                               results,
                               'a1b2c3',
                               'The Title')


class MockGoogleErrorResponse():
    def raise_for_status(self):
        raise requests.exceptions.HTTPError('Bad Things')


def mock_failing_ga_post(*args, **kwargs):
    return MockGoogleErrorResponse()


def test_GATracker_run_just_calls_other_functions(monkeypatch, mocker):
    pv_stub = mocker.stub(name='track_pageview')
    monkeypatch.setattr(analytics.GATracker, 'track_pageview', pv_stub)
    ev_stub = mocker.stub(name='track_events')
    monkeypatch.setattr(analytics.GATracker, 'track_events', ev_stub)

    rv = tracker().run()
    pv_stub.assert_called_once()
    ev_stub.assert_called_once()
    assert rv == None  # noqa: E177


def test_GATracker_constructs_correct_pageview_data(monkeypatch, mocker):
    post_stub = mocker.stub()
    monkeypatch.setattr(analytics, 'post', post_stub)
    # [('t', 'pageview'), ('dh', 'example.org'), ('dp', '/?'),
    #  ('dt', 'The Title'), ('cid', 'a1b2c3')]
    body = "t=pageview&dh=example.org&dp=%2F%3F&dt=The+Title&cid=a1b2c3" \
           "&v=1&tid=x"
    tracker().track_pageview()
    post_stub.assert_called_once_with(
        'https://www.google-analytics.com/collect', body)


def test_GATracker_constructs_correct_event_data(monkeypatch, mocker):
    post_stub = mocker.stub()
    monkeypatch.setattr(analytics, 'post', post_stub)
    # [('t', 'event'),
    #  ('ec', 'View API Item : Partner X'),
    #  ('ea', 'Library of X'),
    #  ('el', 'a1b2 : Document One'),
    #  ('dh', 'example.org'), ('dp', '/?')]
    # [('t', 'event'),
    #  ('ec', 'View API Item : Partner X'),
    #  ('ea', 'Library of Y'),
    #  ('el', 'c3d4 : Document Two'),
    #  ('dh', 'example.org'), ('dp', '/?')]
    body = "t=event&ec=View+API+Item+%3A+Partner+X&ea=Library+of+X&" \
           "el=a1b2+%3A+Document+One&dh=example.org&dp=%2F%3F&v=1&tid=x\n" \
           "t=event&ec=View+API+Item+%3A+Partner+X&ea=Library+of+Y&" \
           "el=c3d4+%3A+Document+Two&dh=example.org&dp=%2F%3F&v=1&tid=x"
    tracker().track_events()
    post_stub.assert_called_once_with(
        'http://www.google-analytics.com/batch', body)


def test_post_logs_exception(monkeypatch, mocker):
    monkeypatch.setattr(requests, 'post', mock_failing_ga_post)
    mocker.spy(logging.Logger, 'exception')
    with pytest.raises(Exception):
        analytics.post('https://example.org', 'x')
        logging.Logger.exception.assert_called_once_with(
            'Failed to post to Google Analytics')


def test_comma_del_string_with_string():
    assert analytics.comma_del_string('x') == 'x'


def test_comma_del_string_with_list():
    assert analytics.comma_del_string(['x', 'y']) == 'x, y'


def test_track(monkeypatch, mocker):
    monkeypatch.setenv('GA_TID', 'the_tid')
    mocker.spy(analytics.GATracker, '__init__')
    start_stub = mocker.stub(name='start')
    monkeypatch.setattr(analytics.GATracker, 'start', start_stub)
    req = Request(method='GET', url='https://example.org/')

    analytics.track(req, {}, 'x', 'title')
    analytics.GATracker.__init__.assert_called_once_with(
        mocker.ANY, 'the_tid', req, {}, 'x', 'title')
    analytics.GATracker.start.assert_called_once()
