# 批量查询医生执业注册信息

从[国家卫健委医师执业注册信息查询平台](https://zgcx.nhc.gov.cn/doctor)批量查询医生信息并截图。

## 环境要求

- Python 3.8+
- Chromium 浏览器（Playwright 自动管理）

## 安装

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 安装 Playwright 浏览器（仅首次，下载 Chromium）
playwright install chromium
```

## 用法

```bash
# 查询单个医生（默认省份：广东，默认医院：莲藕健康医院）
python3 batch-doctor-query.py 艾勇

# 一次查多人
python3 batch-doctor-query.py 艾勇 张三 李四

# 指定省份和医院
python3 batch-doctor-query.py --province 北京市 --hospital 协和医院 张三

# 从文件批量读取（每行一个姓名，# 开头为注释）
python3 batch-doctor-query.py --file names.txt

# 调整查询间隔（避免触发反爬）
python3 batch-doctor-query.py --interval 120 艾勇 张三

# 自定义输出目录
python3 batch-doctor-query.py --output ./截图 艾勇
```

## 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|---|---|---|---|
| `--province` | `-p` | 广东省 | 所在省份 |
| `--hospital` | `-H` | 莲藕健康医院 | 所在医疗机构 |
| `--interval` | `-i` | 60 | 查询间隔（秒） |
| `--file` | `-f` | - | 从文件读取姓名列表 |
| `--output` | `-o` | screenshots | 截图输出目录 |

## 输出

截图保存在 `screenshots/` 目录（默认），文件名格式为 `<姓名>.png`，内容为详情弹窗的完整截图。
