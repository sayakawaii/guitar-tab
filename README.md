# 吉他谱

根据 YouTube 教学 / 演奏视频整理的吉他谱，每首歌一个文件夹，包含 PDF、预览图和生成脚本。

| 歌曲 | PDF | 来源 |
| --- | --- | --- |
| 平凡之路 | [平凡之路_吉他谱_大树音乐屋.pdf](平凡之路/平凡之路_吉他谱_大树音乐屋.pdf) | [大树音乐屋](https://www.youtube.com/watch?v=VsjkwWKKyxc)（视频截谱） |
| 平凡之路（+间奏 solo） | [平凡之路_吉他谱_大树+间奏solo.pdf](平凡之路_solo/平凡之路_吉他谱_大树+间奏solo.pdf)，试听：[全曲](平凡之路_solo/平凡之路_试听_全曲.mp3) / [副歌尾+solo](平凡之路_solo/平凡之路_试听_副歌尾+间奏solo.mp3) | 正歌：大树音乐屋（矢量重排）；间奏 solo：按[原曲](https://www.youtube.com/watch?v=NjTT5_RSkw4) rap 段和声新编；试听为合成音色 |
| 安和桥 | [安和桥_吉他弹唱谱_大树编配+伊森间奏.pdf](安和桥/安和桥_吉他弹唱谱_大树编配+伊森间奏.pdf) | 正歌：[大树音乐屋](https://www.youtube.com/watch?v=QsUSoMVoHcQ)；间奏：[Mr.伊森](https://www.youtube.com/shorts/2oKCmPwX558)（音频转写） |

曲谱版权归原编配者所有，仅供个人练习。

## 重新生成

脚本使用 Python 3.11，依赖 `yt-dlp opencv-python pillow reportlab librosa basic-pitch[onnx]`。视频文件不入库，需要时用 `yt-dlp` 重新下载到对应文件夹。

- 平凡之路：`python build_pdf.py`（使用 `lines/` 中的截帧）
- 平凡之路 + solo：谱面数据在 `data.py`，`python score.py` 生成 PDF，`python synth.py` 生成试听音频（另需 `scipy soundfile imageio-ffmpeg`）
- 安和桥：`python score.py`（谱面数据写在脚本里）
