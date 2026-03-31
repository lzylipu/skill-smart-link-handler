# QAS 任务管理器 - 规则配置示例

## 功能说明

从 QAS API 读取任务内容，应用规则，自动下载。

## 使用方法

### 1. 只查看任务
```bash
python3 qas-task-manager.py --list
```

### 2. 查看并应用规则（不执行）
```bash
python3 qas-task-manager.py --no-execute
```

### 3. 查看、应用规则、执行下载
```bash
python3 qas-task-manager.py
```

### 4. 查看、应用规则、执行下载、删除任务
```bash
python3 qas-task-manager.py --delete
```

---

## 规则配置（在脚本中修改）

编辑 `qas-task-manager.py` 中的 `TaskRules` 类：

```python
class TaskRules:
    # 关键词过滤
    INCLUDE_KEYWORDS = ["电影", "剧集"]  # 只处理包含这些词的任务
    EXCLUDE_KEYWORDS = ["广告", "推广"]  # 排除这些词
    
    # 文件大小过滤
    MIN_FILE_SIZE = 0  # 最小 0 字节
    MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 最大 10GB
    
    # 自动下载配置
    AUTO_DOWNLOAD = True  # 自动启用 aria2
    PAUSE = False  # 不暂停
    
    # 保存路径
    SAVE_PATH_TEMPLATE = "/{root}/{taskname}"
```

---

## 规则示例

### 示例 1：只下载电影
```python
INCLUDE_KEYWORDS = ["电影", "Movie", "Film"]
EXCLUDE_KEYWORDS = []
```

### 示例 2：排除广告
```python
INCLUDE_KEYWORDS = []  # 全部
EXCLUDE_KEYWORDS = ["广告", "推广", "赞助", "赌博"]
```

### 示例 3：只下载大文件（>1GB）
```python
MIN_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB
MAX_FILE_SIZE = float('inf')
```

### 示例 4：下载后不删除
```python
AUTO_DOWNLOAD = True
# 不传 --delete 参数
```

---

## 输出示例

```
============================================================
QAS 任务管理器
============================================================
时间：2026-03-30 21:00:00
API: http://YOUR_SERVER_IP:5015

============================================================
当前任务数：3
============================================================

[1] 复仇者联盟 4.2160p
    链接：https://pan.quark.cn/s/abc123...
    保存路径：/自动/复仇者联盟 4.2160p
    自动下载：❌

[2] 广告推广内容
    链接：https://pan.quark.cn/s/def456...
    保存路径：/自动/广告推广内容
    自动下载：❌

[3] 权力的游戏 S01
    链接：https://pan.quark.cn/s/ghi789...
    保存路径：/自动/权力的游戏 S01
    自动下载：❌


🔍 应用规则过滤...
[1/3] 检查：复仇者联盟 4.2160p
  ✓ 符合规则
[2/3] 检查：广告推广内容
  ⚠️ 排除关键词：广告
  ❌ 不符合规则
[3/3] 检查：权力的游戏 S01
  ✓ 符合规则

✅ 符合规则的任务：2/3

[1/2] 处理：复仇者联盟 4.2160p
  → 更新 aria2 配置...
  ✓ 配置更新成功
  → 执行下载...
  ✓ 下载执行成功

[2/2] 处理：权力的游戏 S01
  → 更新 aria2 配置...
  ✓ 配置更新成功
  → 执行下载...
  ✓ 下载执行成功

============================================================
处理完成！
成功：2
失败：0
============================================================
```

---

## API 调用流程

1. **GET /data** - 获取所有任务
2. **应用规则** - 过滤任务
3. **POST /update** - 更新 aria2 配置
4. **POST /run_script_now** - 执行下载
5. **POST /update** - 删除任务（可选）

---

## 高级用法

### 集成到自动化脚本

```python
from qas_task_manager import QASManager, TaskRules

# 自定义规则
TaskRules.INCLUDE_KEYWORDS = ["电影"]
TaskRules.AUTO_DOWNLOAD = True

# 创建管理器
manager = QASManager("http://YOUR_SERVER_IP:5015", "your_token")

# 处理所有任务
manager.process_all_tasks(auto_execute=True, auto_delete=False)
```

### 定时任务（Cron）

```bash
# 每小时检查并下载新任务
0 * * * * cd /path/to/skills && python3 qas-task-manager.py --delete >> /var/log/qas.log 2>&1
```

---

**状态**: ✅ 完成
**最后更新**: 2026-03-30
