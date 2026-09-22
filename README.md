![数字人横版视频：让人物与信息，沿同一条时间线推进](assets/readme/hero.png)

# 月明·数字人横版视频

用本轮配音对应的口型视频和已有手势素材，制作数字人讲解与信息画面交替的横版视频。

## 你会得到什么

- 镜头配置、人物出镜窗口和手势衔接计划
- 以主配音和 SRT 为时钟的审看视频
- 渲染配置、生成记录与质量检查文件

## 试着这样说

```text
用 moonlit-avatar-video。用这份已确认配音、SRT、镜头表和口型视频制作数字人横版预览，先检查人物底片接缝。
```

## 安装与首次使用

将本仓库的完整目录交给支持本地 Skill 的 Agent 安装，保留 `SKILL.md` 与随附资源。已有同名版本时先检查差异；使用版本锁的工作区沿用自身升级机制。

让 Agent 安装：

```text
请安装这个 Skill：https://github.com/zzyong24/moonlit-avatar-video
```

也可通过 Skills CLI 安装：

```bash
npx skills add zzyong24/moonlit-avatar-video
```

## 配置与依赖

输入需要本轮口型视频、原始手势 catalog、已确认配音和 SRT。渲染脚本使用 Python、Pillow、ffmpeg/ffprobe。手势契约依赖 moonlit-video-script；手势工具随 moonlit-video-script 提供。封面阶段调用 moonlit-video-cover。

## 数据与使用边界

这个仓库不是口型生成服务，安装后仍需准备人物素材和所选服务。使用生成服务时，音频与人物参考按该服务流程提交。影片及配置保存在作品工程，平台发布另行处理。

## 配套 Skill

[video-cover](https://github.com/zzyong24/moonlit-video-cover) · [video-script](https://github.com/zzyong24/moonlit-video-script)

## 详细说明

执行流程与资源导航见 [SKILL.md](SKILL.md)。安装检查不代表真实业务验收；需要外部服务、账号登录或付费生成的步骤，应在使用者自己的环境中验证。

---

月明水清深 · `moonlit-avatar-video`

首图为 AI 生成的品牌概念插画，不是工具截图或执行结果。
