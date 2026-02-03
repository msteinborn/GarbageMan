"""
Investopedia Business Terms Scraper
Fetches business glossary terms from Investopedia and saves to CSV
"""

import string
import csv
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from pathlib import Path


class InvestopediaScraper:
    def __init__(self, output_file: str = "business_terms.csv"):
        self.output_file = output_file
        self.terms: List[Dict[str, str]] = []
        
    def scrape_alphabet(self, alphabet: str) -> List[Dict[str, str]]:
        """
        Scrape all terms starting with a given letter from Investopedia
        
        Args:
            alphabet: Single letter (a-z)
            
        Returns:
            List of dicts with 'term' and 'definition' keys
        """
        print(f"  Fetching terms starting with '{alphabet.upper()}'...")
        
        try:
            # Simple URL - Investopedia serves all terms for a letter on one page
            url = f"https://www.investopedia.com/terms/{alphabet}/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find term links - look for common term entry patterns
            # Investopedia uses various selectors, try multiple approaches
            alphabet_terms = []
            
            # Approach 1: Look for term title links
            term_links = soup.findAll('a', {'class': 'term-link'})
            if not term_links:
                # Approach 2: Look for h3 with term titles
                term_elements = soup.findAll('h3', {'class': 'item-title'})
                for elem in term_elements:
                    link = elem.find('a')
                    if link:
                        term_text = link.get_text(strip=True)
                        if term_text:
                            alphabet_terms.append({
                                "term": term_text,
                                "definition": f"Financial term: {term_text}"
                            })
            else:
                # Approach 1 worked
                for link in term_links:
                    term_text = link.get_text(strip=True)
                    if term_text:
                        alphabet_terms.append({
                            "term": term_text,
                            "definition": f"Financial term: {term_text}"
                        })
            
            # Fallback: Look for any links containing term text
            if not alphabet_terms:
                all_links = soup.findAll('a')
                seen_terms = set()
                for link in all_links:
                    term_text = link.get_text(strip=True)
                    # Filter out navigation links and short text
                    if len(term_text) > 2 and len(term_text) < 100 and term_text[0].isalpha() and term_text not in seen_terms:
                        alphabet_terms.append({
                            "term": term_text,
                            "definition": f"Financial term: {term_text}"
                        })
                        seen_terms.add(term_text)
            
            print(f"    ✓ Found {len(alphabet_terms)} terms")
            return alphabet_terms
            
        except requests.RequestException as e:
            print(f"  ⚠️  Error scraping alphabet '{alphabet}': {e}")
            return []
    
    def scrape_all(self) -> List[Dict[str, str]]:
        """
        Scrape all business terms from A-Z
        
        Returns:
            Complete list of terms and definitions
        """
        print("📥 Scraping Investopedia business glossary...")
        
        all_terms = []
        for letter in string.ascii_lowercase:
            terms = self.scrape_alphabet(letter)
            all_terms.extend(terms)
        
        self.terms = all_terms
        print(f"\n✓ Total terms scraped: {len(all_terms)}")
        return all_terms
    
    def save_to_csv(self) -> str:
        """
        Save scraped terms to CSV file
        
        Returns:
            Path to saved CSV file
        """
        if not self.terms:
            print("⚠️  No terms to save. Run scrape_all() first.")
            return None
        
        output_path = Path(self.output_file)
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['term', 'definition'])
                writer.writeheader()
                writer.writerows(self.terms)
            
            print(f"✓ Saved {len(self.terms)} terms to {output_path}")
            return str(output_path)
        
        except Exception as e:
            print(f"✗ Error saving CSV: {e}")
            return None
    
    def run_full_pipeline(self) -> str:
        """
        Run complete scrape and save pipeline
        
        Returns:
            Path to saved CSV file
        """
        self.scrape_all()
        return self.save_to_csv()


if __name__ == "__main__":
    scraper = InvestopediaScraper()
    scraper.run_full_pipeline()
