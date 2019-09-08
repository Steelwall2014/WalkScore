def Attenuate(distance):
    '''距离衰减系数'''
    if distance <= 400:
        return 1
    elif 400 < distance <= 1600:
        return (-11/15000) * distance + (97/75)
    elif 1600 < distance <= 2400:
        return 0.12
    else:
        return 0