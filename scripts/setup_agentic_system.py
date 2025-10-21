#!/usr/bin/env python3
"""
Setup Script for Agentic Workflow System

This script sets up the new agentic architecture with minimal disruption.
"""

import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_agent_configuration():
    """Create agents.json configuration file."""
    print("Creating agent configuration...")

    config = {
        "agents": {
            "enabled": True,
            "default_agent_type": "json_analyzer",

            "react_engine": {
                "max_iterations": 15,
                "thought_temperature": 0.7,
                "action_temperature": 0.2,
                "enable_self_correction": True
            },

            "tools": {
                "numeric_summary": {
                    "enabled": True,
                    "max_sections": 20,
                    "max_child_items": 25
                },
                "pattern_detector": {
                    "enabled": True,
                    "correlation_threshold": 0.7
                },
                "comparator": {
                    "enabled": True
                },
                "calculator": {
                    "enabled": True,
                    "precision": 6
                },
                "validator": {
                    "enabled": True,
                    "default_tolerance": 0.01
                },
                "json_analyzer": {
                    "enabled": True
                }
            },

            "planning": {
                "enable_adaptive_planning": True,
                "use_memory_for_planning": True,
                "planning_temperature": 0.4
            },

            "memory": {
                "enabled": True,
                "short_term_size": 50,
                "long_term_storage": "./data/agent_memory",
                "enable_learning": True,
                "similarity_threshold": 0.75,
                "min_confidence_for_storage": 0.8
            },

            "validation": {
                "auto_validate_results": True,
                "confidence_threshold": 0.8
            }
        }
    }

    config_path = PROJECT_ROOT / "config" / "agents.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    print(f"✓ Created {config_path}")
    return config


def update_main_configuration():
    """Update main config.json with agent settings."""
    print("Updating main configuration...")

    config_path = PROJECT_ROOT / "config.json"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"⚠ Config file not found: {config_path}")
        return

    # Add agent configuration if not present
    if "agents" not in config:
        config["agents"] = {
            "enabled": True,
            "config_file": "./config/agents.json"
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✓ Updated {config_path}")
    else:
        print(f"  Agent configuration already exists in {config_path}")


def create_directory_structure():
    """Create necessary directory structure."""
    print("Creating directory structure...")

    directories = [
        "data/agent_memory",
        "logs",
        "config",
        "backend/api/v1",
        "backend/api/middleware",
        "backend/core/llm",
        "backend/core/agents",
        "backend/services/agents/tools",
        "backend/infrastructure/config",
        "backend/utils",
    ]

    for dir_path in directories:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

    print(f"✓ Created {len(directories)} directories")


def test_llm_client():
    """Test the new LLM client."""
    print("\nTesting new LLM client...")

    try:
        from backend.core.llm import LLMClient

        client = LLMClient()

        # Test health check
        if client.health_check():
            print("✓ LLM client connected successfully")
            print(f"  Model: {client.model}")
            print(f"  URL: {client.ollama_url}")
        else:
            print("⚠ LLM service not responding - make sure Ollama is running")

    except Exception as e:
        print(f"⚠ LLM client test failed: {e}")


def test_agent_system():
    """Test the agent system."""
    print("\nTesting agent system...")

    try:
        from backend.core.llm import LLMClient
        from backend.core.agents import BaseAgent, AgentConfig
        from backend.services.agents.tools import (
            NumericSummaryTool,
            CalculatorTool,
            ValidatorTool,
            JSONAnalyzerTool
        )

        # Create LLM client
        llm_client = LLMClient()

        # Create tools
        tools = [
            NumericSummaryTool(),
            CalculatorTool(),
            ValidatorTool(),
            JSONAnalyzerTool()
        ]

        # Create agent
        config = AgentConfig(max_iterations=5, enable_memory=False)  # Disable memory for test
        agent = BaseAgent(
            llm_client=llm_client,
            tools=tools,
            config=config
        )

        print(f"✓ Agent initialized with {len(tools)} tools")
        print(f"  Tools: {[tool.name for tool in tools]}")

        # Test with simple data
        test_data = {"values": [1, 5, 3, 9, 2, 7]}

        print("\n  Testing agent execution...")
        result = agent.execute(
            task="Find the maximum value",
            context={"json_data": test_data}
        )

        print(f"✓ Agent execution completed")
        print(f"  Answer: {result.answer[:100]}...")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Iterations: {len(result.execution_trace.steps)}")
        print(f"  Tools used: {list(result.execution_trace.get_tools_used())}")

    except Exception as e:
        print(f"⚠ Agent system test failed: {e}")
        import traceback
        traceback.print_exc()


def create_example_script():
    """Create an example usage script."""
    print("\nCreating example script...")

    example_code = '''#!/usr/bin/env python3
"""
Example: Using the Agentic System for JSON Analysis

This script demonstrates how to use the new agentic workflow system.
"""

from backend.core.llm import LLMClient
from backend.core.agents import BaseAgent, AgentConfig
from backend.services.agents.tools import (
    NumericSummaryTool,
    CalculatorTool,
    ValidatorTool,
    JSONAnalyzerTool
)

# Sample data - warpage analysis
warpage_data = {
    "materials": [
        {"id": "ABC123", "name": "Material A", "warpage": 0.45, "temp": 245},
        {"id": "XYZ789", "name": "Material B", "warpage": 1.23, "temp": 280},
        {"id": "DEF456", "name": "Material C", "warpage": 0.89, "temp": 260},
    ]
}

def main():
    print("=" * 60)
    print("Agentic JSON Analysis Example")
    print("=" * 60)

    # 1. Initialize LLM client
    print("\\n1. Initializing LLM client...")
    llm_client = LLMClient()
    print(f"   Model: {llm_client.model}")

    # 2. Create tools
    print("\\n2. Creating agent tools...")
    tools = [
        NumericSummaryTool(),
        CalculatorTool(),
        ValidatorTool(),
        JSONAnalyzerTool()
    ]
    print(f"   Tools: {[t.name for t in tools]}")

    # 3. Configure agent
    print("\\n3. Configuring agent...")
    config = AgentConfig(
        max_iterations=10,
        enable_memory=True,
        enable_planning=True,
        thought_temperature=0.7,
        action_temperature=0.2
    )

    # 4. Create agent
    print("\\n4. Creating agent...")
    agent = BaseAgent(
        llm_client=llm_client,
        tools=tools,
        config=config
    )

    # 5. Execute task
    print("\\n5. Executing analysis task...")
    print("   Task: Find material with lowest warpage and explain why")

    result = agent.execute(
        task="Which material has the lowest warpage and why?",
        context={"json_data": warpage_data}
    )

    # 6. Display results
    print("\\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\\nAnswer:\\n{result.answer}")
    print(f"\\nConfidence: {result.confidence:.2%}")
    print(f"\\nExecution Summary:")
    print(f"  - Iterations: {len(result.execution_trace.steps)}")
    print(f"  - Tools used: {list(result.execution_trace.get_tools_used())}")
    print(f"  - Execution time: {result.execution_time_ms:.2f}ms")

    if result.insights:
        print(f"\\nInsights:")
        for insight in result.insights:
            print(f"  - {insight}")

    # 7. Show execution trace
    print(f"\\nExecution Trace:")
    for step in result.execution_trace.steps:
        print(f"\\n  Iteration {step.iteration}:")
        print(f"    Thought: {step.thought[:100]}...")
        if step.action:
            print(f"    Action: {step.action.get('tool')}")
        print(f"    Success: {'✓' if not step.error else '✗'}")

if __name__ == "__main__":
    main()
'''

    example_path = PROJECT_ROOT / "scripts" / "example_agentic_usage.py"
    with open(example_path, 'w', encoding='utf-8') as f:
        f.write(example_code)

    print(f"✓ Created {example_path}")


def main():
    """Main setup function."""
    print("=" * 60)
    print("Agentic Workflow System Setup")
    print("=" * 60)

    # Step 1: Create directory structure
    create_directory_structure()

    # Step 2: Create configurations
    create_agent_configuration()
    update_main_configuration()

    # Step 3: Create example script
    create_example_script()

    # Step 4: Test systems
    test_llm_client()
    test_agent_system()

    print("\\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\\nNext steps:")
    print("  1. Review configuration in config/agents.json")
    print("  2. Run example: python scripts/example_agentic_usage.py")
    print("  3. Start server: python server.py")
    print("  4. Test API: curl http://localhost:8000/api/v1/agents/execute")
    print("\\nDocumentation:")
    print("  - docs/REFACTORING_GUIDE.md - Refactoring overview")
    print("  - docs/AGENTS.md - Agent system documentation")
    print("=" * 60)


if __name__ == "__main__":
    main()
'''

    setup_path = PROJECT_ROOT / "scripts" / "setup_agentic_system.py"
    with open(setup_path, 'w', encoding='utf-8') as f:
        f.write(__file__)

    print(f"✓ Created {setup_path}")


def create_example_script():
    """Create an example usage script."""
    print("\nCreating example script...")

    example_code = """#!/usr/bin/env python3
# Example script created above
"""

    example_path = PROJECT_ROOT / "scripts" / "example_agentic_usage.py"
    with open(example_path, 'w', encoding='utf-8') as f:
        f.write(example_code)

    print(f"✓ Created {example_path}")


def main():
    """Main setup function."""
    print("=" * 60)
    print("Agentic Workflow System Setup")
    print("=" * 60)

    # Step 1: Create directory structure
    create_directory_structure()

    # Step 2: Create configurations
    create_agent_configuration()
    update_main_configuration()

    # Step 3: Create example script
    create_example_script()

    # Step 4: Test systems
    test_llm_client()
    test_agent_system()

    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review configuration in config/agents.json")
    print("  2. Run example: python scripts/example_agentic_usage.py")
    print("  3. Start server: python server.py")
    print("\nDocumentation:")
    print("  - docs/REFACTORING_GUIDE.md - Complete refactoring guide")
    print("=" * 60)


if __name__ == "__main__":
    main()
