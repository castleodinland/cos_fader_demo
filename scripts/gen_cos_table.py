import math

TABLE_BITS = 8
TABLE_SIZE = (1 << TABLE_BITS) + 1

def gen_table():
    vals = []
    for i in range(TABLE_SIZE):
        angle = math.pi * i / (TABLE_SIZE - 1)
        q15 = int(round(math.cos(angle) * 32768))
        q15 = max(-32768, min(32767, q15))
        vals.append(q15)
    return vals

def main():
    vals = gen_table()
    with open('cos_table.inc', 'w') as f:
        for i, v in enumerate(vals):
            if i % 8 == 0:
                f.write('\n    ')
            f.write(f'{v}, ')
        f.write('\n')

if __name__ == '__main__':
    main()
