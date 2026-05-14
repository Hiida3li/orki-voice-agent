"""
Business context extractor.
Handles website content extraction and LLM-based analysis.
"""
import json
import logging
from typing import Dict, Any, Optional

import httpx
from bs4 import BeautifulSoup

from .models import BusinessContext, FAQ

logger = logging.getLogger(__name__)


class WebsiteExtractor:
    """Extracts text content from websites."""

    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    DEFAULT_TIMEOUT = 15.0
    MAX_CONTENT_LENGTH = 8000

    async def fetch(self, url: str) -> tuple[str, str]:
        """
        Fetch website content.

        Returns:
            Tuple of (text_content, page_title)
        """
        async with httpx.AsyncClient(
            timeout=self.DEFAULT_TIMEOUT,
            follow_redirects=True
        ) as client:
            response = await client.get(url, headers=self.DEFAULT_HEADERS)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove non-content elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Extract text content
            text_content = soup.get_text(separator='\n', strip=True)
            text_content = text_content[:self.MAX_CONTENT_LENGTH]

            # Get page title
            title = soup.find('title')
            page_title = title.string.strip() if title and title.string else ""

            logger.info(f"Extracted {len(text_content)} characters from {url}")

            return text_content, page_title


class BusinessContextExtractor:
    """Extracts business context using LLM analysis."""

    EXTRACTION_PROMPT = """Analyze the following website content and extract business information.

Website URL: {url}
Page Title: {title}

Website Content:
{content}

Please provide:
1. Company/Business Name (extract the main business name, not generic terms)
2. Brief Description (1-2 sentences about what the business does)
3. Generate 5-8 relevant FAQs that customers might ask about this business

Respond in this exact JSON format:
{{
  "company_name": "Business Name Here",
  "description": "Brief description of the business",
  "faqs": [
    {{"question": "FAQ question 1?", "answer": "Clear answer to the question"}},
    {{"question": "FAQ question 2?", "answer": "Clear answer to the question"}}
  ]
}}

Important:
- company_name should be the actual business name, not generic terms like "Home", "Website", etc.
- description should be concise and informative
- FAQs should be realistic questions customers would ask
- Keep answers clear and helpful
"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.website_extractor = WebsiteExtractor()

    async def extract(self, website_url: str) -> BusinessContext:
        """
        Extract business context from a website URL.

        Args:
            website_url: The URL to extract context from

        Returns:
            BusinessContext with extracted information
        """
        try:
            # Fetch website content
            text_content, page_title = await self.website_extractor.fetch(website_url)

            # Use Gemini to extract structured information
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            prompt = self.EXTRACTION_PROMPT.format(
                url=website_url,
                title=page_title,
                content=text_content
            )

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )

            # Parse the JSON response
            result_text = response.text.strip()
            extracted_data = json.loads(result_text)

            # Build context from extracted data
            faqs = [
                FAQ(question=faq.get('question', ''), answer=faq.get('answer', ''))
                for faq in extracted_data.get('faqs', [])[:10]
            ]

            context = BusinessContext(
                company_name=extracted_data.get('company_name', 'Unknown'),
                description=extracted_data.get('description', ''),
                faqs=faqs
            )

            logger.info(f"LLM extracted: '{context.company_name}' with {len(context.faqs)} FAQs")
            return context

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {website_url}")
            return BusinessContext(company_name='Unknown', error='Request timeout')

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {website_url}: {e}")
            return BusinessContext(company_name='Unknown', error=f'HTTP {e.response.status_code}')

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response: {e}")
            return BusinessContext(company_name='Unknown', error='Failed to parse LLM response')

        except Exception as e:
            logger.error(f"Error extracting business context from {website_url}: {e}", exc_info=True)
            return BusinessContext(company_name='Unknown', error=str(e))


async def extract_business_context(
    website_url: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function for extracting business context.

    Args:
        website_url: The URL to extract context from
        api_key: Google API key (uses environment variable if not provided)

    Returns:
        Dictionary with business context
    """
    import os

    if api_key is None:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return {"company_name": "Unknown", "error": "GOOGLE_API_KEY not configured"}

    extractor = BusinessContextExtractor(api_key)
    context = await extractor.extract(website_url)
    return context.to_dict()
