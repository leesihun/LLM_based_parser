# LLM-based Review Parser - Usage Guide

A complete system for processing cellphone reviews from Excel files using local LLM models via Ollama.

## 🚀 Quick Start Guide

### Step 1: Prerequisites

**Install Ollama:**
1. Download and install Ollama from [https://ollama.ai](https://ollama.ai)
2. Start Ollama service (it should run on `localhost:11434`)

**Download Required Models:**
```bash
ollama pull gemma3:12b
ollama pull nomic-embed-text:latest
```

**Install Python Dependencies:**
```bash
pip install pandas openpyxl ollama
```

### Step 2: Prepare Your Data

1. Place your Excel files (`.xlsx`) in the `data/` folder
2. Files should contain reviews in columns (like your current `폴드긍정.xlsx` and `폴드부정.xlsx`)
3. The system automatically detects sentiment from filenames:
   - Files with "긍정" or "positive" → positive reviews
   - Files with "부정" or "negative" → negative reviews

### Step 3: Run the System

**Complete Processing Pipeline:**
```bash
python enhanced_main.py --mode pipeline
```

This will:
- Read all Excel files from `data/` folder
- Detect languages (Korean, English, etc.)
- Translate non-English reviews to English
- Correct spelling errors
- Generate a consolidated markdown file
- Set up the query system

**Expected Output:**
```
✅ Pipeline completed successfully!
📄 Markdown file: output/consolidated_reviews_20250807_143022.md
📊 Total reviews: 200
⏱️  Processing time: 45.23s
📈 Sentiment distribution: {'positive': 100, 'negative': 100}
```

### Step 4: Ask Questions

After the pipeline completes, you can ask questions:

```bash
python enhanced_main.py --mode query --question "How many responses are good and how many are bad?"
```

```bash
python enhanced_main.py --mode query --question "What keyword is used most often? Semantically analyze it."
```

```bash
python enhanced_main.py --mode query --question "Give me an example of good review regarding screen size."
```

## 📋 Supported Question Types

The system is specifically designed to handle these question types:

### 1. Count Analysis
- "How many responses are good and how many are bad?"
- "What's the ratio of positive to negative reviews?"

### 2. Keyword Analysis
- "What keyword is used most often? How many times was it mentioned?"
- "What are the most common words in positive reviews?"
- "Semantically analyze the review keywords"

### 3. Example Requests
- "Give me an example of good review regarding screen size"
- "Give me an example of bad review regarding screen time"
- "Show me a positive review about battery life"
- "Find a negative review about camera quality"

### 4. General Analysis
- "What are the main complaints in negative reviews?"
- "What do users like most about the phone?"
- "Analyze the sentiment patterns in the reviews"

## ⚙️ Configuration Options

### Environment Variables
```bash
export LLM_MODEL="gemma3:12b"                    # Main LLM model
export EMBEDDING_MODEL="nomic-embed-text:latest" # Embedding model
export OLLAMA_HOST="localhost:11434"             # Ollama service address
export DEFAULT_TEMPERATURE="0.4"                 # Response creativity (0.0-1.0)
export MAX_TOKENS="10000"                        # Maximum response length
export DATA_DIRECTORY="data"                     # Input folder
export OUTPUT_DIRECTORY="output"                 # Output folder
```

### Config File
Edit `config/enhanced_config.py` to customize settings:

```python
# Model settings
self.llm_model = "gemma3:12b"
self.embedding_model = "nomic-embed-text:latest"

# Processing settings
self.default_temperature = 0.4
self.translation_temperature = 0.3
self.batch_size = 10
```

## 📁 File Structure

```
LLM_based_parser/
├── enhanced_main.py              # Main program
├── config/
│   └── enhanced_config.py        # Configuration settings
├── src/
│   ├── enhanced_excel_reader.py  # Excel file processor
│   ├── enhanced_ollama_client.py # LLM communication
│   ├── markdown_generator.py     # Output file creator
│   └── enhanced_query_engine.py  # Question answering
├── data/                         # Your Excel files go here
│   ├── 폴드긍정.xlsx
│   └── 폴드부정.xlsx
├── output/                       # Generated files appear here
└── README.md
```

## 🔍 Understanding the Output

The system generates a comprehensive markdown file in the `output/` folder:

**Sections include:**
- **Dataset Statistics**: Count of reviews by sentiment, language, source file
- **Keyword Analysis**: Most frequent words in positive/negative reviews
- **Review Collection**: All processed reviews with metadata
  - Original text (if non-English)
  - English translation
  - Language detection results
  - Topic tags (screen, battery, camera, etc.)
  - Sentiment classification

## 💡 Usage Examples

### Basic Workflow
```bash
# 1. Process all Excel files
python enhanced_main.py --mode pipeline

# 2. Ask questions about the data
python enhanced_main.py --mode query --question "How many good vs bad reviews?"

# 3. Get specific examples
python enhanced_main.py --mode query --question "Show me a bad review about battery"
```

### Test Mode
```bash
# Run all sample questions automatically
python enhanced_main.py --mode test
```

### Custom Questions
```bash
python enhanced_main.py --mode query --question "What are users saying about the folding mechanism?"

python enhanced_main.py --mode query --question "Compare positive and negative sentiment patterns"

python enhanced_main.py --mode query --question "Find reviews mentioning durability issues"
```

## 🛠️ Troubleshooting

### Common Issues

**1. "Connection refused" error**
- Make sure Ollama is running: check `http://localhost:11434` in browser
- Restart Ollama service if needed

**2. "Model not found" error**
```bash
ollama pull gemma3:12b
ollama pull nomic-embed-text:latest
```

**3. "No reviews found" error**
- Check that Excel files are in the `data/` folder
- Verify Excel files contain data (not empty)
- Check file permissions

**4. Slow processing**
- Reduce batch size in config: `self.batch_size = 5`
- Use smaller model if needed: `self.llm_model = "gemma:7b"`

### Performance Tips

- **Large datasets**: Processing 200+ reviews may take 5-10 minutes
- **Memory usage**: Monitor system resources during processing
- **Model switching**: You can use different models by changing config
- **Parallel processing**: System processes reviews in batches for efficiency

## 🔧 Advanced Usage

### Using Specific Markdown File
```bash
python enhanced_main.py --mode query --markdown "output/my_reviews.md" --question "Your question"
```

### Custom Processing
```python
from enhanced_main import EnhancedPipeline

pipeline = EnhancedPipeline()
result = pipeline.run_complete_pipeline()

# Ask multiple questions
questions = [
    "How many good vs bad reviews?",
    "What's the most mentioned keyword?",
    "Show me a screen size example"
]

for q in questions:
    answer = pipeline.query_engine.query(q)
    print(f"Q: {q}")
    print(f"A: {answer['answer']}")
    print("---")
```

## 📊 Output Files

After running the pipeline, you'll find:

1. **`consolidated_reviews_[timestamp].md`** - Main dataset file with all processed reviews
2. **`processing_log.json`** - Processing statistics and metadata
3. **Log files** - Detailed processing logs in console

The markdown file is specifically formatted for LLM analysis and contains all the information needed to answer your questions accurately.

## ❓ Getting Help

If you encounter issues:

1. Check the console output for error messages
2. Verify Ollama is running and models are available
3. Ensure Excel files are properly formatted
4. Check the `processing_log.json` for detailed information

The system is designed to be robust and provide helpful error messages to guide you through any issues.