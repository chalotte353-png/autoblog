"""
Run this ONCE to clean up existing duplicate posts from your site.
Place in autoblog-main/ and run: python cleanup_duplicates.py
"""
import json, re
from pathlib import Path

OUTPUT_DIR = Path("output")

STOP = {"a","an","the","in","on","at","of","and","for","to","is","are","was","were",
        "it","its","as","by","with","from","that","this","has","have","after","over",
        "into","about","up","out","than","but","be","been","their","his","her","our"}

def slugify_words(slug):
    return set(slug.split("-")) - STOP

def find_duplicates(posts):
    """Return dict of slug -> canonical_slug for duplicates to redirect."""
    keep = []      # list of (slug, words)
    duplicates = {}  # slug -> canonical

    for p in posts:
        slug = p["slug"]
        words = slugify_words(slug)
        is_dup = False
        for kept_slug, kept_words in keep:
            overlap = len(words & kept_words) / max(len(words), len(kept_words))
            if overlap >= 0.6:
                duplicates[slug] = kept_slug
                is_dup = True
                break
        if not is_dup:
            keep.append((slug, words))
    return duplicates

def add_canonical_redirect(file_path, canonical_url):
    """Add canonical tag pointing to original to suppress duplicate."""
    content = file_path.read_text()
    # Update canonical tag
    content = re.sub(
        r'<link rel="canonical" href="[^"]*">',
        f'<link rel="canonical" href="{canonical_url}">',
        content
    )
    file_path.write_text(content)

def main():
    index_file = OUTPUT_DIR / "posts_index.json"
    if not index_file.exists():
        print("posts_index.json not found!")
        return

    posts = json.loads(index_file.read_text())
    print(f"Total posts: {len(posts)}")

    duplicates = find_duplicates(posts)
    print(f"Duplicate posts found: {len(duplicates)}")

    SITE_URL = "https://marketsnewstoday.info"
    fixed = 0
    for dup_slug, canonical_slug in duplicates.items():
        canonical_url = f"{SITE_URL}/posts/{canonical_slug}.html"
        dup_file = OUTPUT_DIR / "posts" / f"{dup_slug}.html"
        if dup_file.exists():
            add_canonical_redirect(dup_file, canonical_url)
            print(f"  Fixed canonical: {dup_slug} → {canonical_slug}")
            fixed += 1

    # Deduplicate the index
    seen = set()
    clean_posts = []
    for p in posts:
        if p["slug"] not in seen and p["slug"] not in duplicates:
            seen.add(p["slug"])
            clean_posts.append(p)

    # Save clean index
    index_file.write_text(json.dumps(clean_posts, indent=2))
    print(f"\n✅ Done! Fixed {fixed} duplicate canonical tags")
    print(f"   Index cleaned: {len(posts)} → {len(clean_posts)} posts")
    print(f"\nNext: Re-run generate_articles.py to rebuild sitemap without duplicates")

if __name__ == "__main__":
    main()
