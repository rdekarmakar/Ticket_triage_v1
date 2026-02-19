"""
Prompt templates for LLM-based triage.
"""

TRIAGE_SYSTEM_PROMPT = """You are an expert SRE/DevOps engineer assisting with production incident triage.
Your role is to:
1. Analyze the alert and assess its severity and impact
2. Suggest immediate actions based on relevant runbook procedures
3. Identify potential root causes
4. Recommend escalation paths if needed

Guidelines:
- Be concise and actionable
- Prioritize system stability
- Reference specific runbook procedures when available
- Format responses for quick readability during incidents
- Use bullet points and numbered lists
- Highlight critical actions"""

TRIAGE_PROMPT_TEMPLATE = """
## Alert Information
**Title:** {alert_title}
**Type:** {alert_type}
**Severity:** {severity}
**Description:** {description}
**Source System:** {source_system}
**Timestamp:** {timestamp}

## Relevant Runbook Sections
{runbook_context}

## Task
Based on the alert and runbook information above, provide a triage response with:

1. **Summary** (1-2 sentences): What is happening and why it matters?

2. **Immediate Actions** (numbered list): What should be done right now?
   - Be specific with commands or steps
   - Order by priority

3. **Root Cause Hypothesis**: What likely caused this issue?

4. **Escalation Recommendation**:
   - Should this be escalated?
   - If yes, to whom?
   - What information should be included?

5. **Confidence Level**: How confident are you in this assessment? (High/Medium/Low)

Keep your response concise and actionable. Focus on what needs to be done NOW.
"""

CLASSIFICATION_PROMPT = """Analyze this production alert and classify it.

Alert Text:
{raw_message}

Respond with ONLY valid JSON in this exact format (no additional text):
{{
    "alert_type": "infrastructure|application|monitoring",
    "severity": "critical|high|medium|low|info",
    "title": "brief descriptive title (max 100 chars)",
    "affected_component": "component name or null if unknown",
    "source_system": "source system name or null if unknown"
}}

Classification Guidelines:
- alert_type:
  - "infrastructure": Server, network, disk, memory, CPU issues
  - "application": HTTP errors, exceptions, crashes, timeouts
  - "monitoring": Alert threshold breaches, metric anomalies

- severity:
  - "critical": Service down, data at risk, immediate action required
  - "high": Significant degradation, affects many users
  - "medium": Noticeable impact, needs attention soon
  - "low": Minor issue, can be scheduled
  - "info": Informational, no immediate action needed
"""

QUICK_SUGGESTION_PROMPT = """Given this production alert, provide a brief (2-3 sentence) assessment and the single most important action to take.

Alert: {alert_text}

Respond in this format:
Assessment: [brief assessment]
Action: [single most important action]
"""

RUNBOOK_SEARCH_QUERY_PROMPT = """Convert this alert into a search query for finding relevant runbook documentation.

Alert: {alert_text}

Respond with ONLY the search query (no explanation). The query should:
- Focus on the type of issue
- Include relevant technical terms
- Be 5-15 words long
"""
