# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.

import numpy as np
import stingray
import stingray.events
import stingray.lightcurve
import stingray.powerspectrum
import stingray.crossspectrum
import types


class PowerspectrumSuite:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """

    def setup_cache(self):
        data = types.SimpleNamespace()
        data.gti = np.array([[0, 3000]])
        data.times0 = np.sort(
            np.random.uniform(data.gti[0, 0], data.gti[-1, 1], 1_000_000)
        )
        data.times1 = np.sort(
            np.random.uniform(data.gti[0, 0], data.gti[-1, 1], 1_000_000)
        )
        data.times = np.sort(np.concatenate([data.times0, data.times1]))
        data.dt = 0.001
        data.segment_size = 3
        data.events0 = stingray.events.EventList(data.times0, gti=data.gti)
        data.events1 = stingray.events.EventList(data.times1, gti=data.gti)
        data.lc0 = data.events0.to_lc(dt=data.dt)
        data.lc1 = data.events1.to_lc(dt=data.dt)

        data.events = stingray.events.EventList(data.times, gti=data.gti)
        data.lc = data.events.to_lc(dt=data.dt)
        return data

    def time_powerspectrum_from_events(self, data):
        stingray.powerspectrum.AveragedPowerspectrum(
            data.events, dt=data.dt, segment_size=data.segment_size
        )

    def time_crossspectrum_from_events(self, data):
        stingray.crossspectrum.AveragedCrossspectrum(
            data.events0,
            data.events1,
            dt=data.dt,
            gti=data.gti,
            segment_size=data.segment_size,
        )

    def time_powerspectrum_from_lc(self, data):
        stingray.powerspectrum.AveragedPowerspectrum(
            data.lc, segment_size=data.segment_size
        )

    def time_crossspectrum_from_lc(self, data):
        stingray.crossspectrum.AveragedCrossspectrum(
            data.lc0, data.lc1, segment_size=data.segment_size
        )
