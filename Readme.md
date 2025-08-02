以下是你目前对**复合机器人语音控制系统**的全部需求总结，我将它分为**功能目标**、**技术偏好与实现方式**、**系统设计原则**三部分，方便你后续整理或立项使用：

---

## ✅ 一、功能需求总结

### 1. 唤醒词激活

- 系统需通过**唤醒词**激活（例如“小车”、“机器人”）。

- 唤醒词识别需**本地运行**，响应快，稳定可靠。

- 可选方案：Vosk、Snowboy 等。

### 2. 语音识别（ASR）

- 在唤醒后开始录音识别用户语音指令。

- 输出为识别文本，后续用于语义理解。

- 支持本地运行，兼容 Whisper 或 Vosk。

### 3. 语义理解与指令提取

- 使用**本地大语言模型**完成语义解析和指令提取。

- 支持通过**系统提示词（Prompt）控制语义行为**。

- 可以采用**MCP（模块化提示词控制）模式**，按模块输出意图、指令等。

- 需求支持两类输出：
  
  - **可执行指令（JSON格式）**
  
  - **自然语言回复**

### 4. 指令标准化

- 所有识别出的指令需统一为标准格式，例如：
  
  json
  
  复制编辑
  
  `{   "command": "move",   "params": { "target": "A" },   "say": "收到，前往 A 点" }`

### 5. 指令执行（机器人动作控制）

- **不由语音系统直接控制机器人**

- 项目中定义每个动作与对应的执行方式（如 ModbusTCP）

- 指令由控制执行器模块转发给机器人控制系统

- 通信方式采用标准工业协议：**ModbusTCP**

- 每个项目通过配置文件约定动作与寄存器/值的映射

### 6. 状态反馈播报

- 机器人状态（如位置到达、动作完成、电量不足）需反馈到语音系统。

- 系统能根据这些状态播报语音提示，提升交互体验。

- TTS可由行为执行器或状态监控模块触发。

### 7. 语音合成（TTS）

- 用于播报自然语言回复、状态反馈、任务进度等。

- 支持本地或边缘TTS（如 Edge-TTS、讯飞本地版等）

- 多种播报来源：
  
  - 大模型生成的回复
  
  - 状态变化事件
  
  - 项目中定义的提示语句模板

---

## 🛠️ 二、技术实现与架构要求

### 1. 模块化设计

- 系统划分多个功能模块（唤醒、ASR、NLP、执行器、TTS等）

- 每个模块应具备可替换性和独立性

### 2. 插件化机制

- 所有模块应通过配置动态加载（插件机制）

- 不同项目仅需修改模块配置即可适配

### 3. 事件驱动通信

- 模块之间通过**事件总线（EventBus）**通信

- 所有模块监听和触发标准事件（如：`wake_detected`, `asr_result`, `command_issued`, `tts_speak`）

### 4. 配置驱动适配

- 每个项目可以通过配置文件（JSON/YAML）定制：
  
  - 唤醒词
  
  - 可用指令
  
  - 指令到控制协议的映射
  
  - 回复模板

- 不同项目不需更改主程序代码，只需配置与控制模块适配。

---

## 📦 三、系统目标与通用性设计要求

| 目标        | 描述                              |
| --------- | ------------------------------- |
| **通用性**   | 一套系统框架可以适配不同的机器人项目，仅需切换配置和执行模块  |
| **本地运行**  | 所有核心模块（唤醒、大模型、TTS）默认支持本地运行，脱离网络 |
| **低耦合**   | 各模块间使用事件或接口通信，互不依赖底层实现          |
| **可扩展**   | 易于添加新的指令、控制方式或模块（如多机器人、多语言等）    |
| **支持热部署** | 理想情况下可热切换配置，适配新场景               |
| **运行稳定**  | 满足工业环境中长时间运行的稳定性和可维护性           |

---

## 🔚 总结一句话

> 你需要一个**模块化、事件驱动、可配置、支持本地大模型语义理解和TTS、通过标准指令间接控制机器人的通用语音控制系统框架**，并能快速适配多个项目现场
> 为了确保 AI 能够准确理解并实现代码，我将对我们讨论的**模块划分基础单位**进行一次全面、清晰、且包含详细说明和示例的总结。这份总结将作为未来代码实现的核心蓝图。

---









## **模块划分基础单位**

我们的语音控制系统将基于**模块化、插件化、事件驱动**的理念，将系统功能解耦为以下八个核心模块。每个模块都遵循**单一职责原则**，并通过**事件总线（EventBus）进行异步通信，以实现松耦合、强协作**。

---

### **模块详细说明**

#### 1. **WakeWordModule (唤醒词模块)**

- **职责**：持续监听音频流，并识别预设的唤醒词（例如“小车”、“机器人”）。一旦识别成功，便向系统发出**唤醒事件**。

- **输入**：来自麦克风的实时音频数据。

- **输出**：发出 `wake_word_detected` 事件，并携带识别到的唤醒词作为参数。

- **关键思想**：本地运行，不依赖云服务，确保低延迟和高可靠性。

- **技术选项**：可配置使用 Vosk、Snowboy 或其他本地唤醒词引擎。

- **示例代码（伪代码）**：
  
  Python
  
  ```
  class VoskWakeWordModule(BaseModule):
      def process(self, audio_chunk):
          if self.vosk_detector.detect(audio_chunk):
              EventBus.emit("wake_word_detected", data={"word": "机器人"})
  ```

---

#### 2. **ASRModule (语音识别模块)**

- **职责**：在接收到唤醒事件后，开始录音并识别用户的语音指令，将其转换为文本。

- **输入**：`wake_word_detected` 事件；录音设备的音频流。

- **输出**：发出 `asr_result` 事件，并携带识别出的文本。

- **关键思想**：只在被唤醒后工作，节省系统资源。

- **技术选项**：可配置使用 Whisper、Vosk 等本地语音识别模型。

- **示例代码（伪代码）**：
  
  Python
  
  ```
  @EventBus.on("wake_word_detected")
  def on_wake_word(event):
      asr_module.start_recording()
  
  class WhisperASRModule(BaseModule):
      def stop_recording(self):
          text = self.whisper_model.transcribe(self.audio_data)
          EventBus.emit("asr_result", data={"text": text})
  ```

---

#### 3. **NLPModule (自然语言处理模块)**

- **职责**：接收 ASR 模块的文本，利用大语言模型（LLM）或规则引擎，理解用户意图，并提取出标准化的 JSON 指令。

- **输入**：`asr_result` 事件，携带用户语音文本。

- **输出**：发出 `nlp_result` 事件，携带一个标准化的 JSON 对象。

- **关键思想**：通过**系统提示词（Prompt）**控制 LLM 的行为，实现语义解析。输出格式必须标准化，便于下游模块处理。

- **标准化输出格式（示例）**：
  
  JSON
  
  ```
  {
    "command": "move_to",
    "params": {
      "target": "A",
      "speed": "high"
    },
    "say": "好的，正在前往 A 点"
  }
  ```

- **示例代码（伪代码）**：
  
  Python
  
  ```
  @EventBus.on("asr_result")
  def on_asr_result(event):
      text = event.data["text"]
      prompt = f"根据'{text}'解析指令..."
      response = self.local_llm.generate(prompt)
      parsed_command = json.loads(response) # 假设 LLM 返回 JSON
      EventBus.emit("nlp_result", data=parsed_command)
  ```

---

#### 4. **CommandRouter (指令路由模块)**

- **职责**：接收 NLP 模块的标准化指令，并根据**项目配置文件**，将抽象的指令映射为具体的执行器操作或脚本调用。这是实现**配置驱动**和**脚本编程**的关键模块。

- **输入**：`nlp_result` 事件，携带标准化的 JSON 指令。

- **输出**：直接调用 **ExecutorModule** 的方法或加载执行脚本。

- **关键思想**：该模块是实现**配置驱动**和**脚本编程**的核心。所有项目特定的逻辑都通过配置文件隔离，无需修改代码。

- **项目配置文件与脚本映射（示意）**：
  
  JSON
  
  ```
  {
    "commands": {
      "transport_item": {
        "executor": "ScriptExecutor",
        "script_path": "scripts/transport_handler.py"
      },
      "move_to": {
        "executor": "ModbusExecutor",
        "action": "write_register",
        "params": { "register": 1000, "value": "{target_value}" }
      }
    }
  }
  ```

- **示例代码（伪代码）**：
  
  Python
  
  ```
  @EventBus.on("nlp_result")
  def on_nlp_result(event):
      command_data = event.data
      command_name = command_data["command"]
      config = self.load_config(command_name)
  
      if config["executor"] == "ScriptExecutor":
          self.script_executor.run(config["script_path"], command_data["params"])
      elif config["executor"] == "ModbusExecutor":
          self.modbus_executor.execute_action(config)
  ```

---

#### 5. **ExecutorModule (执行器模块)**

- **职责**：执行 CommandRouter 传递过来的具体硬件操作。

- **输入**：来自 `CommandRouter` 的具体操作指令（例如：写入 Modbus 寄存器）。

- **输出**：向硬件发送指令；执行结果（成功/失败）。

- **关键思想**：该模块专注于底层通信，与业务逻辑完全解耦。可配置使用 **ModbusExecutor**、**SerialExecutor** 等不同实现。

- **示例代码（伪代码）**：
  
  Python
  
  ```
  class ModbusExecutor(BaseModule):
      def execute_modbus_command(self, cmd_data):
          # 连接到 Modbus 设备
          # 根据 cmd_data 执行写入寄存器操作
          pass
  ```

---

#### 6. **TTSModule (文本转语音模块)**

- **职责**：将文本转换为音频数据。

- **输入**：`nlp_result` 事件中的 `say` 字段，或来自 `StateManager` 的状态文本。

- **输出**：发出 `tts_audio_ready` 事件，携带生成的音频数据路径或字节流。

- **关键思想**：与 `AudioOutput` 模块分离，确保 TTS 引擎的实现可以独立更换。

- **技术选项**：可配置使用 Edge-TTS、讯飞本地版、或其他 TTS 服务。

---

#### 7. **AudioOutput (音频播放模块)**

- **职责**：接收 TTS 模块生成的音频数据，并在扬声器上播放。

- **输入**：`tts_audio_ready` 事件，携带音频数据。

- **输出**：无直接输出，完成音频播放。

- **关键思想**：封装了音频播放的底层实现，可以轻松更换为不同的音频库或设备。

---

#### 8. **StateManager (状态监控模块)**

- **职责**：持续监控机器人或设备的状态（例如：位置、电量、任务完成状态）。一旦检测到状态变化，便向系统发出事件。

- **输入**：来自机器人或其他设备的状态数据流。

- **输出**：发出 `robot_status_changed` 事件，携带最新的状态信息。

- **关键思想**：将硬件状态变化反馈给语音系统，实现闭环交互。可以订阅此事件来触发 TTS 播报。

- **示例代码（伪代码）**：
  
  Python
  
  ```
  class ModbusStateManager(BaseModule):
      def poll_registers(self):
          current_status = self.modbus_client.read_register(3000)
          if current_status != self.last_status:
              EventBus.emit("robot_status_changed", data={"status": current_status})
  ```













## **插件式模块系统**

我们预计项目会有较大的发展，那么选择**基于框架的复杂插件系统**确实是更具前瞻性的决定。它能为未来的功能扩展、版本管理和团队协作打下坚实的基础。

在 Python 中，`pluggy` 是一个非常成熟和强大的插件框架，它被包括 `pytest`、`tox` 和 `apistar` 在内的许多著名项目所采用。它基于**钩子（Hook）**机制，能让插件系统变得非常灵活。

以下是使用 `pluggy` 来规划我们软件的插件式模块系统的方案：

---

### 核心理念：插件管理器与钩子

整个系统将围绕一个**插件管理器（PluginManager）运行，它负责发现、加载和调用插件。插件之间的通信不再是简单的事件，而是通过钩子函数**来实现。

1. **定义钩子规范 (Hook Specs)** 我们首先需要定义一个**钩子规范**，它是一个抽象的接口，声明了所有插件可以实现的函数。这就像是为整个系统定下“契约”。所有插件必须遵守这个规范来提供功能。

2. **实现插件** 每个功能模块（如 `ASRModule`, `NLPModule`）都将作为一个独立的**插件**。这些插件会实现钩子规范中定义的函数，来提供具体的功能。

3. **调用钩子** 核心程序在需要某个功能时，不会直接调用某个模块的方法，而是通过**插件管理器**调用对应的钩子。插件管理器会自动找到所有实现了该钩子的插件，并依次执行它们。

---

### 详细规划与步骤

#### 步骤一：创建钩子规范

首先，我们需要创建一个专门的模块（例如 `hooks.py`）来定义所有钩子。我们将使用 `pluggy.HookspecMarker` 来标记这些钩子。

Python

```
# hooks.py
import pluggy

hookspec = pluggy.HookspecMarker("speech_ai_system")

class SpeechAIHooks:
    """定义我们系统中的所有钩子规范"""

    @hookspec
    def on_wake_word_detected(self, word: str):
        """当唤醒词被检测到时调用，并传递检测到的词。"""

    @hookspec(firstresult=True)
    def process_asr_result(self, text: str) -> dict:
        """接收ASR结果文本，并返回标准化的指令JSON。        firstresult=True 表示只返回第一个非空的结果。"""

    @hookspec
    def execute_command(self, command_data: dict):
        """接收指令JSON，并执行具体操作。"""

    @hookspec
    def on_status_changed(self, status: dict):
        """当机器人状态发生变化时调用。"""
```

**说明：**

- `on_wake_word_detected`：这是一个事件通知类型的钩子，所有对唤醒词感兴趣的插件（如 ASR 模块）都可以实现它。

- `process_asr_result`：这是一个处理/转换类型的钩子，我们希望 `NLPModule` 实现它，将 ASR 文本转换为标准化 JSON。`firstresult=True` 意味着如果有多个插件实现了这个钩子，我们只取第一个返回结果。

- `execute_command`：这也是一个事件通知类型的钩子，`ExecutorModule` 会实现它来执行指令。

---

#### 步骤二：实现插件

接下来，我们将把每个功能模块实现为一个符合钩子规范的插件。每个插件都需要有一个入口点（`hookimpl`）来标记其实现的钩子。

Python

```
# modules/nlp_plugin.py
import pluggy
import json

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class NLPPlugin:
    """负责语义理解的插件"""

    @hookimpl
    def process_asr_result(self, text: str) -> dict:
        """使用本地LLM将文本解析为指令。"""
        print(f"NLPPlugin: 收到文本 '{text}'，开始解析...")
        # 假设这里调用了本地大模型
        if "去A点" in text:
            result = {
                "command": "move",
                "params": {"target": "A"},
                "say": "收到，前往 A 点"
            }
            return result
        return None # 返回 None 表示这个插件无法处理

# modules/executor_plugin.py
class ExecutorPlugin:
    """负责指令执行的插件"""

    @hookimpl
    def execute_command(self, command_data: dict):
        """执行具体的机器人动作。"""
        print(f"ExecutorPlugin: 收到指令 {command_data}，正在执行...")
        if command_data["command"] == "move":
            # 这里是 ModbusTCP 等协议的实际执行代码
            pass
```

---

#### 步骤三：创建插件管理器和核心程序

主程序将负责创建和配置**插件管理器**，加载所有插件，并调用钩子来驱动整个流程。

Python

```
# main.py
import pluggy
from .hooks import SpeechAIHooks
from .modules import nlp_plugin, executor_plugin

# 1. 创建插件管理器
pm = pluggy.PluginManager("speech_ai_system")
pm.add_hookspecs(SpeechAIHooks)

# 2. 注册插件（可以从配置或目录中动态加载）
pm.register(nlp_plugin.NLPPlugin())
pm.register(executor_plugin.ExecutorPlugin())

def main_loop():
    # 模拟唤醒词和ASR流程
    asr_text = "去A点"
    print("核心程序: 唤醒词被检测到，ASR识别结果为:", asr_text)

    # 3. 调用钩子来触发NLP模块
    command_result = pm.hook.process_asr_result(text=asr_text)

    if command_result:
        print("核心程序: 收到NLP解析结果:", command_result)
        # 4. 调用钩子来触发执行模块
        pm.hook.execute_command(command_data=command_result)
    else:
        print("核心程序: NLP模块未能解析指令。")

if __name__ == "__main__":
    main_loop()
```

**运行结果：**

```
核心程序: 唤醒词被检测到，ASR识别结果为: 去A点
NLPPlugin: 收到文本 '去A点'，开始解析...
核心程序: 收到NLP解析结果: {'command': 'move', 'params': {'target': 'A'}, 'say': '收到，前往 A 点'}
ExecutorPlugin: 收到指令 {'command': 'move', 'params': {'target': 'A'}, 'say': '收到，前往 A 点'}，正在执行...
```

---

### 总结

这种基于 `pluggy` 的**插件式模块系统**提供了以下关键优势：

- **真正的模块化**：`NLPPlugin` 和 `ExecutorPlugin` 之间完全解耦。它们不知道彼此的存在，只知道要实现特定的钩子。

- **易于扩展**：如果你想添加一个日志插件，只需创建一个新的模块，实现 `on_wake_word_detected` 和 `execute_command` 钩子来记录事件，然后将其注册到插件管理器即可，无需修改任何现有代码。

- **集中管理**：所有的插件都通过一个集中的**插件管理器**来管理和调用，使得系统的整体行为更加可控。

这个方案为我们后续的开发提供了非常清晰和强大的架构。



### CommandRouter 模块

我们讨论的**基于 `pluggy` 的插件框架**，为 `CommandRouter` 模块的融入提供了非常优雅且强大的方式。

在传统的事件驱动模型中，`CommandRouter` 只是一个监听事件并执行操作的模块。但在 `pluggy` 的框架下，`CommandRouter` 将扮演一个更核心的角色：它将成为一个**插件**，负责协调 NLP 结果和执行器插件之间的关系，同时**将配置驱动和脚本编程的逻辑封装起来**。

下面是 `CommandRouter` 融入这个框架的具体方案。

---

### CommandRouter 的角色与工作流程

在 `pluggy` 框架中，`CommandRouter` 不会直接调用 `Executor` 模块，而是通过调用钩子来触发执行。它的主要职责是：

1. **监听 NLP 结果**：它将实现 `process_asr_result` 钩子，接收 NLP 模块的解析结果。

2. **加载配置**：根据 NLP 结果中的 `command` 名称，它会动态加载对应的**项目配置文件**。

3. **触发执行钩子**：根据配置文件中的指令，它会调用 `execute_command` 钩子，并将具体执行所需的参数传递给它。

这样设计的好处是，`CommandRouter` 成了整个指令执行环节的**大脑**，而 `Executor` 模块则只需要专注于执行具体的任务，两者解耦得更加彻底。

---

### 具体实现步骤

#### 步骤一：扩展钩子规范

为了让 `CommandRouter` 能够更好地控制执行过程，我们可以扩展一下钩子规范，添加一个专门用于执行脚本的钩子。

Python

```
# hooks.py (扩展后的版本)
import pluggy

hookspec = pluggy.HookspecMarker("speech_ai_system")

class SpeechAIHooks:
    # ... (其他钩子保持不变)

    @hookspec
    def run_script(self, script_path: str, params: dict) -> dict:
        """调用并运行一个外部脚本，并传递参数。"""
```

#### 步骤二：实现 CommandRouter 插件

`CommandRouter` 将作为一个插件，主要实现 `process_asr_result` 这个钩子。但请注意，`pluggy` 默认是先执行所有实现了某个钩子的插件。如果 `NLPModule` 和 `CommandRouter` 都实现了 `process_asr_result`，那么它们都会被调用。为了避免冲突，我们可以让 `CommandRouter` 只负责处理 `nlp_result` 事件，而不是直接实现 `process_asr_result` 钩子。

一个更简洁、更符合逻辑的方案是：让 `NLPModule` 只负责解析，`CommandRouter` 在接收到 NLP 的结果后，**再决定如何调用下游的钩子**。

下面是 `CommandRouter` 的实现方式：

Python

```
# modules/command_router_plugin.py
import pluggy
import json

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class CommandRouterPlugin:
    def __init__(self, config_file="config/project.json", pm=None):
        self.config = self._load_config(config_file)
        self.pm = pm  # 插件管理器实例

    def _load_config(self, file_path):
        with open(file_path, "r") as f:
            return json.load(f)

    @hookimpl(hookwrapper=True)
    def process_asr_result(self, text: str) -> dict:
        """        这个钩子实现以包装器模式(hookwrapper)来监听NLP结果。        它在NLP插件执行前后执行，以获取结果。        """
        outcome = yield
        nlp_result = outcome.get_result()
        if nlp_result:
            self.route_command(nlp_result)
        return nlp_result

    def route_command(self, command_data: dict):
        """核心路由逻辑"""
        command_name = command_data.get("command")
        if not command_name or command_name not in self.config["commands"]:
            print("CommandRouter: 未知指令，无法路由。")
            return

        command_config = self.config["commands"][command_name]
        executor_type = command_config.get("executor")

        if executor_type == "ModbusExecutor":
            print(f"CommandRouter: 路由到 ModbusExecutor，执行动作...")
            self.pm.hook.execute_command(command_data=command_data)
        elif executor_type == "ScriptExecutor":
            script_path = command_config.get("script_path")
            if script_path:
                print(f"CommandRouter: 路由到脚本执行器，运行 {script_path}...")
                self.pm.hook.run_script(script_path=script_path, params=command_data.get("params", {}))
            else:
                print("CommandRouter: 脚本路径未配置。")
```

**说明：**

- 我们使用 `hookwrapper=True` 模式，让 `CommandRouter` 在 `NLPModule` 之后执行，来获取它的结果，这种方式比直接监听事件更符合 `pluggy` 的设计哲学。

- `CommandRouterPlugin` 接收一个 `pm` (插件管理器) 实例，以便能够调用其他钩子。

- `route_command` 方法是核心，它根据加载的配置文件，决定调用 `execute_command` 还是 `run_script`。

#### 步骤三：实现 ScriptExecutor 插件

最后，我们需要一个插件来专门负责执行脚本。

Python

```
# modules/script_executor_plugin.py
import subprocess
import json

hookimpl = pluggy.HookimplMarker("speech_ai_system")

class ScriptExecutorPlugin:
    """负责执行外部脚本的插件"""

    @hookimpl
    def run_script(self, script_path: str, params: dict) -> dict:
        """执行指定路径的脚本，并传递参数。"""
        print(f"ScriptExecutorPlugin: 正在执行脚本 {script_path}，参数为 {params}")
        try:
            # 使用 subprocess 调用外部脚本，并将参数作为 JSON 字符串传递
            result = subprocess.run(
                ["python", script_path, json.dumps(params)],
                capture_output=True,
                text=True,
                check=True
            )
            # 假设脚本将结果以 JSON 格式打印到标准输出
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"脚本执行失败: {e.stderr}")
            return {"status": "error", "message": e.stderr}
```

### 总结

将 `CommandRouter` 融入 `pluggy` 框架后，其主要职能被清晰地定义为**指令路由**。它不再是一个硬编码的逻辑，而是**一个可配置、可替换的插件**。通过这种方式：

- **解耦**：`NLPModule` 只管解析，`CommandRouter` 只管路由，`ExecutorModule` 只管执行。

- **灵活性**：我们可以通过修改配置文件来改变路由规则，甚至可以编写新的脚本插件来处理更复杂的业务逻辑。

- **可维护性**：所有项目特有的逻辑都集中在 `CommandRouter` 的配置文件或它调用的脚本中，核心系统保持纯净。

这种设计让系统在未来面对复杂业务需求时，能够保持极高的扩展性和可维护性。
