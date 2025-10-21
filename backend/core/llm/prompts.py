"""
Prompt Templates and System Prompts for LLM

Centralized prompt management for consistency and maintainability.
"""

from __future__ import annotations

from typing import Dict, List, Optional


class PromptTemplate:
    """Template for constructing prompts with variable substitution."""

    def __init__(self, template: str, variables: Optional[List[str]] = None):
        """
        Initialize prompt template.

        Args:
            template: Template string with {variable} placeholders
            variables: List of required variable names
        """
        self.template = template
        self.variables = variables or []

    def format(self, **kwargs) -> str:
        """
        Format template with provided variables.

        Args:
            **kwargs: Variable substitutions

        Returns:
            Formatted prompt string

        Raises:
            ValueError: If required variables are missing
        """
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        return self.template.format(**kwargs)


class SystemPrompts:
    """Collection of system prompts for different use cases."""

    # Base system prompts
    UNIVERSAL = """You are an AI assistant for the HE team. Always be professional, accurate, and helpful.
Provide clear, concise responses and ask for clarification when needed.
Always format your responses better. Use linebreaks liberally."""

    DEFAULT = UNIVERSAL + "\nYou provide general assistance with various tasks including programming, analysis, and problem-solving."

    # Specialized prompts
    RAG_MODE = """You have access to the team's knowledge base. Use the provided context to answer questions accurately.
If the context doesn't contain relevant information, say so and provide general guidance if possible.

Context: {context}"""

    JSON_ANALYSIS = """You are a JSON data analysis expert. Analyze the provided JSON data and answer questions with precision.

IMPORTANT Guidelines:
1. Show step-by-step reasoning
2. Identify relevant JSON paths
3. Extract exact values
4. Perform calculations if needed
5. State your final answer clearly
6. Never guess or hallucinate
7. If information is missing, state explicitly

JSON Data:
{json_data}

Numeric Summary:
{numeric_summary}

Question: {question}"""

    AGENT_REASONING = """You are a reasoning engine for an autonomous agent system.

Your task: Analyze the current state and determine the next action.

Current state:
{current_state}

Available tools:
{tools}

Execution history:
{execution_trace}

Task: {task}

Provide your response in this format:
```json
{{
  "thought": "Your reasoning about what to do next",
  "action": "tool_name",
  "parameters": {{...}},
  "confidence": 0.95
}}
```"""

    AGENT_PLANNING = """You are a task planning expert. Break down complex tasks into executable steps.

Task: {task}

Available tools:
{tools}

Data structure:
{data_structure}

Create a step-by-step execution plan. Output as JSON:
```json
{{
  "steps": [
    {{
      "step_number": 1,
      "tool": "tool_name",
      "parameters": {{}},
      "reasoning": "why this step is needed",
      "expected_output": "what this step should produce"
    }}
  ],
  "estimated_complexity": "low|medium|high",
  "estimated_iterations": 3
}}
```"""

    KEYWORD_EXTRACTION = """You are a keyword extraction specialist. Extract 1-4 specific, searchable keywords from queries.

OUTPUT FORMAT: Return ONLY comma-separated keywords. NO labels, NO prefixes, NO extra text.

Focus on:
1. Technical terms and specific concepts
2. Proper nouns (names, places, technologies)
3. Key descriptive words
4. Avoid generic words like 'help', 'how', 'what', 'the', 'and'

Order keywords by importance (most important first).

Query: {query}"""

    INSIGHT_GENERATION = """You are an insight generation expert. Analyze the data and findings to provide actionable insights.

Data analysis results:
{analysis_results}

Generate insights in this format:
```json
{{
  "key_findings": ["finding 1", "finding 2", ...],
  "insights": ["insight 1", "insight 2", ...],
  "recommendations": ["recommendation 1", "recommendation 2", ...],
  "confidence": 0.95,
  "data_quality": "high|medium|low"
}}
```"""

    @classmethod
    def get(cls, name: str, **kwargs) -> str:
        """
        Get a system prompt by name with variable substitution.

        Args:
            name: Name of the prompt (e.g., 'RAG_MODE', 'JSON_ANALYSIS')
            **kwargs: Variables for template substitution

        Returns:
            Formatted system prompt
        """
        template = getattr(cls, name, cls.DEFAULT)

        if callable(template):
            return template(**kwargs)

        # Simple variable substitution
        try:
            return template.format(**kwargs)
        except KeyError:
            # Return template as-is if variables are missing
            return template

    @classmethod
    def create_messages(
        cls,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        Create messages array for chat completion.

        Args:
            system_prompt: System instructions
            user_message: User's message
            conversation_history: Optional previous messages

        Returns:
            List of message dicts ready for LLM API
        """
        messages = []

        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages
