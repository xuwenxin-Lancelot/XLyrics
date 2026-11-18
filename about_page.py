# Author: Kerwin
"""The project's author, documentation and licensing page.

Modified 2026-11-18: restored upstream attribution and added a modification
notice, as required by the Kerwin non-commercial attribution licence.
"""
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QFrame,
                              QPushButton,QDialog,QTextBrowser,QScrollArea)
from app_paths import RESOURCE_DIR
from app_info import (PROJECT_NAME, VERSION, UPSTREAM_NAME, UPSTREAM_AUTHOR,
                      UPSTREAM_URL, MODIFIED_BY, LICENSE_NAME)

LINK_STYLE='color:#1488D8;text-decoration:none;'


def caption(text,kind='Subtle'):
    item=QLabel(text)
    item.setObjectName(kind)
    item.setWordWrap(True)
    item.setTextFormat(Qt.TextFormat.PlainText)
    return item


def link_label(html):
    item=QLabel(html)
    item.setWordWrap(True)
    item.setOpenExternalLinks(True)
    item.setTextFormat(Qt.TextFormat.RichText)
    return item


def show_document(parent,title,filename):
    dialog=QDialog(parent)
    dialog.setWindowTitle('X歌词 · '+title)
    dialog.resize(780,580)
    layout=QVBoxLayout(dialog)
    browser=QTextBrowser()
    browser.setOpenExternalLinks(True)
    browser.document().setBaseUrl(QUrl.fromLocalFile(str(RESOURCE_DIR)+'/'))
    path=RESOURCE_DIR/filename
    try:
        content=path.read_text(encoding='utf-8')
    except OSError:
        content='文档未包含在当前副本中。请查看发行包中的 licenses 目录。'
    if path.suffix=='.md':browser.setMarkdown(content)
    else:browser.setPlainText(content)
    layout.addWidget(browser)
    close=QPushButton('关闭')
    close.clicked.connect(dialog.accept)
    layout.addWidget(close,alignment=Qt.AlignmentFlag.AlignRight)
    dialog.exec()


def _bullets(lines):
    box=QWidget()
    column=QVBoxLayout(box)
    column.setContentsMargins(0,0,0,0)
    column.setSpacing(3)
    for line in lines:
        column.addWidget(caption('· '+line))
    return box


def build_about_page(studio):
    scroll=QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    body=QWidget()
    layout=QVBoxLayout(body)
    layout.setContentsMargins(0,0,8,0)
    layout.setSpacing(14)

    hero=QFrame(objectName='Card')
    row=QHBoxLayout(hero)
    row.setContentsMargins(24,22,24,22)
    icon=QLabel()
    icon.setPixmap(QPixmap(str(RESOURCE_DIR/'assets/x-logo-256.png')).scaled(
        88,88,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    row.addWidget(icon)
    text=QVBoxLayout()
    text.addWidget(caption(PROJECT_NAME,'Section'))
    text.addWidget(caption('透明桌面歌词，让每一句都有自己的样子。'))
    text.addWidget(caption('版本 '+VERSION+'   ·   Windows x64','Overline'))
    row.addLayout(text,1)
    layout.addWidget(hero)

    # 来源与署名 —— 许可第 4 条要求
    origin=QFrame(objectName='Card')
    content=QVBoxLayout(origin)
    content.setContentsMargins(24,18,24,18)
    content.addWidget(caption('来源 / ORIGIN','Overline'))
    content.addWidget(link_label(
        '本程序基于 <b>%s</b>，原作者 <b>%s</b>。<br>'
        '<a href="%s" style="%s">%s</a>'
        % (UPSTREAM_NAME, UPSTREAM_AUTHOR, UPSTREAM_URL, LINK_STYLE, UPSTREAM_URL)))
    content.addWidget(caption('原创部分的许可：'+LICENSE_NAME+'（非商业 · 须保留署名）','Overline'))
    buttons=QHBoxLayout()
    for title,filename in [('项目许可','LICENSE'),('第三方声明','THIRD_PARTY_NOTICES.md')]:
        button=QPushButton(title)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda checked=False,t=title,f=filename:show_document(studio,t,f))
        buttons.addWidget(button)
    buttons.addStretch()
    content.addLayout(buttons)
    layout.addWidget(origin)

    # 修改版说明 —— 许可第 5 条要求
    changes=QFrame(objectName='Card')
    body_layout=QVBoxLayout(changes)
    body_layout.setContentsMargins(24,18,24,18)
    body_layout.addWidget(caption('本修改版 / MODIFICATIONS','Overline'))
    body_layout.addWidget(caption(
        '这是非官方修改版，由「%s」修改，与原作者无隶属关系，也未获其背书。' % MODIFIED_BY,
        'Section'))
    body_layout.addWidget(caption('主要修改'))
    body_layout.addWidget(_bullets([
        '酷狗、网易云的播放进度改为读取客户端调试协议（CDP）的页面数据，替代原来的系统辅助功能接口',
        '界面改为蓝色主题，重绘应用图标，新增侧边栏播放器快捷启动',
        '新增配置导入导出、歌词偏移调节、位置记忆强化，帧率目标提高到 120',
        '内置一套默认外观参数',
    ]))
    body_layout.addWidget(caption('沿用上游、未作改动'))
    body_layout.addWidget(_bullets([
        'QQ 音乐、汽水音乐仍走系统媒体会话（SMTC），代码未改动',
        '歌词匹配、逐字渲染、曲库页、3D 透视与动效全部沿用上游实现',
    ]))
    body_layout.addWidget(caption('已知限制'))
    body_layout.addWidget(_bullets([
        '酷狗、网易云需要客户端以调试模式启动，程序会自动处理（会重启该播放器）',
        '网易云进度来自页面滑块，精度约 1 秒，由播放时钟插值补齐',
        '未对全部播放器逐一验证，个别客户端版本可能读取失败',
    ]))
    layout.addWidget(changes)

    # 第三方 —— LGPLv3 声明
    third=QFrame(objectName='Card')
    third_layout=QVBoxLayout(third)
    third_layout.setContentsMargins(24,18,24,18)
    third_layout.addWidget(caption('第三方组件 / THIRD PARTY','Overline'))
    third_layout.addWidget(caption(
        '本程序使用 Qt for Python（PySide6 6.12.0）、Shiboken 6.12.0 与 Qt 6.12.0，'
        '按 LGPLv3 使用，可替换或重新链接相应库。'))
    third_layout.addWidget(caption(
        '其余组件（Python、OpenSSL、libffi、PyInstaller、QRC 解码等）适用其各自上游许可，'
        '完整文本见发行包 licenses 目录。'))
    more=QPushButton('打开许可目录')
    more.setCursor(Qt.CursorShape.PointingHandCursor)
    more.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(RESOURCE_DIR/'licenses'))))
    third_layout.addWidget(more,alignment=Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(third)

    layout.addWidget(caption('数据说明：读取本机播放信息与歌词缓存；需要时联网查询歌词。无账号登录，不上传播放日志。'))
    layout.addStretch()
    scroll.setWidget(body)
    return scroll
