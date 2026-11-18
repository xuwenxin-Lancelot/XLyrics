# -*- coding: utf-8 -*-
"""Assemble the licences/ folder that must ship with every build.

Kerwin NC 1.0 asks for the licence to travel with any copy; LGPLv3 asks for the
GPL+LGPL texts, a notice, and a way to obtain the library sources; MIT asks for
the copyright notice. This script collects all of it from the repo.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'licenses')

QT_NOTICE = """Qt for Python (PySide6) / Shiboken / Qt —— LGPLv3 声明
=====================================================

本程序使用以下组件：
  · PySide6 Essentials 6.12.0
  · Shiboken6 6.12.0
  · Qt 6.12.0（Core / Gui / Widgets / Network / Svg）

上述组件按 GNU Lesser General Public License version 3 (LGPLv3) 使用。
完整许可文本见本目录的 LGPL-3.0.txt 与 GPL-3.0.txt。

对应源码获取地址（Qt 官方发布）：
  PySide / Shiboken
    https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.12.0-src/pyside-setup-everywhere-src-6.12.0.tar.xz
  Qt Base
    https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/qtbase-everywhere-src-6.12.0.tar.xz
  Qt Svg
    https://download.qt.io/official_releases/qt/6.12/6.12.0/submodules/qtsvg-everywhere-src-6.12.0.tar.xz

许可说明：
  https://doc.qt.io/qtforpython-6/licenses.html
  https://www.qt.io/development/open-source-lgpl-obligations

替换与重新链接：
  本发行版为 onedir（文件夹）形式，Qt 相关动态库位于 _internal 目录下，
  未加密、未设置完整性校验。你可以用自己的兼容版本替换这些 DLL，
  也可以为调试修改过的库进行必要的逆向工程。
"""

INDEX = """许可文件索引
============

LICENSE-Kerwin-NC-1.0.txt   本项目原创部分（上游 Better lyrics | 浮词）的许可全文
LGPL-3.0.txt                GNU Lesser General Public License v3
GPL-3.0.txt                 GNU General Public License v3（LGPLv3 要求一并提供）
Qt-PySide6-NOTICE.txt       Qt / PySide6 / Shiboken 的使用声明、源码地址与替换说明
MIT-qq_des.txt              QRC 解码所依赖 DES 实现的 MIT 许可与版权声明
修改说明.txt                 本修改版的来源、修改内容、未改动部分与已知限制
third_party/                其余第三方组件（Python、OpenSSL、libffi、PyInstaller 等）的许可原文

上游项目：Better lyrics | 浮词  https://github.com/Kerwin0126/Better-lyrics
原作者：Kerwin
"""

MODIFICATION = """X歌词 —— 修改版说明
========================

一、来源
  本程序基于 Better lyrics | 浮词（0.6.0），原作者 Kerwin。
  上游仓库：https://github.com/Kerwin0126/Better-lyrics
  原创部分遵循「Kerwin 非商业署名许可 1.0」，全文见 LICENSE-Kerwin-NC-1.0.txt。

  这是非官方修改版，修改者 xuwenxin-Lancelot，与原作者无隶属关系，也未获其背书。
  本修改版继续按同一许可（非商业、保留署名）提供，不得用于商业用途。

二、主要修改
  1. 播放进度数据源
     · 酷狗：由系统辅助功能接口（MSAA）改为读取客户端内嵌页面的调试协议（CDP）
     · 网易云：由 MSAA / 媒体会话改为读取播放页的进度滑块（CDP）
     两者都需要播放器以调试模式启动，程序会自动重启该播放器完成切换。
  2. 界面
     · 主色改为蓝色系，重绘应用图标，名称改为「X歌词」
     · 侧边栏底部新增酷狗、网易云两个快捷启动入口
  3. 功能
     · 新增外观配置的导入 / 导出
     · 新增歌词偏移的界面调节（毫秒级，可正负）
     · 强化位置记忆（双行、滚动分别记忆）
     · 帧率目标提升并开放 120 帧选项
     · 内置一套默认外观参数

三、沿用上游、未作改动
  · QQ 音乐、汽水音乐仍使用 Windows 系统媒体会话（SMTC），相关代码未改动
  · 歌词匹配、逐字渲染、3D 透视、动效、曲库页均沿用上游实现
  · 本地歌词缓存读取（KRC / QRC）沿用上游实现

四、已知限制
  · 酷狗、网易云必须运行在调试模式下，否则读不到进度；程序会自动处理，
    处理时会关闭并重启对应播放器
  · 网易云进度来自页面滑块，刷新率约 1 秒，由播放时钟插值补齐，
    因此整秒附近可能有轻微修正
  · 未对全部播放器、全部客户端版本逐一验证，个别版本可能读取失败
  · 本修改版未覆盖上游的安装程序、自动更新等发布相关能力

五、构建
  构建脚本与说明见随附源码包（build 相关说明与 *.spec 文件）。
"""


def _copy(src, dst):
    if not os.path.isfile(src):
        print('  ! 缺少 %s' % src)
        return False
    shutil.copy2(src, dst)
    return True


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    _copy(os.path.join(HERE, 'LICENSE'),
          os.path.join(OUT, 'LICENSE-Kerwin-NC-1.0.txt'))
    _copy(os.path.join(HERE, 'third_party', 'licenses', 'LGPL-3.0-only.txt'),
          os.path.join(OUT, 'LGPL-3.0.txt'))
    _copy(os.path.join(HERE, 'third_party', 'licenses', 'GPL-3.0-only.txt'),
          os.path.join(OUT, 'GPL-3.0.txt'))
    _copy(os.path.join(HERE, 'third_party', 'qq_des', 'LICENSE'),
          os.path.join(OUT, 'MIT-qq_des.txt'))

    src_tree = os.path.join(HERE, 'third_party', 'licenses')
    if os.path.isdir(src_tree):
        shutil.copytree(src_tree, os.path.join(OUT, 'third_party'))
        print('  third_party/ 已复制')

    for name, content in (('Qt-PySide6-NOTICE.txt', QT_NOTICE),
                          ('许可文件索引.txt', INDEX),
                          ('修改说明.txt', MODIFICATION)):
        with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
            f.write(content)

    total = sum(len(files) for _, _, files in os.walk(OUT))
    print('licenses/ 生成完成，共 %d 个文件' % total)


if __name__ == '__main__':
    sys.exit(main() or 0)
