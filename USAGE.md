# 如何运行复合机器人语音控制系统

本指南将引导您完成在 Windows 系统上设置和运行此软件的所有步骤。

## 1. 系统必备组件

在开始之前，请确保您的系统上已安装以下软件：

1.  **Python**: 版本 3.9 或更高。您可以从 [python.org](https://www.python.org/downloads/) 下载。在安装时，请确保勾选 "Add Python to PATH" 选项。
2.  **LM Studio**: 用于在本地运行大型语言模型 (LLM)。您可以从 [lmstudio.ai](https://lmstudio.ai/) 下载。
3.  **Git**: 用于从代码仓库下载本项目。您可以从 [git-scm.com](https://git-scm.com/downloads) 下载。

## 2. 设置步骤

### 第一步：获取代码

打开一个命令行终端 (如 Command Prompt 或 PowerShell) 并运行以下命令，将项目代码克隆到您的本地计算机：

```bash
git clone <your-repository-url>
cd <repository-folder-name>
```

### 第二步：安装 Python 依赖项

在项目的根目录（您应该能看到 `requirements.txt` 文件），运行以下命令来安装所有必需的 Python 库：

```bash
pip install -r requirements.txt
```

此过程可能需要一些时间，它会自动安装 `Vosk`, `pyttsx3`, `Flask` 等所有需要的库。

## 3. 配置

### 第一步：配置并运行 LM Studio

1.  打开 LM Studio。
2.  在搜索框 (Search) 中，找到并下载一个您喜欢的通用聊天模型（例如 `Gemma`, `Llama3`, `Mistral` 等的某个版本）。
3.  切换到本地服务器 (Local Server) 选项卡 (左侧的 `<-->` 图标)。
4.  在顶部选择您下载的模型。
5.  点击 **Start Server** 按钮。

服务器启动后，它应该在 `http://localhost:1234` 上运行，这正是我们的程序将要连接的地址。

### 第二步（可选）：配置 Modbus 服务器地址

如果您需要连接到一个真实的 Modbus TCP 设备，您可能需要修改其 IP 地址和端口。打开以下文件：

-   `speech_ai_system/plugins/executor_plugin.py`
-   `speech_ai_system/plugins/state_manager_plugin.py`

在每个文件的顶部，您会看到如下配置，请根据您的设备修改 `MODBUS_HOST` 和 `MODBUS_PORT`：

```python
# --- Configuration ---
MODBUS_HOST = "localhost"  # 修改为您的机器人控制器的 IP 地址
MODBUS_PORT = 502          # 修改为您的机器人控制器的端口
```

如果只是测试，您可以忽略此步骤。

## 4. 运行应用程序

一切准备就绪后，在项目的根目录打开一个命令行终端，然后运行以下命令：

```bash
python -m speech_ai_system.main
```

您应该会看到如下输出，提示系统正在启动：

```
Starting Speech AI System...
A web-based GUI will be available at http://localhost:5001
```

## 5. 如何使用

1.  **打开 Web GUI**: 在您的浏览器中打开 `http://localhost:5001`。您将在这个页面上看到所有实时的系统日志。
2.  **下载Vosk模型**: 第一次运行时，程序会自动下载约 42MB 的 Vosk 语音识别模型。请耐心等待，直到您在日志中看到 "Listening for wake words..." 消息。
3.  **说出唤醒词**: 对着您的麦克风说出唤醒词。默认的唤醒词是 **"小车"** (xiǎo chē) 或 **"机器人"** (jī qì rén)。
4.  **下达指令**: 当您听到一声提示音（或在日志中看到 ASR 会话已启动）后，下达您的语音指令，例如 **"去A点"** 或 **"把箱子送到B点"**。
5.  **查看反馈**: 系统会将您的语音转换为文本，发送给 LM Studio 进行理解，然后执行相应的操作（或打印模拟的执行信息），并通过语音和日志给出反馈。
6.  **停止程序**: 当您想关闭程序时，回到运行程序的命令行终端，然后按下 **Ctrl + C**。程序将优雅地关闭所有服务。

---
如果您遇到任何问题，请首先检查 Web GUI 中的日志，它会提供关于系统内部状态的详细信息。
