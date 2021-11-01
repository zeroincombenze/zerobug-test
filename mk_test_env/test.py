# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
import calendar


def evaluate_date(value):
    if not value:
        return value
    sep = tm = None
    if 'T' in value:
        sep = 'T'
    elif ' ' in value:
        sep = ' '
    if sep:
        value, tm = value.split(sep)
    if value.startswith('+'):
        value = str(
            date.today() + timedelta(int(value[1:])))
    elif value.startswith('-'):
        value = str(
            date.today() - timedelta(int(value[1:])))
    else:
        items = value.split('-')
        refs = [date.today().year, date.today().month, date.today().day]
        for i, item in enumerate(items):
            if item.startswith('<'):
                v = int(item[1:]) if item[1:].isdigit() else 1
                items[i] = refs[i] - v
            elif item in ('#>', '1>', '2>', '3>', '4>', '5>'):
                v = int(item[0]) if item[0].isdigit() else 1
                items[i] = refs[i] + v
            elif item in ('#', '##', '####'):
                items[i] = refs[i]
            else:
                items[i] = int(items[i]) or refs[i]
        if items[2] < 1:
            items[1] -= 1
        if items[1] < 1:
            items[1] = 12
            items[0] -= 1
        if items[2] < 1:
            items[2] = calendar.monthrange(items[0],
                                           items[1])[1]
        if items[1] > 12:
            items[1] = 1
            items[0] += 1
        if items[2] == 99:
            items[2] = calendar.monthrange(items[0],
                                           items[1])[1]
        elif items[2] > calendar.monthrange(items[0],
                                            items[1])[1]:
            items[2] = 1
            items[1] += 1
            if items[1] > 12:
                items[1] = 1
                items[0] += 1
        value = '%04d-%02d-%02d' % (
            items[0], items[1], items[2])
    if tm:
        value = '%s%s%s' % (value, sep, tm)
    return value


if __name__ == "__main__":
    tod = date.today()
    value = ''
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = None
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = False
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '2021-06-22'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '-30'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '+30'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '<#-#-#'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '<##-##-##'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '<3-12-99'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '####-##-##'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '#>-##-##'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '1>-##-##'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '2>-##-##'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '####-<#-31'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '####-<#-99'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '####-<2-99'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '####-##-<15'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '####-<1-99 00:00:00'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
    value = '####-<1-99T23:59:59'
    print('[%s] %s->%s' % (tod, value, evaluate_date(value)))
