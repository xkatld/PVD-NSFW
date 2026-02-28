# 使用说明

### [在线讨饭](https://pay.fsynet.com/user/test.php)

### 免责声明
本程序及下载内容仅供个人学习与交流使用。严禁将本项目用于任何形式的商业用途或非法向他人售卖。用户需自行承担使用过程中可能产生的法律风险，作者对任何侵权或违规行为概不负责。

### 命令行选项

| 参数 | 描述 | 示例 |
| :--- | :--- | :--- |
| --id | 处理指定 ID 的单个视频 | python main.py --id 12345 |
| --range | 处理指定 ID 范围的视频 | python main.py --range 1000 2000 |
| --list | 处理给定 ID 列表的视频 | python main.py --list 101 102 103 |
| --keyword | 搜索关键词并处理结果 | python main.py --keyword "关键词" |
| --local | 启用本地存储模式 | python main.py --id 123 --local |
| --stats | 查看数据库抓取统计 | python main.py --stats |
| --help | 显示帮助信息 | python main.py --help |

### 存储模式

1. 云端同步 (默认)
直接运行命令时不带 --local。视频下载合并后会自动调用 rclone 同步至 OneDrive 配置路径。

2. 本地下载
命令末尾增加 --local。视频处理完成后将从临时目录移动至 videos 文件夹，不触发云端同步。

### 视频播放器 (Player)

项目内置了一个基于 Express 的视频在线播放器，支持本地 `videos` 目录的视频预览。

1. **启动服务**
进入 `player` 目录并运行以下命令进行编译与启动：
```bash
cd player
npm install
npx ts-node server.ts
```

2. **访问地址**
- 地址：`https://localhost:8443`
- 验证：首次访问需输入密码 `Aiwang888`

3. **功能特性**
- 自动读取 `videos/data.db` 数据库中的已下载视频。
- 支持按 ID 和标题浏览，直接在浏览器中流式播放。
- 具备基础的 Cookie 会话验证。

### 配置说明

修改项目根目录的 config.yaml 文件：
- storage.output_dir: 本地视频存放路径
- storage.db_name: 数据库文件名
- rclone.remote_dest: Rclone 远端路径
- concurrency.max_video_tasks: 视频并行处理数
- concurrency.max_segment_tasks: TS 片段下载并发数
