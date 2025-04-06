# Vue-to-React Converter

A code conversion agent based on the OpenAI Agents Python SDK that converts Vue.js components to React components.

## Features

- Specify source and destination folders for code conversion
- Generate comprehensive documentation of all files in source directory
- Create a conversion plan based on component dependencies
- Support configurable batch sizes for conversion
- Automatically compare functionality before/after conversion
- Support multiple iterations of fixes if functionality differs
- Allow injecting knowledge bases to guide the conversion process
- Generate test reports highlighting areas needing special attention

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/vue-to-react-converter.git
cd vue-to-react-converter

# Install the package
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Basic usage
python main.py --source-dir /path/to/vue/components --destination-dir /path/to/output

# With custom batch size and knowledge base
python main.py --source-dir /path/to/vue/components --destination-dir /path/to/output --batch-size 10 --knowledge-base /path/to/knowledge_base.json
```

### Python API

```python
import asyncio
from src import convert_vue_to_react

async def main():
    report = await convert_vue_to_react(
        source_dir="/path/to/vue/components",
        destination_dir="/path/to/output",
        batch_size=5,
        knowledge_base_path="/path/to/knowledge_base.json",
        max_fix_iterations=3,
    )
    
    print(f"Total files: {report.total_files}")
    print(f"Successful conversions: {report.successful_conversions}")
    print(f"Partial conversions: {report.partial_conversions}")
    print(f"Failed conversions: {report.failed_conversions}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Architecture

The Vue-to-React converter is built using a multi-agent architecture:

1. **VueToReactConverter**: Main orchestrator for the conversion process
2. **FileAnalysisAgent**: Analyzes Vue files and generates documentation
3. **ConversionPlanningAgent**: Creates dependency-based conversion plan
4. **CodeConversionAgent**: Performs the actual code conversion
5. **ComparisonAgent**: Validates conversion results and suggests fixes
6. **KnowledgeBaseManager**: Manages conversion rules and patterns

## Conversion Process

1. **File Analysis**: Analyze all Vue components in the source directory
   - Extract component structure (template, script, style)
   - Identify props, data, computed properties, methods, lifecycle hooks
   - Document component functionality and dependencies

2. **Conversion Planning**: Create a plan for converting components
   - Build a dependency graph between components
   - Sort components based on dependencies
   - Group components into batches for conversion

3. **Code Conversion**: Convert Vue components to React
   - Convert template to JSX
   - Convert script to React hooks and functions
   - Convert style to CSS
   - Apply knowledge base rules

4. **Comparison and Validation**: Validate conversion results
   - Compare Vue and React components for functional equivalence
   - Identify issues and discrepancies
   - Apply fixes for identified issues

5. **Report Generation**: Generate a comprehensive report
   - Document conversion results for each component
   - Highlight areas needing special attention
   - Provide suggestions for manual fixes

## Knowledge Base

The knowledge base is a JSON file that contains rules for converting Vue to React:

```json
{
  "rules": [
    {
      "pattern": "v-if=\"([^\"]+)\"",
      "replacement": "{\\1 && ",
      "description": "Convert v-if to conditional rendering",
      "examples": {
        "before": "<div v-if=\"show\">Content</div>",
        "after": "{show && <div>Content</div>}"
      }
    }
  ],
  "lifecycle_mappings": {
    "created": "[]",
    "mounted": "[]"
  },
  "directive_mappings": {
    "v-if": "conditional rendering",
    "v-for": "map"
  },
  "special_cases": {
    "computed_properties": {
      "pattern": "computed:\\s*{(.*?)}",
      "replacement": "useMemo",
      "description": "Convert computed properties to useMemo"
    }
  }
}
```

## Testing

```bash
# Run tests
python -m unittest discover tests
```

## License

MIT
