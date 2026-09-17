"""Helpers that keep benchmark calls valid across Stingray versions.

Features are detected from call signatures, never from version numbers.
Old Stingray classes often accept ``**kwargs`` and only *warn* about unknown
keywords; passing them anyway adds the warning cost to the timing, so we pass
a keyword only when the installed version declares it.
"""

import inspect
from functools import lru_cache


@lru_cache(maxsize=None)
def accepts(func, name):
    """Return True if ``func`` declares a parameter called ``name``."""
    try:
        return name in inspect.signature(func).parameters
    except (TypeError, ValueError):
        return False


def supported_kwargs(func, **kwargs):
    """Filter ``kwargs`` down to those declared by ``func``."""
    return {key: val for key, val in kwargs.items() if accepts(func, key)}


def make_eventlist(times, gti=None, skip_checks=False):
    """Create an EventList; ``skip_checks`` is ignored before Stingray v2.0."""
    from stingray.events import EventList

    kwargs = supported_kwargs(EventList.__init__, skip_checks=skip_checks)
    return EventList(times, gti=gti, **kwargs)


def make_lightcurve(times, counts, dt, gti=None, skip_checks=False):
    """Create a Lightcurve; ``skip_checks`` is ignored where unsupported."""
    from stingray.lightcurve import Lightcurve

    kwargs = supported_kwargs(Lightcurve.__init__, skip_checks=skip_checks)
    return Lightcurve(times, counts, dt=dt, gti=gti, **kwargs)


def averaged_spectrum_from_events(cls, *events, dt, segment_size, **kwargs):
    """Build an averaged power or cross spectrum from event lists.

    Stingray v0.1 spectra accept only light curves (no ``dt`` argument); there
    we emulate the user's route of binning the events first, so the binning
    time is included in the timing, as it is inside newer versions.
    """
    if accepts(cls.__init__, "dt"):
        return cls(*events, dt=dt, segment_size=segment_size, **kwargs)
    light_curves = [ev.to_lc(dt) for ev in events]
    return cls(*light_curves, segment_size=segment_size, **kwargs)
