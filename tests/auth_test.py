"""Unit tests for Sensorlinx login lifecycle, idempotency, and 401 retry.

These tests cover bug fixes for the "login times out and never recovers" failure
mode reported by users. See https://github.com/sslivins/pysensorlinx/issues for
context.
"""

import asyncio

import aiohttp
import pytest
from aioresponses import aioresponses

from pysensorlinx import (
    InvalidCredentialsError,
    LoginError,
    LoginTimeoutError,
    NoTokenError,
    Sensorlinx,
)
from pysensorlinx.sensorlinx import (
    BUILDINGS_ENDPOINT,
    DEVICES_ENDPOINT_TEMPLATE,
    HOST_URL,
    LOGIN_ENDPOINT,
    PROFILE_ENDPOINT,
)


LOGIN_URL = f"{HOST_URL}/{LOGIN_ENDPOINT}"
PROFILE_URL = f"{HOST_URL}/{PROFILE_ENDPOINT}"
BUILDINGS_URL = f"{HOST_URL}/{BUILDINGS_ENDPOINT}"
DEVICE_URL = f"{HOST_URL}/{DEVICES_ENDPOINT_TEMPLATE.format(building_id='b1')}/d1"


def _login_ok(m, token: str = "tok-1", refresh: str = "ref-1"):
    """Register a successful login response."""
    m.post(LOGIN_URL, status=200, payload={"token": token, "refresh": refresh})


# ---------------------------------------------------------------------------
# Lifecycle: login failures must leave the client in a clean, not-logged-in
# state. This is the regression behind "Login request timed out" / never
# recovers.
# ---------------------------------------------------------------------------


@pytest.mark.auth
async def test_login_timeout_leaves_client_not_logged_in():
    """A login that times out must not leave a half-initialized session.

    Repro for the bug: today login() assigns self._session BEFORE the POST,
    and the timeout handler doesn't tear it down. Subsequent data calls
    then check `if self._session is None` (false), skip relogin, and call
    the API unauthenticated forever.
    """
    sl = Sensorlinx()
    with aioresponses() as m:
        m.post(LOGIN_URL, exception=asyncio.TimeoutError())
        with pytest.raises(LoginTimeoutError):
            await sl.login("user@example.com", "pw")

    assert sl.is_logged_in is False
    assert sl._session is None
    assert sl._bearer_token is None


@pytest.mark.auth
async def test_login_invalid_credentials_propagate_typed_exception():
    """InvalidCredentialsError must NOT be re-wrapped as a generic LoginError.

    Today the `except Exception as e: raise LoginError(...)` block in login()
    swallows the typed auth exception, so HA can never distinguish bad
    creds from a network error. Without this the ConfigEntryAuthFailed
    path can't fire.
    """
    sl = Sensorlinx()
    with aioresponses() as m:
        m.post(LOGIN_URL, status=401, payload={"error": "bad creds"})
        with pytest.raises(InvalidCredentialsError):
            await sl.login("user@example.com", "pw")

    assert sl.is_logged_in is False
    assert sl._session is None


@pytest.mark.auth
async def test_login_no_token_propagates_typed_exception():
    """NoTokenError (200 OK with no token in body) must not be re-wrapped."""
    sl = Sensorlinx()
    with aioresponses() as m:
        m.post(LOGIN_URL, status=200, payload={"refresh": "x"})  # no 'token'
        with pytest.raises(NoTokenError):
            await sl.login("user@example.com", "pw")

    assert sl.is_logged_in is False
    assert sl._session is None


@pytest.mark.auth
async def test_login_unknown_5xx_raises_login_error_and_cleans_up():
    sl = Sensorlinx()
    with aioresponses() as m:
        m.post(LOGIN_URL, status=503, body="Service Unavailable")
        with pytest.raises(LoginError):
            await sl.login("user@example.com", "pw")

    assert sl.is_logged_in is False
    assert sl._session is None


# ---------------------------------------------------------------------------
# Idempotency: calling login() while already logged in is a no-op (no new
# session, no new POST).
# ---------------------------------------------------------------------------


@pytest.mark.auth
async def test_login_is_idempotent_when_already_logged_in():
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m)
        await sl.login("u", "p")
        first_session = sl._session
        first_token = sl._bearer_token
        # Second call must NOT POST again or replace the session.
        await sl.login()
        assert sl._session is first_session
        assert sl._bearer_token == first_token
    await sl.close()


@pytest.mark.auth
async def test_login_replaces_session_when_called_after_failure():
    """A relogin after a failure must close the prior session, not leak it."""
    sl = Sensorlinx()
    with aioresponses() as m:
        m.post(LOGIN_URL, exception=asyncio.TimeoutError())
        with pytest.raises(LoginTimeoutError):
            await sl.login("u", "p")
        assert sl._session is None  # cleaned up

        _login_ok(m)
        await sl.login()  # uses cached creds
        assert sl.is_logged_in is True
    await sl.close()


# ---------------------------------------------------------------------------
# 401 auto-retry: after a token expires mid-day, the very next call must
# self-heal by reauthenticating once and retrying. This is what removes
# the need for the HA integration to call login() every cycle.
# ---------------------------------------------------------------------------


@pytest.mark.auth
async def test_data_call_retries_once_on_401_and_succeeds():
    sl = Sensorlinx()
    with aioresponses() as m:
        # Initial login.
        _login_ok(m, token="old-tok")
        # First profile call returns 401 (token expired).
        m.get(PROFILE_URL, status=401)
        # Library reauths with cached creds.
        _login_ok(m, token="new-tok")
        # Retry succeeds.
        m.get(PROFILE_URL, status=200, payload={"id": "u1"})

        await sl.login("u", "p")
        result = await sl.get_profile()

    assert result == {"id": "u1"}
    assert sl._bearer_token == "new-tok"
    await sl.close()


@pytest.mark.auth
async def test_data_call_two_consecutive_401s_raises_invalid_creds():
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m, token="old-tok")
        m.get(PROFILE_URL, status=401)
        # Reauth attempt itself returns 401 (creds rotated).
        m.post(LOGIN_URL, status=401)

        await sl.login("u", "p")
        with pytest.raises(InvalidCredentialsError):
            await sl.get_profile()

    assert sl.is_logged_in is False
    await sl.close()


# ---------------------------------------------------------------------------
# Recovery: a data call after a prior login failure must self-heal on the
# next cycle. Mirrors the user's exact failure mode.
# ---------------------------------------------------------------------------


@pytest.mark.auth
async def test_data_call_recovers_after_prior_login_timeout():
    sl = Sensorlinx()
    with aioresponses() as m:
        # Cycle 1: login times out.
        m.post(LOGIN_URL, exception=asyncio.TimeoutError())
        with pytest.raises(LoginTimeoutError):
            await sl.login("u", "p")

        # Cycle 2: HA polls again. With the fix, `is_logged_in` is False,
        # so HA calls login() and it succeeds, then get_buildings() works.
        _login_ok(m)
        m.get(BUILDINGS_URL, status=200, payload=[{"id": "b1"}])

        assert sl.is_logged_in is False
        await sl.login()  # cached creds
        result = await sl.get_buildings()

    assert result == [{"id": "b1"}]
    await sl.close()


@pytest.mark.auth
async def test_close_clears_cached_credentials():
    """close() is an explicit shutdown — must clear creds too, not just session."""
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m)
        await sl.login("u", "p")

    await sl.close()
    assert sl._username is None
    assert sl._password is None
    assert sl._bearer_token is None
    assert sl._session is None


@pytest.mark.auth
async def test_cleanup_on_failure_preserves_cached_credentials():
    """A transient cleanup must NOT wipe creds — auto-relogin needs them."""
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m)
        await sl.login("u", "p")
        # Now simulate a 401 leading to a cleanup+relogin attempt that fails.
        m.get(PROFILE_URL, status=401)
        m.post(LOGIN_URL, exception=asyncio.TimeoutError())
        with pytest.raises((LoginTimeoutError, LoginError)):
            await sl.get_profile()

    assert sl.is_logged_in is False
    # But cached creds remain so a future cycle can recover.
    assert sl._username == "u"
    assert sl._password == "p"
    await sl.close()


# ---------------------------------------------------------------------------
# Concurrency: two coroutines racing to login() must not both POST.
# ---------------------------------------------------------------------------


@pytest.mark.auth
async def test_concurrent_logins_are_serialized():
    sl = Sensorlinx()
    with aioresponses() as m:
        # Register exactly ONE successful login; if the lock works, only
        # one POST happens. Without the lock, the second concurrent call
        # would hit aioresponses with no registered mock and 4xx/raise.
        _login_ok(m)

        await asyncio.gather(sl.login("u", "p"), sl.login("u", "p"))

    assert sl.is_logged_in is True
    await sl.close()


# ---------------------------------------------------------------------------
# Gap coverage: behaviors introduced by the refactor that weren't yet
# directly exercised by the lifecycle/idempotency tests above.
# ---------------------------------------------------------------------------


@pytest.mark.auth
async def test_is_logged_in_false_when_session_closed():
    """is_logged_in must reflect aiohttp's own close state, not just bearer presence.

    aiohttp can self-close a session on certain transport errors; if we only
    checked the bearer token we'd think we were still logged in and fire
    requests through a dead session.
    """
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m)
        await sl.login("u", "p")
        assert sl.is_logged_in is True
        await sl._session.close()  # simulate aiohttp self-closing
        assert sl.is_logged_in is False
    await sl.close()


@pytest.mark.auth
async def test_is_logged_in_false_after_close():
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m)
        await sl.login("u", "p")
    await sl.close()
    assert sl.is_logged_in is False


@pytest.mark.auth
async def test_login_with_new_credentials_replaces_cached_creds():
    """login("new","creds") while already logged in must NOT take the idempotent
    fast-path — the user is rotating credentials and expects a fresh login."""
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m, token="tok-old")
        await sl.login("old-user", "old-pass")
        first_session = sl._session

        m.post(LOGIN_URL, status=200, payload={"token": "tok-new", "refresh": "r2"})
        await sl.login("new-user", "new-pass")

    assert sl._username == "new-user"
    assert sl._password == "new-pass"
    assert sl._bearer_token == "tok-new"
    # Old session must be closed so we don't leak it.
    assert first_session.closed is True
    assert sl._session is not first_session
    await sl.close()


@pytest.mark.auth
async def test_login_idempotent_when_called_with_same_credentials():
    """Re-logging-in with the exact same creds while already authenticated
    is a no-op (avoids gratuitous POSTs from defensive callers)."""
    sl = Sensorlinx()
    with aioresponses() as m:
        # Register only one successful login. If idempotency works the
        # second login() call won't try to POST again.
        _login_ok(m, token="tok-1")
        await sl.login("u", "p")
        await sl.login("u", "p")  # would raise ConnectionError without no-op
        assert sl._bearer_token == "tok-1"
    await sl.close()


@pytest.mark.auth
async def test_set_device_parameter_retries_once_on_401():
    """The 401 auto-retry must work for writes (PATCH), not just reads.

    set_device_parameter is the one transport-level write — its retry path
    is identical to GET because the body is deterministic and idempotent.
    """
    sl = Sensorlinx()
    from pysensorlinx import SensorlinxDevice
    device = SensorlinxDevice(sl, "b1", "d1")

    with aioresponses() as m:
        _login_ok(m, token="tok-stale")
        await sl.login("u", "p")

        # First PATCH gets stale-token 401, then relogin, then succeeds.
        m.patch(DEVICE_URL, status=401, body="token expired")
        m.post(LOGIN_URL, status=200, payload={"token": "tok-fresh", "refresh": "r"})
        m.patch(DEVICE_URL, status=200, payload={"ok": True})

        # permanent_hd is the simplest boolean param; one parameter is enough.
        await sl.set_device_parameter("b1", "d1", permanent_hd=True)

    assert sl._bearer_token == "tok-fresh"
    await sl.close()


@pytest.mark.auth
async def test_authorization_header_is_refreshed_after_relogin():
    """After a 401 → relogin, the retried request must carry the NEW bearer.

    Regression guard: the old auth header must not survive into the retry.
    aioresponses doesn't surface request headers easily, so we assert via
    the bearer state seen by subsequent calls.
    """
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m, token="tok-old")
        await sl.login("u", "p")
        assert sl.headers["Authorization"] == "Bearer tok-old"

        m.get(PROFILE_URL, status=401)
        m.post(LOGIN_URL, status=200, payload={"token": "tok-new", "refresh": "r"})
        m.get(PROFILE_URL, status=200, payload={"id": 1})
        await sl.get_profile()

        assert sl.headers["Authorization"] == "Bearer tok-new"
        assert sl._bearer_token == "tok-new"
    await sl.close()


@pytest.mark.auth
async def test_data_call_does_not_retry_on_500():
    """Non-401 server errors must surface immediately, not trigger relogin.

    Re-authenticating in response to a 5xx would mask backend outages and
    spam the auth endpoint. Only definite 401s reauth.

    get_profile() catches non-LoginError exceptions and returns None,
    so a successful "no retry" outcome here is: result is None and
    only one login POST was registered (not consumed twice).
    """
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m)
        await sl.login("u", "p")

        m.get(PROFILE_URL, status=500, body="internal error")
        # Only one login POST was registered; if relogin had been
        # attempted on 500 it would raise ConnectionError as a second
        # POST has no mock — so the *absence* of that error proves the
        # 500 path didn't reauth.
        result = await sl.get_profile()
        assert result is None
        assert sl.is_logged_in is True  # still logged in; no churn
    await sl.close()


@pytest.mark.auth
async def test_data_call_does_not_relogin_on_connection_error():
    """Connection errors must not trigger relogin (semantics ambiguous for writes,
    and pointless for reads — auth wasn't the problem)."""
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m)
        await sl.login("u", "p")

        m.get(
            PROFILE_URL,
            exception=aiohttp.ClientConnectionError("network down"),
        )
        # No second POST registered: if we tried to relogin on conn error,
        # this would raise ConnectionRefused as a different error.
        result = await sl.get_profile()
        # get_profile catches non-LoginError exceptions and returns None.
        assert result is None
    await sl.close()


@pytest.mark.auth
async def test_close_is_safe_when_never_logged_in():
    """Defensive: HA may call close() during teardown even if login never ran."""
    sl = Sensorlinx()
    await sl.close()  # must not raise
    assert sl.is_logged_in is False


@pytest.mark.auth
async def test_close_is_idempotent():
    sl = Sensorlinx()
    with aioresponses() as m:
        _login_ok(m)
        await sl.login("u", "p")
    await sl.close()
    await sl.close()  # second close must not raise
    assert sl.is_logged_in is False


@pytest.mark.auth
async def test_concurrent_data_calls_login_only_once():
    """Two coroutines racing to make data calls when not logged in must
    share a single login POST, not stampede the auth endpoint."""
    sl = Sensorlinx()
    with aioresponses() as m:
        # Register exactly ONE login + two profile responses. If the lock
        # works, both calls share the single login.
        _login_ok(m)
        m.get(PROFILE_URL, status=200, payload={"id": 1})
        m.get(PROFILE_URL, status=200, payload={"id": 1})

        # Pre-cache creds so login(no-args) inside _authenticated_request works.
        sl._username = "u"
        sl._password = "p"

        results = await asyncio.gather(sl.get_profile(), sl.get_profile())

    assert all(r == {"id": 1} for r in results)
    assert sl._bearer_token == "tok-1"
    await sl.close()


@pytest.mark.auth
async def test_consecutive_failed_logins_do_not_leak_sessions():
    """A storm of failed logins must not pile up unclosed ClientSessions.

    Regression guard for the original bug where every login() created a
    fresh session without closing the prior one.
    """
    sl = Sensorlinx()
    sessions = []

    with aioresponses() as m:
        for _ in range(3):
            m.post(LOGIN_URL, exception=asyncio.TimeoutError())

        for _ in range(3):
            with pytest.raises(LoginTimeoutError):
                await sl.login("u", "p")
            # _cleanup_session nulls _session, so we can only sample what
            # is_logged_in says. The strong invariant: after each failure,
            # session is None (closed and dropped).
            assert sl._session is None
            assert sl.is_logged_in is False

    await sl.close()
