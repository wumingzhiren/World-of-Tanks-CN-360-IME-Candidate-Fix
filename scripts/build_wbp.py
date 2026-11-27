# -*- coding: utf-8 -*-
"""
把 build/ime.swf 打成偶游盒子可用的 .wbp 安装包。

.wbp 结构（与盒子上架版一致）：
    Files/gui/flash/ime.swf   实际替换文件（loose 模式，直铺 res_mods）
    Files/原.swf              原生文件，仅供审核比对，不安装
    wbpimg.jpg                列表页封面图
    wbpinfo                   GB2312 编码的 XML 清单，EscapePath 决定装到哪

用法：
    python build_wbp.py                       # 默认版本 + 默认作者
    python build_wbp.py 2.4.3.0               # 指定游戏版本
    python build_wbp.py 2.4.3.0 你的昵称       # 版本 + 作者
    python build_wbp.py --author 你的昵称      # 只改作者，版本用默认

交互式打包（会先询问版本号）请用同目录的 build_package.py / 打包.bat。

ID 保持不变：盒子按 ID 识别为同一个插件，换版本号仍算同一插件的更新。
"""
import hashlib
import os
import re
import sys
import zipfile

# ---------------------------------------------------------------- 可改配置

# "loose"  -> 直接把 ime.swf 铺到 res_mods\<版本>\gui\flash\（默认，实测有效）
# "wotmod" -> 装到 mods\<版本>\xxx.wotmod（包能加载，但覆盖不了游戏自带的 ime.swf）
MODE = "loose"

AUTHOR = "无名氏有人用么"                       # 默认作者名，可命令行覆盖
MOD_NAME = "非1X缩放下输入法候选框错位修复"        # 盒子列表里显示的名字
# 盒子不接受外链引流，上架版此字段为 "-"；留空或改值都会进 XML，注意别填到外站
URL = "-"
PACKAGE_ID = "33C8ADA77A3A43BE866119AA85627691"   # 固定不变，改了就成另一个插件
DEFAULT_VERSION = "2.4.2.0"
MOD_VERSION = "1.0"
MOD_FILE = "IME_CandidateFix_%s.wotmod" % MOD_VERSION
WOTMOD_ID = "whd.ime_candidate_fix"
FIXED_TIME = (2026, 11, 26, 0, 0, 0)   # 固定时间戳，保证同输入输出同一 MD5

# ---------------------------------------------------------------- 路径

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
BUILD_DIR = os.path.join(ROOT, "build")
SWF = os.path.join(BUILD_DIR, "ime.swf")
ORIG = os.path.join(BUILD_DIR, "ime_orig.swf")
COVER = os.path.join(ROOT, "docs", "images", "cover-wbpimg.jpg")

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+\.\d+$")

META = (
    "<root>\r\n"
    "<id>" + WOTMOD_ID + "</id>\r\n"
    "<version>" + MOD_VERSION + "</version>\r\n"
    "<name>IME Candidate Fix</name>\r\n"
    "<description>Fixes IME candidate window position at non-1x interface scales</description>\r\n"
    "</root>\r\n"
)

SUMMARY = (
    "修复非 1X 界面缩放（2X / 1.5X / 1.25X / 0.75X 等）下中文输入法候选框偏移到光标右下方、"
    "输入框靠边时整块出屏的问题。1X 缩放本来就正常，无需安装。"
)


def build_info(target, version, author):
    """target 是 .wbp 解出的文件相对游戏根目录的落点。"""
    return (
        '<?xml version="1.0" encoding="gb2312"?>\r\n'
        "   <Package>\r\n"
        "  <ID>" + PACKAGE_ID + "</ID>\r\n"
        "  <Name>" + MOD_NAME + "</Name>\r\n"
        "  <Version>" + version + "</Version>\r\n"
        "  <Author>" + author + "</Author>\r\n"
        "  <Url><![CDATA[" + URL + "]]></Url>\r\n"
        "  <Summary><![CDATA[" + SUMMARY + "]]></Summary>\r\n"
        "  <FileList>\r\n"
        "\t</FileList>\r\n"
        "  <EscapePath>\r\n"
        '        <File Name="' + target + '"/>\r\n'
        "\r\n"
        "\t</EscapePath>\r\n"
        "</Package>"
    )


def zinfo(name, compress=zipfile.ZIP_DEFLATED):
    zi = zipfile.ZipInfo(name, date_time=FIXED_TIME)
    zi.compress_type = compress
    zi.external_attr = 0o644 << 16
    return zi


def build_wotmod(path, swf):
    """wotmod 内的条目必须 stored，引擎会报 'compression not supported'。"""
    S = zipfile.ZIP_STORED
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zinfo("meta.xml", S), META.encode("utf-8"))
        z.writestr(zinfo("res/", S), b"")
        z.writestr(zinfo("res/gui/", S), b"")
        z.writestr(zinfo("res/gui/flash/", S), b"")
        z.writestr(zinfo("res/gui/flash/ime.swf", S), swf)
    return os.path.getsize(path)


def build(version=DEFAULT_VERSION, author=AUTHOR, quiet=False):
    """打包并返回结果字典；失败抛异常。"""
    version = (version or DEFAULT_VERSION).strip()
    if not VERSION_RE.match(version):
        raise ValueError("版本号格式不对：%r（应形如 2.4.2.0，4 段数字）" % version)

    if not os.path.exists(SWF):
        raise IOError("找不到 %s，请先用 scripts\\build.bat 编译" % SWF)
    if not os.path.exists(COVER):
        raise IOError("找不到封面 %s" % COVER)

    os.makedirs(BUILD_DIR, exist_ok=True)
    out = os.path.join(BUILD_DIR, "[%s]%s.wbp" % (version, MOD_NAME))
    swf = open(SWF, "rb").read()

    if MODE == "loose":
        entry = "Files/gui/flash/ime.swf"
        payload = swf
        target = "res_mods\\%s\\gui\\flash\\ime.swf" % version
        note = "直铺 res_mods"
    else:
        tmp = os.path.join(BUILD_DIR, "_files")
        os.makedirs(tmp, exist_ok=True)
        wotmod = os.path.join(tmp, MOD_FILE)
        size = build_wotmod(wotmod, swf)
        entry = "Files/" + MOD_FILE
        payload = open(wotmod, "rb").read()
        target = "mods\\%s\\%s" % (version, MOD_FILE)
        note = "wotmod %d 字节" % size

    # 原生文件随包附带，供审核比对；EscapePath 里没有它，不会被安装
    orig = open(ORIG, "rb").read() if os.path.exists(ORIG) else None

    if os.path.exists(out):
        os.remove(out)
    S = zipfile.ZIP_STORED
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zinfo("wbpimg.jpg"), open(COVER, "rb").read())
        z.writestr(zinfo("wbpinfo"), build_info(target, version, author).encode("gb2312"))
        if MODE == "loose":
            z.writestr(zinfo("Files/gui/", S), b"")
            z.writestr(zinfo("Files/gui/flash/", S), b"")
            z.writestr(zinfo(entry), payload)
            if orig:
                z.writestr(zinfo("Files/原.swf"), orig)
        else:
            z.writestr(zinfo(entry), payload)

    data = open(out, "rb").read()
    result = {
        "path": out,
        "size": len(data),
        "md5": hashlib.md5(data).hexdigest(),
        "swf_size": len(swf),
        "swf_md5": hashlib.md5(swf).hexdigest(),
        "orig_size": len(orig) if orig else 0,
        "orig_md5": hashlib.md5(orig).hexdigest() if orig else "",
        "entry": entry,
        "target": target,
        "note": note,
        "version": version,
        "author": author,
        "url": URL,
    }
    if not quiet:
        print("mode      %s (%s)" % (MODE, note))
        print("version   %s" % version)
        print("author    %s" % author)
        print("url       %s" % URL)
        print("ime.swf   %d bytes  md5 %s" % (result["swf_size"], result["swf_md5"]))
        if orig:
            print("原.swf    %d bytes  md5 %s（仅供比对，不安装）" % (result["orig_size"], result["orig_md5"]))
        print("entry     %s  %d bytes" % (entry, len(payload)))
        print("target    %s" % target)
        print("wbp       %d bytes  md5 %s" % (result["size"], result["md5"]))
        print("output    %s" % out)
        with zipfile.ZipFile(out) as z:
            for i in z.infolist():
                print("  %8d  %s" % (i.file_size, i.filename))
    return result


def _parse_args(argv):
    version, author = DEFAULT_VERSION, AUTHOR
    args = list(argv)
    while args:
        a = args.pop(0)
        if a in ("-v", "--version") and args:
            version = args.pop(0)
        elif a in ("-a", "--author") and args:
            author = args.pop(0)
        elif VERSION_RE.match(a):
            version = a
        elif a not in ("-q", "--quiet"):
            author = a
    return version, author


def main():
    version, author = _parse_args(sys.argv[1:])
    try:
        build(version, author)
    except Exception as e:
        raise SystemExit("[FAILED] %s" % e)


if __name__ == "__main__":
    main()
