**Ask a Question – AI Automatically Decomposes, Processes in Parallel, and Generates a Final Integrated Report**

### Features

- **Intelligent Topic Decomposition**: Analyzes the topic from multiple perspectives to ensure comprehensive understanding
- **Parallel Processing**: Handles multiple subtopics simultaneously to improve efficiency
- **Resource Tracking**: Records API usage
- **Automatic Saving**: All conversation history is saved automatically

---

### Installation Requirements

```bash
bash
复制编辑
pip install -r requirements.txt

```

---

### Configuration

In `config.py`, configure your API key. You must remove the `.example` extension from `config.example.py`:

```python
python
复制编辑
API_BASE_URL = "Your API base URL"
API_KEY = "Your API key"

```

**Optional**: Configure a second API account to improve parallel processing efficiency:

```python
python
复制编辑
RESEARCH_API_BASE_URL = "Second API base URL"
RESEARCH_API_KEY = "Second API key"

```

---

### Model Configuration

In `config.py`, you can configure which models are used in each stage:

```python
python
复制编辑
WORKFLOW_STAGES = {
    'decomposition': "deepseek-ai/deepseek-r1",  # Topic decomposition stage
    'research': "deepseek-ai/deepseek-r1",       # Content research stage
    'verification': "deepseek-ai/deepseek-r1",   # Verification stage
    'scoring': "deepseek-ai/deepseek-r1"         # Scoring stage
}

```

---

### How to Use

Start a new conversation:

```bash
bash
复制编辑
python main.py

```

Input your topic of interest, for example:

```
pgsql
复制编辑
Enter the topic you want to learn about: Explain virtual currencies in detail
Your current knowledge of the topic: I only know Dogecoin is a meme coin, and Bitcoin is called digital gold, but I don't know why
Your learning goal: I want to understand what I’m buying and what affects its price before investing

```

The system will automatically:

1. Decompose the topic into multiple subtopics
2. Process each subtopic in parallel
3. Generate a final integrated report

---

### Output Files

- `output/[timestamp]/final_report.md`: Final report
- `output/[timestamp]/decomposition_structure.json`: Topic decomposition structure
- `output/[timestamp]/*.txt`: Detailed processing logs

Final result showcase:

[https://sorrow233.notion.site/197c238567d3809abd1eca3d5eeb98ac](https://www.notion.so/197c238567d3809abd1eca3d5eeb98ac?pvs=21)

---

### Directory Structure

```
bash
复制编辑
.
├── main.py              # Main program entry
├── config.py            # Configuration file
├── modules/             # Core modules
│   ├── decomposer.py    # Topic decomposer
│   ├── researcher.py    # Content researcher
│   ├── evaluator.py     # Quality evaluator
│   └── api_client.py    # API client
├── utils/               # Utility functions
│   ├── file_utils.py    # File operations
│   └── resource_tracker.py  # Resource tracker
└── output/              # Output directory

```

---

### Advanced Features

- **Resume Previous Session** (Continue after research is completed):

```bash
bash
复制编辑
python continue.py

```

- **Track API Usage**:
    
    View `API_usage_summary.txt` for cumulative usage statistics
    
- **Custom Branches**:
    
    Add custom focus points during topic decomposition
    

---

### Notes

- Ensure your API keys are correctly configured. `config.example.py` is only a sample; the `.example` must be removed.
- It is recommended to back up the `output` directory regularly.

---

### FAQ

**Q: How can I modify the number of parallel tasks?**

**A:** Adjust the `MAX_CONCURRENT_TASKS` parameter in `config.py`.
