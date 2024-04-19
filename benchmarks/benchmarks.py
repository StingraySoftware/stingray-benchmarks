# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.

import numpy as np
import stingray
import stingray.events
import stingray.lightcurve
import stingray.powerspectrum
import stingray.crossspectrum
import types


class NonUniformSuite:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """

    def setup_cache(self):
        data = types.SimpleNamespace()
        data.gti = np.array([[0, 1000]])
        data.times_unsorted = np.random.uniform(
            data.gti[0, 0], data.gti[-1, 1], 10000000
        )

        data.times = np.sort(data.times_unsorted)
        return data

    def time_eventlist_creation_no_checks(self, data):
        stingray.events.EventList(data.times, gti=data.gti, skip_checks=True)

    def time_eventlist_creation_with_checks(self, data):
        stingray.events.EventList(data.times, gti=data.gti)

    def time_lightcurve_creation_from_times(self, data):
        stingray.lightcurve.Lightcurve.make_lightcurve(data.times, dt=1, gti=data.gti)

    def time_lightcurve_creation_from_times_no_gti(self, data):
        stingray.lightcurve.Lightcurve.make_lightcurve(data.times, dt=1)


class UniformSuite:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """

    def setup_cache(self):
        data = types.SimpleNamespace()
        data.gti = np.array([[0, 1000]])
        data.dt = 0.00003
        data.times = np.arange(data.gti[0, 0], data.gti[-1, 1], data.dt)
        data.counts = np.random.poisson(100, size=data.times.size)
        return data

    def time_lightcurve_creation_with_checks(self, data):
        stingray.lightcurve.Lightcurve(data.times, data.counts)

    def time_lightcurve_creation_no_checks(self, data):
        stingray.lightcurve.Lightcurve(
            data.times, data.counts, dt=data.dt, skip_checks=True, gti=data.gti
        )


class PowerspectrumSuite:
    """
    An example benchmark that times the performance of various kinds
    of iterating over dictionaries in Python.
    """

    def setup_cache(self):
        data = types.SimpleNamespace()
        data.gti = np.array([[0, 1000]])
        data.times0 = np.sort(
            np.random.uniform(data.gti[0, 0], data.gti[-1, 1], 10000000)
        )
        data.times1 = np.sort(
            np.random.uniform(data.gti[0, 0], data.gti[-1, 1], 10000000)
        )
        data.times = np.sort(np.concatenate([data.times0, data.times1]))
        data.dt = 0.1
        data.segment_size = 100
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
