channels_compare = [4, 5, 6,   16, 17, 18, 19, 20, 21, 22, 23,   25, 26, 27]
channels_for_avrg = [16, 17, 18, 19, 20, 21, 22]

def selection(list1):
    return [{
        'i': m['i'],
        'ref_id': m['ref_id'],
        'ref_time': m['ref_time'],
        'dug_avrg': m['dug_avrg'],
        'match': m['match'],
    } for m in list1]

def selection2(list1):
    return [{
        'i': m['i'],
#         'ref_time': m['ref_time'],
        'dug_avrg': m['dug_avrg'],
        'match': m['match'],
    } for m in list1]

def utf_to_sec_relative(utc):
    return utc.__float__() - 1486646660 + 20

def utf_average(event):
    sum = 0
    utc_list = [v for k,v in event['picks'].items() if k in channels_for_avrg]

    for t in utc_list:
        sum += t.__float__()
    # t = 0 is 2017-02-09T13-24-00
    return utf_to_sec_relative(sum / len(utc_list))
