# 描述性统计服务

基于 Python + Flask + Pandas 的 CSV 描述性统计服务，上传 CSV 文件即可获取各数值列的统计指标。

## 功能特性

- 📊 **描述性统计**：均值、中位数、标准差、最小值、最大值、四分位数（Q1/Q2/Q3）
- 🌐 **Web 界面**：美观的上传页面，支持拖拽上传
- 🔌 **API 接口**：RESTful API 便于集成
- 📁 **编码兼容**：自动识别 UTF-8 / GBK 编码
- 🛡️ **安全限制**：最大支持 100MB 文件

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

启动后访问：http://localhost:5000

## 使用方式

### Web 界面

1. 打开浏览器访问 http://localhost:5000
2. 点击上传区域或拖拽 CSV 文件
3. 点击「开始分析」按钮
4. 查看统计结果表格

### API 调用

```bash
curl -X POST -F "file=@sample_data.csv" http://localhost:5000/api/statistics
```

**响应示例：**

```json
{
  "row_count": 20,
  "column_count": 6,
  "numeric_columns": ["年龄", "身高", "体重", "收入", "工作年限"],
  "statistics": {
    "年龄": {
      "count": 20,
      "mean": 33.8,
      "median": 33.5,
      "std": 5.778,
      "min": 25,
      "25%": 28.75,
      "50%": 33.5,
      "75%": 38.25,
      "max": 45
    }
  }
}
```

## 项目结构

```
.
├── app.py              # Flask 应用主文件
├── requirements.txt    # Python 依赖
├── sample_data.csv     # 示例测试数据
└── README.md           # 使用说明
```

## 核心代码说明

- **`compute_statistics(df)`** — 统计计算核心函数，使用 Pandas 计算各数值列的描述性统计量
- **`/api/statistics`** — POST 接口，接收 CSV 文件并返回 JSON 格式统计结果
- **`/`** — Web 界面首页，包含拖拽上传和结果展示

## 测试数据

使用项目自带的 `sample_data.csv` 进行测试，包含 20 条人员数据（年龄、身高、体重、收入、工作年限等字段）。
