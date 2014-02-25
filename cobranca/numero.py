def split1000(s, sep=',', dec=None):
    z = -1
    if dec == None:
        x = 0
        while x < len(s):
            if s[x].isdigit() == False:
                z = x
                dec = s[x]
                break
            else:
                x = x + 1
    else:
        z = s.find(dec)

    if z >= 0:
        #print s[:z]
        return split1000(s[:z], sep, dec) + s[z:]
    else:
        if len(s) <= 3:
            return s  
        else: 
            x = s[:3]
            
            if x.isdigit() == False:
                return s
            else:
                return split1000(s[:-3], sep) + sep + s[-3:]

print(split1000('12134,78','.'))