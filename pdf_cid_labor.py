"""已知原始 pdf 和 导出后的含 (cid:xxx) 的 txt 文件。
通过对比，手工找出 (cid:xxx) 和 字符的对应关系。
目前仅适用部分英语字体
"""

import re

cmap = {
    2: "’",
    3: " ",
    4: "A",
    17: "B",
    18: "C",
    24: "D",
    28: "E",
    38: "F",
    39: "G",
    44: "H",
    47: "I",
    58: "J",
    60: "K",
    62: "L",
    68: "M",
    69: "N",
    75: "O",
    87: "P",
    89: "Q",
    90: "R",
    94: "S",
    100: "T",
    104: "U",
    115: "V",
    116: "W",
    121: "X",
    122: "Y",
    127: "Z",
    258: "a",
    271: "b",
    272: "c",
    282: "d",
    286: "e",
    296: "f",
    297: "fb",
    299: "ff",
    322: "fj",
    325: "fk",
    332: "ft",
    336: "g",
    346: "h",
    349: "i",
    361: "j",
    364: "k",
    367: "l",
    373: "m",
    374: "n",
    381: "o",
    393: "p",
    395: "q",
    396: "r",
    400: "s",
    410: "t",
    414: "tf",
    415: "ti",
    425: "tt",
    426: "ttf",
    427: "tti",
    437: "u",
    448: "v",
    449: "w",
    454: "x",
    455: "y",
    460: "z",
    853: ",",
    855: ":",
    856: ".",
    859: "’",
    876: "/",
    882: "-",
    894: "(",
    895: ")",
    919: '"',
    926: "©",
    928: "®",
    1004: "0",
    1005: "1",
    1006: "2",
    1007: "3",
    1008: "4",
    1009: "5",
    1010: "6",
    1011: "7",
    1012: "8",
    1013: "9",
}


CID_REGEX = re.compile(r"\(\s*cid\s*:\s*\d+\s*\)")


def gather_unknown_cid(unique_str_cids):
    res = []
    for str_cid in unique_str_cids:
        cid = int(str_cid.split(":")[1].strip(")").strip())
        if cid not in cmap or cmap[cid] is None:
            res.append(str_cid)
    return res


def replace_cid(match):
    str_cid = match.group(0)
    cid = int(str_cid.split(":")[1].strip(")").strip())
    s = cmap.get(cid, str_cid)
    return s


input_fn = "a.txt"
output_fn = "b.txt"

with open(input_fn, "r", encoding="utf-8") as f:
    raw_content = f.read()

cid_matches = CID_REGEX.findall(raw_content)

unique_str_cids = set(cid_matches)
print(f"文件中 (cid:xxx) 集合的大小: {len(unique_str_cids)}")


unknown_cid_list = gather_unknown_cid(unique_str_cids)
if unknown_cid_list:
    print("未知的 (cid:xxx) 列表:")
    for str_cid in unknown_cid_list:
        print(str_cid)


replaced_content = CID_REGEX.sub(replace_cid, raw_content)

with open(output_fn, "w", encoding="utf-8") as f:
    f.write(replaced_content)
