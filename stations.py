#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
everything important about the several Callisto stations

:authors: 	Lukas Höfig
:contact: 	lukas.hoefig@edu.uni-graz.at
:date:       27.09.2022
"""


from typing import List
from astropy.io import fits
import urllib
from bs4 import BeautifulSoup
import os

import config

e_callisto_url = config.e_callisto_url

# station_dict = {}
# station_list = []
#
# # TODO -> keep dict?


class Station:
    """
    """

    def __init__(self, name: str, focus_code=None, longitude=None, latitude=None, spectral_range=None):
        """
        :param name: ID of the Observatory
        :param spectral_range: dict{"ID", [spectral, range]}
        """
        self.name = name
        self.focus_code = focus_code
        self.longitude = longitude
        self.latitude = latitude
        self.spectral_range = spectral_range
        if focus_code is not None:
            name = self.name + self.focus_code
        else:
            name = self.name
        # station_list.append(name)
        # station_dict[name] = self

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return id(hash(self.name))

    def obsTime(self):
        """
        sun zenith by latitude
        """
        return (12 - (self.longitude + 360) / 360 * 24) % 24


class StationSet:
    """
    TODO could be a single function
    """
    def __init__(self, stations: List[Station]):
        self.stations = stations

    def getSet(self):
        sets = []
        for station1 in range(len(self.stations)):
            for station2 in range(station1 + 1, len(self.stations)):
                sets.append([self.stations[station1], self.stations[station2]])
        return sets


def stationRange(station_list: List):
    set_ = StationSet(station_list)
    return set_.getSet()

# def getStationFromStr(name: str) -> Station:
#     return station_dict[name]


def getFocusCode(*date, station: str):
    """
    gets the first valid focus code for the frq band 
    """
    date_ = config.getDateFromArgs(*date)

    files = os.listdir(config.pathDataDay(date_))
    files_station = [i for i in files if i.startswith(station + "_")]
    for i in files_station:
        file = fits.open(config.pathDataDay(date_) + i)
        frq_axis = file[1].data['frequency'].flatten()
        frq = sorted([frq_axis[0], frq_axis[-1]])
        if config.frq_limit_low_upper > frq[0] > config.frq_limit_low_lower and \
                config.frq_limit_high_upper > frq[1] > config.frq_limit_high_lower:
            return i.rsplit("_")[-1].rstrip(".fit.gz")
    raise ValueError("No valid focus code for that day")


def listFilesDay(url: str):
    """
    :param url: full url incl the day
    """
    page = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(page, 'html.parser')
    return [node.get('href') for node in soup.find_all('a') if node.get('href').endswith(config.file_type_zip)]


def listFD(url: str, station: List[str]):
    """
    :param url: full url incl the day
    :param station: [name, focus-code]
    """
    page = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(page, 'html.parser')

    return [url + '/' + node.get('href') for node in soup.find_all('a')
            if node.get('href').startswith(station[0]) and node.get('href').endswith(station[1] + config.file_type_zip)]


def getStations(*date):
    date_ = config.getDateFromArgs(*date)

    date_str = "{:%Y/%m/%d}".format(date_)
    files = listFilesDay(e_callisto_url + date_str)
    stations = []
    stations_return = []
    for i in files:
        parts = i.rsplit("_")
        stations.append([parts[0], parts[3][:2]])
    stations_clean = []
    for i in stations:
        if i not in stations_clean:
            stations_clean.append(i)
    for i in stations_clean:
        name = i[0]
        focus_code = i[1]
        for a, b in enumerate(listFD(e_callisto_url + date_str, i)):
            with fits.open(b) as fds:
                try: 
                    lat = fds[0].header['OBS_LAT']
                    lac = fds[0].header['OBS_LAC']
                    if lac == 'S':
                        lat = -lat
                    lon = fds[0].header['OBS_LON']
                    loc = fds[0].header['OBS_LOC']
                    if loc == 'W':
                        lon = -lon
                    frq_axis = fds[1].data['frequency'].flatten()
                    frq = sorted([frq_axis[0], frq_axis[-1]])
                    if config.frq_limit_low_upper > frq[0] > config.frq_limit_low_lower and \
                            config.frq_limit_high_upper > frq[1] > config.frq_limit_high_lower:
                        station = Station(name, focus_code, lon, lat, frq)
                        stations_return.append(station)
                except IndexError:
                    print("Could not read fits file of ", b)
                break
    return stations_return


def getStationFromFile(file: str):
    name = file.rsplit("/")[-1].rsplit("_")[0]
    focus_code = file.rsplit("/")[-1].rsplit("_")[-1].rstrip(".fit.gz")
    try:
        with fits.open(file) as fds:
            lat = fds[0].header['OBS_LAT']
            lac = fds[0].header['OBS_LAC']
            if lac == 'S':
                lat = -lat
            lon = fds[0].header['OBS_LON']
            loc = fds[0].header['OBS_LOC']
            if loc == 'W':
                lon = -lon
            frq_axis = fds[1].data["frequency"].flatten()
            frq = sorted([frq_axis[0], frq_axis[-1]])
            if config.frq_limit_low_upper > frq[0] > config.frq_limit_low_lower and \
                    config.frq_limit_high_upper  > frq[1] > config.frq_limit_high_lower:
                return Station(name, focus_code, lon, lat, frq)
            raise AttributeError("Station in file has wrong frequency range.")
    except IndexError:
        print(f"failed to open {file}")
        return Station(name, focus_code=focus_code)
