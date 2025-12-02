# 🌍 GeoCodex - AI-Powered Spatial Analysis for QGIS

![GeoCodex Logo](icon.png)

**Transform natural language into powerful PostGIS spatial queries**

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [LLM Providers](#supported-llm-providers) • [Usage](#usage) • [Architecture](#architecture)

---

## 📋 Overview

**GeoCodex** is an intelligent QGIS plugin that bridges the gap between natural language and spatial database queries. Using state-of-the-art Large Language Models (LLMs), it enables GIS professionals to perform complex spatial analysis simply by describing what they want in plain English.

Whether you're a seasoned GIS analyst or a newcomer to spatial databases, GeoCodex empowers you to:

- 🗣️ **Ask questions in natural language** - "Find all hospitals within 10 miles of flood zones"
- 🖼️ **Analyze images** - Upload sketches, maps, or diagrams and get executable SQL
- 🔧 **Auto-fix SQL errors** - Self-healing queries that automatically correct mistakes
- 🗺️ **Visualize results** - Instantly load query results as QGIS layers

---

## ✨ Features

### 🎯 Core Capabilities

| Feature                        | Description                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------- |
| **Natural Language to SQL**    | Convert plain English questions into optimized PostGIS queries                  |
| **Multi-Provider LLM Support** | Choose from OpenAI, Anthropic, Google Gemini, NVIDIA, OpenRouter, or Ollama     |
| **Dual-Agent Architecture**    | Separate vision and coding models for optimal performance                       |
| **Image Analysis**             | Upload map sketches or diagrams for spatial query generation                    |
| **Self-Healing SQL**           | Automatic error detection and correction (up to 3 retry attempts)               |
| **Chat Interface**             | Conversational interaction with context-aware responses                         |
| **DE-9IM Support**             | Advanced topological analysis using Dimensionally Extended 9-Intersection Model |

### 🔬 Advanced Spatial Analysis

GeoCodex understands complex spatial relationships:

- **Proximity Analysis**: "within X miles/km", "near", "close to"
- **Topological Relations**: intersects, contains, within, touches, overlaps, crosses
- **DE-9IM Patterns**: Precise topology with `ST_Relate()` for advanced use cases
- **Multi-Criteria Selection**: Combine spatial and attribute filters seamlessly
- **Coordinate System Handling**: Automatic transformation for accurate distance calculations

---

## 🚀 Installation

### Prerequisites

- **QGIS 3.0+** (tested on QGIS 3.28+)
- **PostgreSQL/PostGIS** database with spatial data
- **API Key** from at least one supported LLM provider

### Install from Plugin Manager

1. Open QGIS
2. Navigate to `Plugins` → `Manage and Install Plugins`
3. Search for "GeoCodex"
4. Click `Install`

### Install from ZIP

1. Download the latest release from [GitHub Releases](https://github.com/AmroEid77/GeoCodex/releases)
2. In QGIS: `Plugins` → `Manage and Install Plugins` → `Install from ZIP`
3. Select the downloaded ZIP file
4. Restart QGIS

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/AmroEid77/GeoCodex.git

# Copy to QGIS plugins directory
# Windows:
copy -r GeoCodex "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\geo_codex"

# Linux:
cp -r GeoCodex ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/geo_codex

# macOS:
cp -r GeoCodex ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/geo_codex
```

---

## 🔑 Supported LLM Providers

GeoCodex supports multiple LLM providers, giving you flexibility in cost, performance, and privacy:

| Provider          | Vision Models                                     | Code Models                               | Notes                    |
| ----------------- | ------------------------------------------------- | ----------------------------------------- | ------------------------ |
| **OpenAI**        | GPT-4o, GPT-4o-mini, GPT-4-turbo                  | GPT-4o, GPT-4o-mini, GPT-3.5-turbo        | Best overall quality     |
| **Anthropic**     | Claude Sonnet 4, Claude 3.5 Sonnet, Claude 3 Opus | Claude Sonnet 4, Claude 3.5 Sonnet        | Excellent reasoning      |
| **Google Gemini** | Gemini 2.0 Flash, Gemini 1.5 Pro                  | Gemini 2.0 Flash, Gemini 1.5 Pro          | Fast & cost-effective    |
| **NVIDIA NIM**    | Mistral Medium 3, Llama 3.2 Vision                | DeepSeek V3.1, Llama 3.3, Qwen 2.5 Coder  | Enterprise-grade         |
| **OpenRouter**    | Multiple providers                                | Multiple providers                        | Unified API access       |
| **Ollama**        | LLaVA, BakLLaVA, Moondream                        | CodeLlama, DeepSeek Coder, Qwen 2.5 Coder | Local/private deployment |

### Getting API Keys

- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com/)
- **Google Gemini**: [aistudio.google.com](https://aistudio.google.com/app/apikey)
- **NVIDIA NIM**: [build.nvidia.com](https://build.nvidia.com/)
- **OpenRouter**: [openrouter.ai/keys](https://openrouter.ai/keys)
- **Ollama**: No API key needed (local deployment)

---

## 🏃 Quick Start

### 1. Configure Database Connection

1. Open GeoCodex from the QGIS toolbar
2. Go to the **Settings** tab
3. Enter your PostgreSQL/PostGIS connection details:
   - Host, Port, Database name
   - Username and Password
4. Click **Test Connection**

### 2. Configure LLM Provider

1. Select your preferred **LLM Provider** (e.g., OpenAI)
2. Enter your **API Key**
3. Choose models for:
   - **Interpreter**: Vision-capable model for image analysis
   - **Coder**: Model optimized for SQL generation
4. Click **Test Connections** to verify

### 3. Start Asking Questions!

**Tab 1: Ask Data** - Direct natural language queries

```
"Show me all parks larger than 100 acres within 5 miles of schools"
```

**Tab 2: GeoCodex Chat** - Conversational interface with image support

```
"I need to find optimal locations for new fire stations based on population density"
[Attach image of current station layout]
```

---

## 📖 Usage

### Ask Data Tab

The simplest way to query your spatial database:

1. Type your question in natural language
2. Click **Generate SQL** to see the query
3. Review and modify if needed
4. Click **Execute SQL** to run and visualize results

**Example Questions:**

- "Find all buildings within flood zone A"
- "Which roads intersect with wetland areas?"
- "List hospitals more than 20km from any fire station"
- "Show parcels that touch the city boundary"

### GeoCodex Chat Tab

For complex, multi-step analysis with image support:

1. **Text-only queries**: Type your question and click Send
2. **Image + Text**: Click 📎 to attach an image, then describe what you need
3. **Execute SQL**: When SQL appears in the response, click **Run SQL** to execute

**The Dual-Agent Flow:**

1. **Interpreter Agent** (vision model) analyzes your image and extracts requirements
2. **Coder Agent** (SQL model) generates precise PostGIS queries based on the analysis

### Self-Healing SQL

GeoCodex automatically attempts to fix SQL errors:

1. If a query fails, the error is sent back to the LLM
2. The LLM analyzes the error and generates a corrected query
3. Up to 3 automatic retry attempts
4. All attempts are logged in the chat for transparency

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GeoCodex Plugin                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │   Ask Data  │  │   GeoCodex  │  │   Settings  │    UI Layer     │
│  │     Tab     │  │   Chat Tab  │  │     Tab     │                  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘                  │
│         │                │                                           │
│         └────────┬───────┘                                           │
│                  ▼                                                   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                 WorkflowOrchestrator                          │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                     │  │
│  │  │   Interpreter   │  │     Coder       │                     │  │
│  │  │  (Vision Model) │  │  (SQL Model)    │                     │  │
│  │  └────────┬────────┘  └────────┬────────┘                     │  │
│  └───────────┼────────────────────┼──────────────────────────────┘  │
│              │                    │                                  │
│              ▼                    ▼                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                      LLMClient                                │  │
│  │  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ │  │
│  │  │ OpenAI  │ │Anthropic │ │ Gemini │ │ NVIDIA │ │  Ollama  │ │  │
│  │  └─────────┘ └──────────┘ └────────┘ └────────┘ └──────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     DBConnector                               │  │
│  │              PostgreSQL / PostGIS Database                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component             | Description                                  |
| --------------------- | -------------------------------------------- |
| `geo_codex_dialog.py` | Main UI controller with async threading      |
| `orchestrator.py`     | Workflow management, dual-agent coordination |
| `llm_client.py`       | Unified interface to all LLM providers       |
| `llm_provider.py`     | Provider configurations and model catalogs   |
| `prompt_builder.py`   | Expert prompts for SQL generation            |
| `db_connector.py`     | PostgreSQL/PostGIS database operations       |
| `image_utils.py`      | Image processing for vision models           |

---

## 🔧 Configuration

### Environment Variables (Optional)

You can set API keys via environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export NVIDIA_API_KEY="nvapi-..."
export OPENROUTER_API_KEY="sk-or-..."
```

### Database Connection String

GeoCodex uses standard PostgreSQL connection parameters:

```
Host: localhost
Port: 5432
Database: gis_database
User: postgres
Password: ****
```

---

## 📚 Examples

### Basic Proximity Query

```
User: "Find all hospitals within 5 miles of parks"

Generated SQL:
WITH hospitals_proj AS (
  SELECT *, ST_Transform(geom, 2163) as geom_proj FROM hospitals
),
parks_proj AS (
  SELECT *, ST_Transform(geom, 2163) as geom_proj FROM parks
)
SELECT DISTINCT h.*, h.geom
FROM hospitals_proj h
WHERE EXISTS (
  SELECT 1 FROM parks_proj p
  WHERE ST_DWithin(h.geom_proj, p.geom_proj, 8046.72)
);
```

### Advanced DE-9IM Topology

```
User: "Find parcels that share exactly a boundary edge with the flood zone (no interior overlap)"

Generated SQL:
SELECT p.*, p.geom
FROM parcels p, flood_zones f
WHERE ST_Relate(p.geom, f.geom, 'FF2F11212');
```

### Multi-Criteria Site Selection

```
User: "Find vacant lots larger than 2 acres, within 1km of transit stations, and outside flood zones"

Generated SQL:
WITH vacant_lots AS (
  SELECT * FROM parcels
  WHERE land_use = 'vacant' AND ST_Area(geom) > 8093.71
),
near_transit AS (
  SELECT v.* FROM vacant_lots v
  WHERE EXISTS (
    SELECT 1 FROM transit_stations t
    WHERE ST_DWithin(ST_Transform(v.geom, 2163), ST_Transform(t.geom, 2163), 1000)
  )
)
SELECT n.*, n.geom FROM near_transit n
WHERE NOT EXISTS (
  SELECT 1 FROM flood_zones f WHERE ST_Intersects(n.geom, f.geom)
);
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the GPL v2 License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Amro Eid** - _Initial work & Development_ - [AmroEid77](https://github.com/AmroEid77)
- **Ahmad** - _Contributor_

---

## 🙏 Acknowledgments

- QGIS Development Team
- PostGIS Community
- LangChain for LLM abstractions
- All the amazing LLM providers

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/AmroEid77/GeoCodex/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AmroEid77/GeoCodex/discussions)
- **Email**: amro.eidd@gmail.com

---

Made with ❤️ for the GIS Community
