"""
LLM integration for analysis and report generation
Supports multiple providers: OpenAI, Gemini, Groq, local models
"""

import json
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response from LLM"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""
    
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using OpenAI"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"OpenAI API error: {str(e)}")


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider"""
    
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Gemini"""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            response = await self.model.generate_content_async(full_prompt)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise LLMError(f"Gemini API error: {str(e)}")


class GroqProvider(BaseLLMProvider):
    """Groq API provider"""
    
    def __init__(self):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
    
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Groq"""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise LLMError(f"Groq API error: {str(e)}")


class LLMService:
    """Main LLM service for SmartRecon-AI"""
    
    SYSTEM_PROMPT = """You are SmartRecon-AI, an expert bug-bounty recon and reporting assistant.

You receive:
- Target scope and policy
- Outputs from recon tools (Subfinder, Amass, HTTPX, FFUF, Nuclei, custom scripts) in JSON

Your tasks:
1. Normalize and deduplicate findings across tools while preserving crucial evidence
2. Prioritize findings by realistic exploitability and impact, mapping them to CWE and approximate CVSS
3. Highlight a concise top list of findings that deserve manual investigation and explain why
4. Generate safe, non-destructive PoC steps and example HTTP requests/payloads
5. Produce professional, Markdown-formatted bug bounty reports, optimized for platforms like HackerOne/Intigriti

Constraints:
- Never propose illegal or destructive actions (no data deletion, no DoS)
- Never fabricate tool output; reason only from the provided data
- When uncertain, explicitly state what additional manual tests are needed
- All PoCs must be safe and non-destructive

Output format: Always respond with valid JSON containing the requested structure."""
    
    def __init__(self):
        self.provider = self._get_provider()
    
    def _get_provider(self) -> BaseLLMProvider:
        """Get LLM provider based on configuration"""
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "openai":
            return OpenAIProvider()
        elif provider == "gemini":
            return GeminiProvider()
        elif provider == "groq":
            return GroqProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    async def prioritize_findings(
        self,
        findings: List[Dict[str, Any]],
        target_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize and analyze findings using LLM
        
        Args:
            findings: List of raw findings from tools
            target_info: Target information and scope
        
        Returns:
            List of prioritized findings with AI analysis
        """
        prompt = f"""Analyze and prioritize these security findings for the target.

Target Information:
{json.dumps(target_info, indent=2)}

Findings:
{json.dumps(findings[:20], indent=2)}  # Limit to top 20 for token efficiency

Tasks:
1. Deduplicate similar findings
2. Assign priority rank (1 = highest priority)
3. Estimate likelihood of valid bug (0-100)
4. Suggest manual verification steps
5. Assess potential impact

Respond with JSON array:
[
  {{
    "original_finding_id": "...",
    "priority_rank": 1,
    "severity": "high",
    "likelihood_of_valid_bug": 85,
    "suggested_manual_steps": ["step1", "step2"],
    "potential_impact": "description",
    "reasoning": "why this is prioritized"
  }}
]"""
        
        try:
            response = await self.provider.generate(prompt, self.SYSTEM_PROMPT)
            
            # Parse JSON response
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            prioritized = json.loads(response)
            return prioritized
            
        except Exception as e:
            logger.error(f"Error prioritizing findings: {e}")
            return []
    
    async def generate_poc(
        self,
        finding: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Generate proof-of-concept for a finding
        
        Args:
            finding: Finding details
            context: Additional context
        
        Returns:
            PoC as markdown string
        """
        prompt = f"""Generate a safe, non-destructive proof-of-concept for this finding.

Finding:
{json.dumps(finding, indent=2)}

Context:
{json.dumps(context, indent=2)}

Generate:
1. Clear step-by-step reproduction instructions
2. Example HTTP request (curl or raw)
3. Expected vs actual response
4. Impact explanation
5. Remediation recommendation

Format as Markdown. Be specific but concise. Never include destructive payloads."""
        
        try:
            poc = await self.provider.generate(prompt, self.SYSTEM_PROMPT)
            return poc
        except Exception as e:
            logger.error(f"Error generating PoC: {e}")
            return "Failed to generate PoC"
    
    async def generate_report_summary(
        self,
        scan_data: Dict[str, Any],
        findings: List[Dict[str, Any]]
    ) -> str:
        """
        Generate executive summary for report
        
        Args:
            scan_data: Scan metadata
            findings: List of findings
        
        Returns:
            Executive summary as markdown
        """
        prompt = f"""Generate a professional executive summary for this bug bounty reconnaissance report.

Scan Information:
{json.dumps(scan_data, indent=2)}

Findings Summary:
- Total findings: {len(findings)}
- Critical: {sum(1 for f in findings if f.get('severity') == 'critical')}
- High: {sum(1 for f in findings if f.get('severity') == 'high')}
- Medium: {sum(1 for f in findings if f.get('severity') == 'medium')}
- Low: {sum(1 for f in findings if f.get('severity') == 'low')}

Generate a concise executive summary (3-4 paragraphs) covering:
1. Scope and methodology
2. Key findings and risk assessment
3. Overall security posture
4. Recommended priorities

Format as Markdown."""
        
        try:
            summary = await self.provider.generate(prompt, self.SYSTEM_PROMPT)
            return summary
        except Exception as e:
            logger.error(f"Error generating report summary: {e}")
            return "Failed to generate summary"
