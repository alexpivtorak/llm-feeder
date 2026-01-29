import asyncio
import re
from urllib.parse import urljoin, urlparse
from typing import Set, List, Optional
import typer
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from rich.console import Console
from rich.progress import Progress

app = typer.Typer()
console = Console()

class Scraper:
    def __init__(self, start_url: str, output_file: str):
        self.start_url = start_url
        self.output_file = output_file
        self.visited: Set[str] = set()
        self.seen_urls: Set[str] = set()
        self.queue: List[str] = [start_url]
        self.seen_urls.add(self.normalize_url(start_url))
        self.base_domain = urlparse(start_url).netloc
        self.base_path = urlparse(start_url).path
        # Ensure base path ends with / if it's a directory for correct subpath checking
        if not self.base_path.endswith('/') and '.' not in self.base_path.split('/')[-1]:
             self.base_path += '/'
        # specialized cleaning for content
        self.markdown_content: List[str] = []

    def is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        # Check domain match
        if parsed.netloc != self.base_domain:
            return False
        # Check if it is a subpath of the start url or related
        # Relaxed check: just same domain is usually enough for docs if we are careful, 
        # but let's try to stick to the subpath if possible/configured.
        # For now, let's keep it strictly same domain and ensuring it doesn't jump out of docs/
        # commonly docs are at /docs/... or similar.
        if not url.startswith(self.start_url):
             # Try to be a bit smarter, if start_url is .../docs/intro, we want .../docs/advanced
             # So we check if it starts with the base path of start_url
             pass
        
        return True

    def normalize_url(self, url: str) -> str:
        # Remove fragment
        return url.split('#')[0].rstrip('/')

    async def crawl(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            with Progress() as progress:
                task_id = progress.add_task("[cyan]Crawling...", total=None)
                
                while self.queue:
                    url = self.queue.pop(0)
                    normalized_url = self.normalize_url(url)

                    if normalized_url in self.visited:
                        continue
                    
                    self.visited.add(normalized_url)
                    progress.update(task_id, description=f"Crawling: {url}", advance=1)
                    
                    try:
                        await page.goto(url, wait_until="domcontentloaded")
                        content = await page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Extract Main Content
                        main_content = soup.find('main') or soup.find('article') or soup.find('body')
                        
                        if main_content:
                            # Clean up
                            for tag in main_content(['script', 'style', 'nav', 'footer']):
                                tag.decompose()
                            
                            # Resolve relative URLs
                            for tag in main_content.find_all(['a', 'img']):
                                if tag.name == 'a' and tag.get('href'):
                                    tag['href'] = urljoin(url, tag['href'])
                                elif tag.name == 'img' and tag.get('src'):
                                    tag['src'] = urljoin(url, tag['src'])

                            title = soup.title.string if soup.title else url
                            markdown = md(str(main_content), heading_style="ATX")
                            
                            # Post-process markdown to remove excessive newlines
                            markdown = re.sub(r'\n{3,}', '\n\n', markdown).strip()
                            
                            self.markdown_content.append(f"# {title}\n\nURL: {url}\n\n{markdown}\n\n---\n\n")

                        # Find Links
                        for a in soup.find_all('a', href=True):
                            href = a['href']
                            full_url = urljoin(url, href)
                            normalized_full = self.normalize_url(full_url)
                            
                            if (self.is_valid_url(full_url) and 
                                normalized_full not in self.visited and 
                                normalized_full not in self.seen_urls): # Check against seen_urls to avoid dups in queue
                                
                                self.seen_urls.add(normalized_full)
                                self.queue.append(full_url)

                    except Exception as e:
                        console.print(f"[red]Error scraping {url}: {e}[/red]")

            await browser.close()
            
        # Write output
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.markdown_content))
        
        console.print(f"[green]Scraping complete! Saved to {self.output_file}[/green]")
        console.print(f"Total pages visited: {len(self.visited)}")

@app.command()
def main(
    url: str = typer.Option(..., help="The URL to start scraping from"),
    output: str = typer.Option("docs.md", help="The output markdown file")
):
    """
    Scrape a documentation website and save it as a single Markdown file.
    """
    scraper = Scraper(url, output)
    asyncio.run(scraper.crawl())

if __name__ == "__main__":
    app()
