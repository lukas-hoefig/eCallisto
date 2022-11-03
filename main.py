#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, datetime

import steps


if __name__ == '__main__':
    """
    args: year month day #days 
    """
    input_arg = sys.argv
    args = [2022, 1, 1, 1]
    if input_arg and len(input_arg) > 2:
        for i, j in enumerate(input_arg[1:]):
            args[i] = int(j)
    
    date_start = datetime.datetime(args[0], args[1], args[2])

    for i in range(0, args[3]):
        date = date_start + datetime.timedelta(days=i)
        steps.run1stSearch(date, mask_frq=True)
        steps.run2ndSearch(date)
        steps.run3rdSearch(date)
