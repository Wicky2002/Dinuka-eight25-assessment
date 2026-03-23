import re
from typing import Dict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class WebScraper:
	def __init__(self, timeout_seconds: int = 15, allow_insecure: bool = True) -> None:
		self.timeout_seconds = timeout_seconds
		self.allow_insecure = allow_insecure

	def extract_metrics(self, url: str) -> Dict[str, object]:
		headers = {
			"User-Agent": (
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
				"AppleWebKit/537.36 (KHTML, like Gecko) "
				"Chrome/122.0 Safari/537.36"
			)
		}
		try:
			response = requests.get(
				url,
				headers=headers,
				timeout=self.timeout_seconds,
				verify=False,
			)
		except requests.exceptions.SSLError:
			if not self.allow_insecure:
				raise
			response = requests.get(
				url,
				headers=headers,
				timeout=self.timeout_seconds,
				verify=False,
			)
		response.raise_for_status()

		soup = BeautifulSoup(response.text, "html.parser")
		body = soup.body or soup
		for tag in body(["script", "style", "noscript"]):
			tag.decompose()

		page_text = " ".join(body.stripped_strings)
		word_count = len(re.findall(r"\b\w+\b", page_text))

		h1_count = len(soup.find_all("h1"))
		h2_count = len(soup.find_all("h2"))
		h3_count = len(soup.find_all("h3"))

		cta_count = 0
		for tag in soup.find_all(["a", "button"]):
			if self._is_cta(tag):
				cta_count += 1

		base_netloc = urlparse(url).netloc.lower()
		internal_links = 0
		external_links = 0
		for link in soup.find_all("a", href=True):
			href_value = link.get("href", "")
			href = href_value if isinstance(href_value, str) else ""
			if not href or href.startswith("#"):
				continue
			absolute = urljoin(url, href)
			parsed = urlparse(absolute)
			if not parsed.netloc:
				continue
			if parsed.netloc.lower() == base_netloc:
				internal_links += 1
			else:
				external_links += 1

		images = soup.find_all("img")
		image_count = len(images)
		missing_alt = 0
		for img in images:
			alt_value = img.get("alt", "")
			alt_text = alt_value if isinstance(alt_value, str) else ""
			if not alt_text.strip():
				missing_alt += 1
		missing_alt_text_percent = (
			round((missing_alt / image_count) * 100, 2) if image_count else 0.0
		)

		meta_title = None
		if soup.title and soup.title.string:
			meta_title = soup.title.string.strip()

		meta_description = None
		meta_desc_tag = soup.find("meta", attrs={"name": "description"})
		if meta_desc_tag and meta_desc_tag.get("content"):
			content_value = meta_desc_tag.get("content")
			content_text = content_value if isinstance(content_value, str) else ""
			meta_description = content_text.strip() or None

		return {
			"word_count": word_count,
			"h1_count": h1_count,
			"h2_count": h2_count,
			"h3_count": h3_count,
			"cta_count": cta_count,
			"internal_links": internal_links,
			"external_links": external_links,
			"image_count": image_count,
			"missing_alt_text_percent": missing_alt_text_percent,
			"meta_title": meta_title,
			"meta_description": meta_description,
			"page_text": page_text,
		}

	def _is_cta(self, tag) -> bool:
		classes = tag.get("class", [])
		class_text = " ".join(classes).lower()
		return "btn" in class_text or "button" in class_text
