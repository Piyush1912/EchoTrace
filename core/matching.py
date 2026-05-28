from core.storeNmatch import match_audio

# Usage: pass the path to an audio file you want to test matching
# Example: python -m core.matching
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m core.matching <path_to_audio_file>")
        sys.exit(1)
    audio_path = sys.argv[1]
    match, elapsed = match_audio(audio_path)
    print(f"Match: {match}")
    print(f"Time:  {elapsed:.2f}s")
