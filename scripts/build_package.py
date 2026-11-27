# -*- coding: utf-8 -*-
"""
交互式打包：先询问游戏版本号，再生成 .wbp 安装包。

直接双击同目录的「打包.bat」，或在命令行运行：
    python build_package.py

也可以带参数跳过提问：
    python build_package.py 2.4.3.0
    python build_package.py 2.4.3.0 作者名
"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_wbp  # noqa: E402

# 本机游戏目录，可用环境变量 WOT_DIR 覆盖
GAME_DIR = os.environ.get("WOT_DIR", r"C:\Games\World_of_Tanks_CN")


def detect_versions():
    """从 mods / res_mods 目录里找出所有版本号，新的在前。"""
    found = set()
    for sub in ("mods", "res_mods"):
        p = os.path.join(GAME_DIR, sub)
        if not os.path.isdir(p):
            continue
        try:
            names = os.listdir(p)
        except OSError:
            continue
        for n in names:
            if build_wbp.VERSION_RE.match(n) and os.path.isdir(os.path.join(p, n)):
                found.add(n)
    return sorted(found, key=lambda v: tuple(int(x) for x in v.split(".")), reverse=True)


def ask_version(default):
    while True:
        raw = input("请输入游戏版本号 [默认 %s]: " % default).strip()
        if not raw:
            return default
        if build_wbp.VERSION_RE.match(raw):
            return raw
        print("  格式不对，应形如 2.4.2.0（4 段数字），请重新输入。")


def ask_author(default):
    raw = input("作者名 [默认 %s]: " % default).strip()
    return raw or default


def ask_yes(prompt):
    raw = input(prompt + " [Y/n]: ").strip().lower()
    return raw in ("", "y", "yes")


def main():
    print("=" * 60)
    print("  非1X缩放输入法候选框错位修复 —— 盒子安装包打包工具")
    print("=" * 60)

    found = detect_versions()
    default_version = found[0] if found else build_wbp.DEFAULT_VERSION
    if found:
        print("本机已安装版本：%s" % "  ".join(found))
    else:
        print("未在本机游戏目录找到版本（%s），使用默认值。" % GAME_DIR)
    print()

    # 命令行带版本号时跳过提问与确认
    argv = [a for a in sys.argv[1:] if not a.startswith("-")]
    auto = bool(argv and build_wbp.VERSION_RE.match(argv[0]))
    if auto:
        version = argv[0]
        author = argv[1] if len(argv) > 1 else build_wbp.AUTHOR
        print("版本号 %s（来自命令行参数，跳过确认）" % version)
    else:
        version = ask_version(default_version)
        author = ask_author(build_wbp.AUTHOR)

    out_name = "[%s]%s.wbp" % (version, build_wbp.MOD_NAME)
    print()
    print("即将打包")
    print("  版本    %s" % version)
    print("  作者    %s" % author)
    print("  输出    build\\%s" % out_name)
    print("  落点    res_mods\\%s\\gui\\flash\\ime.swf" % version)
    print()
    if not auto and not ask_yes("确认打包？"):
        print("已取消。")
        return 1

    try:
        r = build_wbp.build(version, author)
    except Exception as e:
        print()
        print("[失败] %s" % e)
        return 1

    print()
    print("-" * 60)
    print("打包完成")
    print("  文件    %s" % r["path"])
    print("  大小    %d 字节" % r["size"])
    print("  MD5     %s" % r["md5"])
    print("  内含    ime.swf %d 字节  MD5 %s" % (r["swf_size"], r["swf_md5"]))
    print("-" * 60)

    # 同插件其它版本的包，提示一下避免传错
    others = []
    for n in os.listdir(build_wbp.BUILD_DIR):
        if n.endswith(".wbp") and n != out_name and build_wbp.MOD_NAME in n:
            others.append(n)
    if others:
        print()
        print("注意：build 目录下还有同插件的其它版本包，上传时别选错：")
        for n in others:
            print("  · %s" % n)

    print()
    print("下一步：用盒子「卸载 → 安装」这个包，进游戏输几个字确认候选框贴合光标。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
