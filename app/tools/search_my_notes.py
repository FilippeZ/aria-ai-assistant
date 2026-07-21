import asyncio
import json
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Create a FastMCP server named "Aria Knowledge Bridge"
mcp = FastMCP("Aria Knowledge Bridge")

KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"

async def query_notebooklm(query: str) -> str:
    """Read and search notebooks from the knowledge base directory."""
    if not KB_DIR.exists():
        return "Δεν βρέθηκαν σημειώσεις στο NotebookLM knowledge base."
        
    notes = list(KB_DIR.glob("*.md"))
    if not notes:
        return "Δεν βρέθηκαν σημειώσεις."
        
    # Read the latest notebook file
    latest_note = sorted(notes, key=os.path.getmtime, reverse=True)[0]
    content = latest_note.read_text(encoding="utf-8")
    
    return f"[NotebookLM File: {latest_note.name}]\n{content[:1200]}"

@mcp.tool()
async def search_my_notes(query: str) -> str:
    """Χρησιμοποίησε αυτό το εργαλείο για να αναζητήσεις πληροφορίες στις προσωπικές σημειώσεις και τα τεχνικά βιβλία του χρήστη. ΠΑΝΤΑ να το καλείς όταν ζητείται τεχνική θεωρία."""
    try:
        return await query_notebooklm(query)
    except Exception as e:
        return f"Σφάλμα κατά την αναζήτηση: {str(e)}"

if __name__ == "__main__":
    mcp.run()
