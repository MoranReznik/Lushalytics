def format_num(x, style='comma', decimals=1):

    if style == 'comma':
        x = round(x, decimals)
        s = f'{x:,}'
        if decimals == 0:
            s = s.rstrip('0').rstrip('.') if '.' in s else s
        return s
    
    elif style == 'suffix': 

        magnitude = 0
        while abs(x) >= 1000:
            magnitude += 1
            x /= 1000.0

        x = round(x, 0)
        return '{}{}'.format('{:f}'.format(x).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])