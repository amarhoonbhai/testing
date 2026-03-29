
import asyncio
import sys
import os
import re

# Simulate the resolution logic with fallback
def simulate_resolution(group_doc):
    chat_id = group_doc.get("chat_id")
    chat_title = group_doc.get("chat_title")
    chat_username = group_doc.get("chat_username")
    
    # 1. Try public username resolution
    username = chat_username
    if not username and chat_title and re.match(r'^[a-zA-Z0-9_]{4,32}$', chat_title):
        # Fallback for old groups: title might be the slug
        username = chat_title
        
    return username

def test_fallback():
    print("--- Fallback Logic Verification ---")
    
    # Case 1: New group with username
    group1 = {"chat_id": -123, "chat_title": "My Group", "chat_username": "my_username"}
    print(f"Case 1 (New): {group1} -> Resolved Username: {simulate_resolution(group1)}")
    
    # Case 2: Old group without username field, title is the slug
    group2 = {"chat_id": -456, "chat_title": "legacy_slug", "chat_username": None}
    print(f"Case 2 (Legacy): {group2} -> Resolved Username: {simulate_resolution(group2)}")
    
    # Case 3: Group with title that is NOT a slug (has spaces)
    group3 = {"chat_id": -789, "chat_title": "Group With Spaces", "chat_username": None}
    print(f"Case 3 (Non-slug): {group3} -> Resolved Username: {simulate_resolution(group3)}")

if __name__ == "__main__":
    test_fallback()
