"""
Crash reproduction test for Music Player backend.

This file demonstrates and tests a deliberate crash scenario introduced
for debugging purposes. The crash occurs in the search method.

Before the fix: Calling search() with any query will raise TypeError
After the fix: search() handles the error gracefully

To reproduce the crash manually:
    python -m src.main
    Use search or another endpoint that triggers the bug
"""

import pytest
from src.backend.services.library import LibraryServiceImpl


def test_crash_repro():
    """Test that reproduces the deliberate crash."""
    svc = LibraryServiceImpl()
    
    # This should crash before the fix
    result = svc.search("test")
    
    # We expect this to fail before fix
    assert result is not None


def test_search_with_special_chars():
    """Search with various queries."""
    svc = LibraryServiceImpl()
    
    # Test with various query strings
    queries = [
        "",
        "test",
        "Hello",
        "Music Player",
        "test@special#chars",
    ]
    
    for query in queries:
        with pytest.raises(TypeError):
            result = svc.search(query)


if __name__ == "__main__":
    # Run directly
    print("Testing crash reproduction...")
    test_crash_repro()
    print("CRASH REPRODUCED!")
