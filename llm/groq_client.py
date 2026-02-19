"""
Groq API client wrapper for LLM inference.
"""

from typing import Optional
from groq import Groq

from config.settings import get_settings


class GroqClient:
    """Wrapper for Groq API for triage suggestions."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize the Groq client.

        Args:
            api_key: Groq API key (defaults to env var)
            model: Model to use
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
        """
        settings = get_settings()

        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self.temperature = temperature if temperature is not None else settings.groq_temperature
        self.max_tokens = max_tokens or settings.groq_max_tokens

        self.client = Groq(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            model: Override model
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            Generated text response
        """
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens or self.max_tokens
        )

        return response.choices[0].message.content

    def classify_alert(self, alert_text: str) -> dict:
        """
        Classify an alert to extract structured information.

        Args:
            alert_text: Raw alert message

        Returns:
            Dictionary with classification results
        """
        from llm.prompts import CLASSIFICATION_PROMPT

        prompt = CLASSIFICATION_PROMPT.format(raw_message=alert_text)

        response = self.generate(
            prompt=prompt,
            temperature=0.1  # Low temperature for consistent classification
        )

        # Parse JSON response
        import json
        try:
            # Clean up response if needed
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Return default classification if parsing fails
            return {
                "alert_type": "unknown",
                "severity": "medium",
                "title": alert_text[:100] if len(alert_text) > 100 else alert_text,
                "affected_component": None,
                "source_system": None
            }

    def generate_triage(
        self,
        alert_title: str,
        alert_type: str,
        severity: str,
        description: str,
        source_system: str,
        timestamp: str,
        runbook_context: str
    ) -> str:
        """
        Generate a triage suggestion for an alert.

        Args:
            alert_title: Title of the alert
            alert_type: Type of alert
            severity: Severity level
            description: Alert description
            source_system: Source system
            timestamp: Alert timestamp
            runbook_context: Relevant runbook content

        Returns:
            Triage suggestion text
        """
        from llm.prompts import TRIAGE_SYSTEM_PROMPT, TRIAGE_PROMPT_TEMPLATE

        prompt = TRIAGE_PROMPT_TEMPLATE.format(
            alert_title=alert_title,
            alert_type=alert_type,
            severity=severity,
            description=description,
            source_system=source_system or "Unknown",
            timestamp=timestamp,
            runbook_context=runbook_context
        )

        return self.generate(
            prompt=prompt,
            system_prompt=TRIAGE_SYSTEM_PROMPT
        )
