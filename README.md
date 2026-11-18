# X歌词

Windows 桌面透明歌词：逐字变色、3D 透视、柔和放大与动效，支持酷狗、QQ 音乐、网易云、汽水音乐。

> **这是 [Better lyrics | 浮词](https://github.com/Kerwin0126/Better-lyrics) 的非官方修改版，原作者 Kerwin。**
> 与原作者无隶属关系，也未获其背书。上游原始说明保留在 [README-UPSTREAM.md](README-UPSTREAM.md)。
>
> 修改者：xuwenxin-Lancelot

## 本修改版改了什么

**播放进度数据源**

- 酷狗：由系统辅助功能接口（MSAA）改为读取客户端内嵌页面的调试协议（CDP）
- 网易云：由 MSAA / 媒体会话改为读取播放页的进度滑块（CDP）

两者都要求播放器以调试模式启动，程序会自动重启对应播放器完成切换。

**界面与交互**

- 主色改为蓝色系，重绘应用图标，名称改为「X歌词」
- 侧边栏底部新增酷狗、网易云两个快捷启动入口
- 新增外观配置的导入 / 导出、歌词偏移的界面调节、位置记忆强化
- 帧率目标提升并开放 120 帧选项，内置一套默认外观参数

**沿用上游、未作改动**

- QQ 音乐、汽水音乐仍使用 Windows 系统媒体会话（SMTC）
- 歌词匹配、逐字渲染、3D 透视、动效、曲库页均为上游实现

完整说明见 [licenses/修改说明.txt](licenses/修改说明.txt)。

## 运行（源码方式）

```bash
pip install PySide6-Essentials==6.12.0
py -3 desktop_lyrics.py
```

需要先有读取器可执行文件（见下方构建步骤）。

## 构建

仓库不包含编译产物，需按顺序生成：

1. **原生组件**（需要 Visual Studio 的 C++ 工具链）
   ```powershell
   .\build_mediareader.ps1
   ```
   产出 `MediaReader.exe`、`QrcDecode.dll`、`RoundedBackdrop.dll`。

2. **辅助读取器**（需要 .NET Framework，用系统自带 csc 编译）
   ```powershell
   .\build_reader.ps1
   ```
   产出 `luotuo.exe`（由 `PlaybackReader.cs` 编译）。

3. **CDP 读取器**（需要 PyInstaller）
   ```bash
   pyinstaller --onefile --console --name cdp_reader --distpath ./dist_reader --workpath ./build_reader --specpath ./build_reader cdp_reader.py
   pyinstaller --onefile --console --name netease_reader --distpath ./dist_reader --workpath ./build_reader2 --specpath ./build_reader2 netease_reader.py
   ```

4. **许可清单**
   ```bash
   py -3 build_licenses.py
   ```

5. **打包**
   ```bash
   # 文件夹版（推荐，满足 LGPLv3 对替换库的要求）
   pyinstaller onedir.spec --distpath ./dist_onedir --workpath ./build_onedir -y
   # 单文件版
   pyinstaller onefile.spec --distpath ./dist_single --workpath ./build_single -y
   ```

## 许可

原创部分遵循 **Kerwin 非商业署名许可 1.0**（见 [LICENSE](LICENSE)）：允许非商业使用、修改与分享，
必须保留原作者署名并说明修改内容，禁止商业利用。修改名称、图标、界面不解除该限制。

第三方组件（Qt / PySide6 / Shiboken、Python、OpenSSL、PyInstaller、QRC 解码等）
适用各自上游许可，全文见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [licenses/](licenses/)。
