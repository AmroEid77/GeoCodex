# 🌍 GeoCodex - Comprehensive Technical Documentation

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Core Components Deep Dive](#3-core-components-deep-dive)
4. [Workflow Pipelines](#4-workflow-pipelines)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Module Reference](#6-module-reference)
7. [LLM Provider Integration](#7-llm-provider-integration)
8. [Prompt Engineering](#8-prompt-engineering)

---

## 1. Project Overview

**GeoCodex** is an AI-powered QGIS plugin that transforms natural language queries into executable PostGIS spatial SQL queries. It leverages a **dual-agent architecture** where:

- **Interpreter Agent**: A vision-capable LLM that analyzes images and extracts spatial workflow requirements
- **Coder Agent**: An SQL-specialized LLM that generates optimized PostGIS queries

### Key Capabilities

| Feature                | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| Natural Language → SQL | Convert plain English to PostGIS queries              |
| Image Analysis         | Extract spatial workflows from diagrams/maps          |
| Self-Healing SQL       | Automatic error correction with up to 3 retries       |
| Multi-Provider Support | OpenAI, Anthropic, Gemini, NVIDIA, OpenRouter, Ollama |
| DE-9IM Support         | Advanced topological analysis                         |
| Async Operations       | Non-blocking UI with threaded workers                 |

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              GeoCodex Plugin                                      │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        UI LAYER (PyQt5)                                     │ │
│  │  ┌─────────────┐  ┌─────────────────┐  ┌────────────────┐                   │ │
│  │  │Configuration│  │  Ask Data Tab   │  │  GeoCodex Chat │                   │ │
│  │  │    Tab      │  │  (NL → SQL)     │  │  (Dual-Agent)  │                   │ │
│  │  └──────┬──────┘  └────────┬────────┘  └───────┬────────┘                   │ │
│  └─────────┼──────────────────┼───────────────────┼────────────────────────────┘ │
│            │                  │                   │                               │
│            └──────────────────┴───────────────────┘                               │
│                               │                                                   │
│  ┌────────────────────────────▼────────────────────────────────────────────────┐ │
│  │                    ORCHESTRATION LAYER                                       │ │
│  │  ┌──────────────────────────────────────────────────────────────────────┐   │ │
│  │  │              WorkflowOrchestrator (orchestrator.py)                  │   │ │
│  │  │  • Manages dual-agent coordination                                   │   │ │
│  │  │  • Handles NL-to-SQL, Image-to-SQL, Chat workflows                   │   │ │
│  │  │  • Implements self-healing SQL with retry logic                      │   │ │
│  │  │  • Creates and manages LLM client instances                          │   │ │
│  │  └──────────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                               │                                                   │
│  ┌────────────────────────────▼────────────────────────────────────────────────┐ │
│  │                       CORE LAYER (geo_codex_logic/core/)                    │ │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐        │ │
│  │  │    LLMClient      │  │   LLMProvider     │  │   DBConnector     │        │ │
│  │  │  (llm_client.py)  │  │ (llm_provider.py) │  │ (db_connector.py) │        │ │
│  │  │                   │  │                   │  │                   │        │ │
│  │  │ • Unified API     │  │ • Provider enums  │  │ • PostgreSQL      │        │ │
│  │  │ • Text generation │  │ • Model catalogs  │  │   connection      │        │ │
│  │  │ • Vision queries  │  │ • Factory pattern │  │ • Schema fetching │        │ │
│  │  │ • Connection test │  │ • Client classes  │  │ • Query execution │        │ │
│  │  └─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘        │ │
│  └────────────┼──────────────────────┼──────────────────────┼──────────────────┘ │
│               │                      │                      │                    │
│  ┌────────────▼──────────────────────▼──────────────────────▼──────────────────┐ │
│  │                       UTILITIES LAYER (geo_codex_logic/utils/)              │ │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐        │ │
│  │  │   PromptBuilder   │  │    ImageUtils     │  │   ErrorHandler    │        │ │
│  │  │(prompt_builder.py)│  │  (image_utils.py) │  │(error_handler.py) │        │ │
│  │  │                   │  │                   │  │                   │        │ │
│  │  │ • SQL prompts     │  │ • Base64 encoding │  │ • (Reserved)      │        │ │
│  │  │ • Chat prompts    │  │ • Image loading   │  │                   │        │ │
│  │  │ • DE-9IM refs     │  │                   │  │                   │        │ │
│  │  └───────────────────┘  └───────────────────┘  └───────────────────┘        │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                       EXTERNAL SERVICES                                      │ │
│  │  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐   │ │
│  │  │ OpenAI  │ │Anthropic │ │ Gemini │ │ NVIDIA │ │OpenRouter│ │  Ollama  │   │ │
│  │  └─────────┘ └──────────┘ └────────┘ └────────┘ └──────────┘ └──────────┘   │ │
│  │                                                                              │ │
│  │                      PostgreSQL/PostGIS Database                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Components Deep Dive

### 3.1 Entry Point: `geo_codex.py`

The main plugin entry point that QGIS loads. It:

- Initializes the plugin within QGIS
- Creates toolbar icon and menu entries
- Manages the plugin lifecycle (`initGui()`, `unload()`, `run()`)
- Creates and displays the main dialog (`GeoCodexDialog`)

```python
class GeoCodex:
    def __init__(self, iface):
        self.iface = iface  # QGIS interface hook

    def run(self):
        # Creates dialog only once (lazy initialization)
        if self.first_start:
            self.dlg = GeoCodexDialog()
        self.dlg.show()
```

### 3.2 UI Controller: `geo_codex_dialog.py`

The main dialog window with **three tabs**:

| Tab                | Purpose                         | Key Methods                                               |
| ------------------ | ------------------------------- | --------------------------------------------------------- |
| **Configuration**  | LLM & Database setup            | `on_test_connections_click()`                             |
| **Ask Data (SQL)** | Direct NL→SQL queries           | `on_generate_sql_click()`, `on_execute_sql_click()`       |
| **GeoCodex Chat**  | Conversational + Image analysis | `on_send_message_click()`, `on_run_sql_from_chat_click()` |

#### Async Threading Pattern

The dialog uses `QThread`-based workers to prevent UI freezing:

```python
class AsyncWorker(QThread):
    """Worker thread for async operations"""
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.signals = WorkerSignals()  # finished, error, progress

    def run(self):
        result = self.func(*self.args, **self.kwargs)
        self.signals.finished.emit(success, result)
```

#### Configuration Management

- **Dual-Model Configuration**: Users can configure separate models for Interpreter (vision) and Coder (SQL)
- **`useSameModelCheckbox`**: When checked, uses the same model for both roles
- Model dropdowns auto-populate based on selected provider

```python
def _get_interpreter_config(self) -> dict:
    return {
        "provider": self.interpreterProviderCombo.currentText(),
        "api_key": self.interpreterApiKeyInput.text(),
        "model_name": self.interpreterModelCombo.currentText(),
        "base_url": self.interpreterBaseUrlInput.text()
    }
```

### 3.3 Workflow Orchestrator: `orchestrator.py`

The **central brain** of the plugin. It coordinates all workflows and manages the dual-agent architecture.

#### Key Responsibilities:

1. **Create LLM Clients** on-demand for Interpreter and Coder roles
2. **Execute Workflows**: NL→SQL, Image→SQL, Chat with/without images
3. **Self-Healing SQL**: Automatic error correction with retry logic
4. **Layer Management**: Load query results as QGIS layers

#### Core Methods:

| Method                        | Workflow      | Description                                                 |
| ----------------------------- | ------------- | ----------------------------------------------------------- |
| `run_nl_to_sql_workflow()`    | NL→SQL        | Convert natural language to SQL (Coder only)                |
| `run_image_to_sql_workflow()` | Image→SQL     | Dual-agent: Interpreter extracts steps, Coder generates SQL |
| `run_chat_message()`          | Chat (text)   | Process text-only chat messages                             |
| `run_chat_with_image()`       | Chat (image)  | Dual-agent chat with schema-aware image analysis            |
| `run_sql_with_auto_fix()`     | Self-healing  | Execute SQL with automatic error correction                 |
| `run_sql_to_layer_workflow()` | Layer loading | Execute SQL and load results as QGIS layer                  |

#### Self-Healing SQL Algorithm:

```python
def run_sql_with_auto_fix(self, sql_query, layer_name, max_retries=3):
    current_sql = sql_query
    for attempt in range(max_retries + 1):
        success, result = self._try_execute_sql(current_sql, layer_name)

        if success:
            return True, result, current_sql

        # On failure, ask LLM to fix
        fixed_sql = self._fix_sql_with_llm(current_sql, result, schema_info)
        current_sql = fixed_sql

    return False, "Failed after all retries", current_sql
```

---

## 4. Workflow Pipelines

### 4.1 Natural Language → SQL Pipeline

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   User Query    │────▶│    DBConnector    │────▶│  Schema Info    │
│ "Find hospitals │     │ get_schema_info() │     │ (tables/columns)│
│  within 5mi of  │     └───────────────────┘     └────────┬────────┘
│  flood zones"   │                                        │
└─────────────────┘                                        │
                                                           ▼
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│  Clean SQL      │◀────│   Coder LLM       │◀────│  PromptBuilder  │
│  (PostGIS)      │     │  generate_response│     │ build_sql_prompt│
└─────────────────┘     └───────────────────┘     └─────────────────┘
```

**Code Flow:**

```python
def run_nl_to_sql_workflow(self, user_query):
    # 1. Get database schema
    schema_info = DBConnector(**db_params).get_schema_info()

    # 2. Build expert prompt with schema context
    prompt = prompt_builder.build_sql_prompt(user_query, schema_info)

    # 3. Generate SQL using Coder LLM
    sql = self._create_coder_client().generate_response(prompt)

    return True, clean_sql(sql)
```

### 4.2 Image → SQL Pipeline (Dual-Agent)

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   User Image    │────▶│   ImageUtils      │────▶│  Base64 Image   │
│  (workflow      │     │ encode_to_base64()│     │                 │
│   diagram)      │     └───────────────────┘     └────────┬────────┘
└─────────────────┘                                        │
                                                           ▼
                              ┌─────────────────────────────────────┐
                              │        INTERPRETER AGENT            │
                              │  (Vision LLM - e.g., GPT-4o)        │
                              │                                     │
                              │  • Analyzes image content           │
                              │  • Extracts workflow steps          │
                              │  • Maps to database schema          │
                              │  • Identifies spatial operations    │
                              └──────────────┬──────────────────────┘
                                             │
                                             ▼
                              ┌─────────────────────────────────────┐
                              │          CODER AGENT                │
                              │  (SQL LLM - e.g., DeepSeek)         │
                              │                                     │
                              │  • Receives workflow steps          │
                              │  • Has full schema context          │
                              │  • Generates PostGIS SQL            │
                              │  • Applies DE-9IM if needed         │
                              └──────────────┬──────────────────────┘
                                             │
                                             ▼
                              ┌─────────────────────────────────────┐
                              │       FINAL SQL OUTPUT              │
                              │  Optimized PostGIS query            │
                              └─────────────────────────────────────┘
```

### 4.3 Chat with Image Pipeline

This is the most sophisticated workflow:

````python
def run_chat_with_image(self, message, image_path, chat_history):
    # 1. Encode image
    base64_image = image_utils.encode_image_to_base64(image_path)

    # 2. Get database schema for BOTH agents
    schema_info = DBConnector(**db_params).get_schema_info()

    # 3. INTERPRETER AGENT - Schema-aware image analysis
    interpreter_prompt = f"""
    DATABASE SCHEMA: {schema_info}

    YOUR TASK - Analyze the image and create DETAILED MAPPING:
    - Identify criteria and map to actual table/column names
    - Determine spatial operations needed
    - Specify logical flow of operations
    """

    image_analysis = interpreter_client.generate_vision_response(
        interpreter_prompt, base64_image
    )

    # 4. CODER AGENT - SQL generation from mapped analysis
    sql_prompt = prompt_builder.build_sql_prompt(
        f"Generate SQL based on: {image_analysis}\nUser request: {message}",
        schema_info
    )

    sql_response = coder_client.generate_response(sql_prompt)

    return True, f"{image_analysis}\n\n```sql\n{sql}\n```"
````

### 4.4 Self-Healing SQL Pipeline

```
┌─────────────────┐
│   Execute SQL   │
└────────┬────────┘
         │
         ▼
    ┌────────────┐
    │  Success?  │───Yes───▶ Load as QGIS Layer ✓
    └────────────┘
         │No
         ▼
┌─────────────────┐
│ Capture Error   │
│ Message         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌───────────────────┐
│   Coder LLM     │────▶│   Fixed SQL       │
│ _fix_sql_with_  │     │                   │
│ llm()           │     └────────┬──────────┘
└─────────────────┘              │
                                 │
    ┌────────────────────────────┘
    │
    ▼
┌──────────────────┐
│ Retry Count < 3? │───No───▶ Return Failure
└──────────────────┘
    │Yes
    └───────────────▶ Loop back to Execute SQL
```

---

## 5. Data Flow Diagrams

### 5.1 Complete Message Processing Flow

```
User Input (Text/Image)
         │
         ▼
┌─────────────────────────┐
│   GeoCodexDialog        │
│   (UI Controller)       │
│   • Captures input      │
│   • Manages chat state  │
│   • Creates AsyncWorker │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   AsyncWorker Thread    │
│   • Runs in background  │
│   • Emits signals       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  WorkflowOrchestrator   │
│  • Routes to workflow   │
│  • Manages agents       │
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌─────────┐   ┌───────────┐
│Interpret│   │   Coder   │
│  Agent  │   │   Agent   │
└────┬────┘   └─────┬─────┘
     │              │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────┐
│     SQL Result          │
│     or Error            │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Signal: finished      │
│   Back to UI thread     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Update Chat Display   │
│   Show SQL Panel        │
│   Enable Execute Button │
└─────────────────────────┘
```

### 5.2 Database Schema Discovery

```
┌─────────────────────────┐
│     DBConnector         │
│     get_schema_info()   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ Query: Get all non-system schemas       │
│                                         │
│ SELECT schema_name FROM schemata        │
│ WHERE schema_name NOT IN                │
│   ('pg_catalog', 'information_schema')  │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ For each schema:                        │
│   Query: Get tables and columns         │
│                                         │
│   SELECT table_name, column_name,       │
│          data_type                      │
│   FROM information_schema.columns       │
│   WHERE table_schema = {schema}         │
└───────────┬─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────┐
│ Output Format:                          │
│                                         │
│ --- Schema: public ---                  │
│ Table 'public.cities' has columns:      │
│   (id (integer), name (varchar),        │
│    geom (geometry), pop (integer))      │
│                                         │
│ Table 'public.roads' has columns: ...   │
└─────────────────────────────────────────┘
```

---

## 6. Module Reference

### 6.1 `geo_codex_logic/core/llm_client.py`

**Purpose**: Unified facade for all LLM interactions

| Method                            | Parameters                                      | Returns            | Description                     |
| --------------------------------- | ----------------------------------------------- | ------------------ | ------------------------------- |
| `__init__`                        | `provider`, `api_key`, `model_name`, `base_url` | -                  | Initialize client               |
| `test_connection()`               | -                                               | `Tuple[bool, str]` | Test API connectivity           |
| `generate_response()`             | `prompt: str`                                   | `str`              | Text-only generation            |
| `generate_vision_response()`      | `prompt: str`, `base64_image: str`              | `str`              | Vision+text generation          |
| `get_workflow_steps_from_image()` | `base64_image: str`                             | `str`              | Extract GIS workflow from image |

### 6.2 `geo_codex_logic/core/llm_provider.py`

**Purpose**: Provider-specific client implementations and factory pattern

#### Enums and Data Classes:

```python
class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    NVIDIA = "nvidia"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"

@dataclass
class ModelConfig:
    provider: LLMProvider
    model_name: str
    api_key: Optional[str]
    base_url: Optional[str]
    temperature: float = 0.1
    max_tokens: int = 8192
```

#### Provider Client Classes:

| Class              | Provider   | Dependencies                                    |
| ------------------ | ---------- | ----------------------------------------------- |
| `OpenAIClient`     | OpenAI     | `langchain_openai.ChatOpenAI`                   |
| `AnthropicClient`  | Anthropic  | `langchain_anthropic.ChatAnthropic`             |
| `GeminiClient`     | Google     | `langchain_google_genai.ChatGoogleGenerativeAI` |
| `NVIDIAClient`     | NVIDIA NIM | `langchain_nvidia_ai_endpoints.ChatNVIDIA`      |
| `OpenRouterClient` | OpenRouter | `langchain_openai.ChatOpenAI` (custom base_url) |
| `OllamaClient`     | Ollama     | `langchain_ollama.ChatOllama`                   |

#### Factory Function:

```python
def create_llm_client(config: ModelConfig) -> BaseLLMClient:
    client_map = {
        LLMProvider.OPENAI: OpenAIClient,
        LLMProvider.ANTHROPIC: AnthropicClient,
        # ... etc
    }
    client = client_map[config.provider](config)
    client.initialize()
    return client
```

### 6.3 `geo_codex_logic/core/db_connector.py`

**Purpose**: PostgreSQL/PostGIS database interactions

| Method              | Parameters                                   | Returns            | Description                                  |
| ------------------- | -------------------------------------------- | ------------------ | -------------------------------------------- |
| `__init__`          | `host`, `port`, `dbname`, `user`, `password` | -                  | Store connection params                      |
| `test_connection()` | -                                            | `Tuple[bool, str]` | Verify database connectivity                 |
| `get_schema_info()` | -                                            | `str`              | Fetch all tables/columns as formatted string |

### 6.4 `geo_codex_logic/utils/prompt_builder.py`

**Purpose**: Construct expert prompts for LLM

| Function                        | Purpose                                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------ |
| `build_sql_prompt()`            | Main SQL generation prompt with DE-9IM reference, distance conversions, CRS handling |
| `build_sql_from_steps_prompt()` | Convert workflow steps to SQL (for image pipeline)                                   |
| `build_chat_sql_prompt()`       | Conversational SQL generation with context                                           |

### 6.5 `geo_codex_logic/utils/image_utils.py`

**Purpose**: Image processing utilities

| Function                   | Purpose                                  |
| -------------------------- | ---------------------------------------- |
| `encode_image_to_base64()` | Read image file and return Base64 string |

---

## 7. LLM Provider Integration

### 7.1 Provider Configuration Matrix

| Provider   | Base URL                              | Requires API Key | Vision Support    | Notes                          |
| ---------- | ------------------------------------- | ---------------- | ----------------- | ------------------------------ |
| OpenAI     | `https://api.openai.com/v1`           | ✅               | ✅ GPT-4o/4-turbo | Best overall quality           |
| Anthropic  | `https://api.anthropic.com`           | ✅               | ✅ Claude 3+      | Excellent reasoning            |
| Gemini     | (Google SDK)                          | ✅               | ✅ Gemini Pro     | Fast & cost-effective          |
| NVIDIA     | `https://integrate.api.nvidia.com/v1` | ✅               | ✅ Mistral/Llama  | Enterprise-grade, SSL handling |
| OpenRouter | `https://openrouter.ai/api/v1`        | ✅               | ✅ Multiple       | Unified API access             |
| Ollama     | `http://localhost:11434`              | ❌               | ✅ LLaVA          | Local/private deployment       |

### 7.2 Model Selection Strategy

The plugin uses different models for different roles:

**Vision Models (Interpreter)**: Optimized for image understanding

- OpenAI: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- Anthropic: `claude-sonnet-4-*`, `claude-3-5-sonnet-*`, `claude-3-opus-*`
- NVIDIA: `mistralai/mistral-medium-3-instruct`, `meta/llama-3.2-90b-vision-instruct`

**Code Models (Coder)**: Optimized for SQL generation

- OpenAI: `gpt-4o`, `gpt-3.5-turbo`
- Anthropic: `claude-sonnet-4-*`, `claude-3-5-sonnet-*`
- NVIDIA: `deepseek-ai/deepseek-v3.1`, `qwen/qwen2.5-coder-32b-instruct`

### 7.3 Vision API Pattern

All providers follow a similar pattern for vision requests:

```python
# OpenAI/NVIDIA/OpenRouter pattern
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
    ]
}]
response = self.client.invoke(messages)

# Anthropic/Gemini pattern (using LangChain HumanMessage)
from langchain_core.messages import HumanMessage
message = HumanMessage(content=[
    {"type": "text", "text": prompt},
    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
])
response = self.client.invoke([message])
```

---

## 8. Prompt Engineering

### 8.1 SQL Generation Prompt Structure

The prompts in `prompt_builder.py` follow a structured format:

```
═══════════════════════════════════════════════════════════════════════════════
CRITICAL ANALYSIS METHODOLOGY - FOLLOW THIS PROCESS:
═══════════════════════════════════════════════════════════════════════════════

STEP 1: DECOMPOSE THE PROBLEM
- Identify ALL criteria
- Categorize by table
- Determine operation order

STEP 2: IDENTIFY SPATIAL RELATIONSHIPS
- "within X miles" → ST_DWithin()
- "intersects" → ST_Intersects()
- etc.

STEP 3: HANDLE COORDINATE SYSTEMS
- Transform to projected CRS for distance calculations
- ST_Transform(geom, 2163) for USA

STEP 4: BUILD INCREMENTALLY WITH CTEs
- Use WITH clauses for complex queries

STEP 5: VERIFY LOGIC
- Ensure ALL criteria included
- Use DISTINCT if needed

═══════════════════════════════════════════════════════════════════════════════
SPATIAL ANALYSIS PATTERNS:
═══════════════════════════════════════════════════════════════════════════════
[Pattern examples with code]

═══════════════════════════════════════════════════════════════════════════════
DE-9IM REFERENCE:
═══════════════════════════════════════════════════════════════════════════════
[Full DE-9IM matrix explanation and common patterns]

═══════════════════════════════════════════════════════════════════════════════
DATABASE SCHEMA:
═══════════════════════════════════════════════════════════════════════════════
{schema_info}

═══════════════════════════════════════════════════════════════════════════════
USER'S REQUEST:
═══════════════════════════════════════════════════════════════════════════════
{user_query}
```

### 8.2 Key Prompt Techniques

1. **Schema Context Injection**: Always include full database schema so LLM knows exact table/column names

2. **Distance Conversion Reference**: Embedded conversion table (1 mile = 1609.34m)

3. **CRS Handling Guidelines**: Explicit instructions to transform to projected CRS

4. **DE-9IM Reference**: Full topological relationship patterns

5. **Critical Geometry Requirement**:

   ```
   CRITICAL: ALWAYS include geometry column (named 'geom') in final SELECT
   ```

6. **Anti-Pattern Warnings**:
   ```
   Do NOT reference temporary layers like "GeoCodex Query Result"
   ```

### 8.3 Self-Healing Fix Prompt

When SQL fails, a specialized prompt is constructed:

````python
fix_prompt = f"""
You are a PostGIS/PostgreSQL expert. Fix the following SQL query.

DATABASE SCHEMA:
{schema_info}

FAILED SQL QUERY:
```sql
{failed_sql}
````

ERROR MESSAGE:
{error_msg}

COMMON FIXES TO CONSIDER:

- "Layer is invalid" = MISSING GEOMETRY COLUMN
- Column name typos
- Wrong geometry column name
- Data type mismatches
- Missing schema prefix

OUTPUT: Return ONLY the corrected SQL wrapped in `sql` blocks.
"""

```

---

## Summary

GeoCodex is a sophisticated QGIS plugin built on these key principles:

1. **Dual-Agent Architecture**: Separates vision understanding (Interpreter) from code generation (Coder) for optimal results

2. **Provider Agnostic**: Unified abstraction layer supports 6 LLM providers with consistent API

3. **Self-Healing**: Automatic SQL error correction with intelligent retry logic

4. **Schema-Aware**: All prompts include full database schema for accurate table/column references

5. **Async UI**: Non-blocking operations using QThread workers

6. **Expert Prompting**: Comprehensive prompts with spatial analysis patterns, DE-9IM references, and CRS handling guidelines

The modular architecture (`geo_codex_logic/`) cleanly separates concerns:
- **Core**: LLM client abstraction and database connectivity
- **Utils**: Prompt engineering and image processing
- **Orchestrator**: Workflow coordination and business logic
- **UI**: PyQt5 dialog with async operation handling
```
