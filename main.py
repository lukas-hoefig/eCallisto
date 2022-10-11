#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import timedelta
import copy
import numpy as np
import sys
import warnings

import download
import stations
import analysis
import events
import data
import correlation
import const


def run1stSearch(*date, days=1, mask_frq=False, nobg=True, bin_f=False, bin_t=False,
                 flatten=True, bin_t_w=4, flatten_w=400, r_w=180):
    date_start = const.getDateFromArgs(*date)
    limit = 0.6
    time_step = timedelta(days=1)

    events_day = []
    for i in range(days):
        date_ = date_start + time_step * i
        observatories = stations.getStations(date_)
        download.downloadFullDay(date_, station=observatories)
        sets = []
        for j in observatories:
            sets.extend(data.listDataPointDay(date_, station=j))
        e_list = events.EventList([], date_)
        for set1 in range(len(sets)):
            for set2 in range(set1 + 1, len(sets)):
                data1_raw = copy.deepcopy(sets[set1])
                data2_raw = copy.deepcopy(sets[set2])
                data1, data2 = data.fitTimeFrameDataSample(data1_raw, data2_raw)

                if data1 and data2:
                    if mask_frq:
                        mask1 = analysis.maskBadFrequencies(data1)
                        mask2 = analysis.maskBadFrequencies(data2)
                        data1.spectrum_data.data[mask1] = np.nanmean(data1.spectrum_data.data)
                        data2.spectrum_data.data[mask2] = np.nanmean(data2.spectrum_data.data)
                    corr = correlation.Correlation(data1, data2, date_.day, no_background=nobg, bin_freq=bin_f,
                                                   bin_time=bin_t, flatten=flatten, bin_time_width=bin_t_w,
                                                   flatten_window=flatten_w, r_window=r_w)
                    corr.calculatePeaks(limit=limit)
                    try:
                        event_peaks = analysis.peaksInData(data1, data2)
                        for peak in corr.peaks:
                            if peak.inList(event_peaks):
                                e_list += peak
                    except AttributeError:
                        pass
                else:
                    pass
        try:
            e_list.sort()
        except AttributeError:
            # empty list
            pass
        events_day.append(e_list)
        analysis.saveData(date_, event_list=e_list, step=1)
    return events_day


def run2ndSearch(*date, mask_freq=True, no_bg=True, bin_f=False, bin_t=True, flatten=True, bin_t_w=None, flatten_w=None,
                 r_w=30):
    date_ = const.getDateFromArgs(*date)
    events_day = analysis.loadData(date_, step=1)
    e_list = events.EventList([], date_)
    limit = 0.8

    for event in events_day:
        obs = stations.StationSet(event.stations)
        set_obs = obs.getSet()
        for i in set_obs:
            try:
                dp1_peak = data.createFromTime(event.time_start, station=i[0], extent=False)
                dp2_peak = data.createFromTime(event.time_start, station=i[1], extent=False)
                dp1_peak.createSummedCurve()
                dp2_peak.createSummedCurve()
                dp1_peak.flattenSummedCurve()
                dp2_peak.flattenSummedCurve()
                event_peaks = analysis.peaksInData(dp1_peak, dp2_peak)
                if not event.inList(event_peaks):
                    pass
                else:
                    dp1, dp2, cor = analysis.calcPoint(event.time_start, obs1=i[0], obs2=i[1], mask_frq=mask_freq,
                                                       r_window=r_w,
                                                       flatten=flatten, bin_time=bin_t, bin_freq=bin_f, no_bg=no_bg,
                                                       flatten_window=bin_t_w, bin_time_width=flatten_w, limit=limit)
                    for peak in cor.peaks:
                        if peak.inList(event_peaks):
                            e_list += peak
                        else:
                            pass
            except FileNotFoundError:
                warnings.warn(message="Some file not found", category=UserWarning)

    analysis.saveData(date_, event_list=e_list, step=2)
    return e_list


if __name__ == '__main__':
    input_arg = sys.argv
    args = [2022, 1, 1, 1]
    if input_arg and len(input_arg) > 2:
        for i, j in enumerate(input_arg[1:]):
            args[i] = int(j)
    run1stSearch(*args[:-1], days=args[-1], mask_frq=True)
    for i in range(args[-2], args[-2] + args[-1]):
        run2ndSearch(args[:-2], i)
