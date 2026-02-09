import os
import sys
from openai import OpenAI

def check_access():
    print("--- OpenAI API Access Diagnostic ---")
    
    # 1. Get API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n[INFO] No OPENAI_API_KEY found in environment variables.")
        api_key = input("Please enter your OpenAI API Key: ").strip()
        if not api_key:
            print("[ERROR] No API Key provided. Exiting.")
            return

    client = OpenAI(api_key=api_key)

    # 2. Check Model List Access
    print("\n[1/3] Checking ability to list models...")
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        print("✅ Successfully retrieved model list.")
    except Exception as e:
        print(f"❌ Failed to list models. Error: {e}")
        print("\nPossible causes:")
        print("- Invalid API Key")
        print("- Project permissions do not allow listing models")
        print("- Organization restrictions")
        print("- Zero budget / Billing issues")
        return

    # 3. Check for gpt-4o-transcribe specifically
    print("\n[2/3] Checking for 'gpt-4o-transcribe' model based on list...")
    if "gpt-4o-transcribe" in model_ids:
        print("✅ 'gpt-4o-transcribe' found in your available models.")
    else:
        print("❌ 'gpt-4o-transcribe' NOT found in your available models.")
        print("Available models start with:", model_ids[:5])
        print("\nCommon reasons:")
        print("- Your Project configuration specifically excludes this model.")
        print("- This key belongs to a Project that doesn't have Audio permissions.")

    # 4. Attempt a dummy completion
    print("\n[3/3] Testing 'gpt-3.5-turbo' chat completion (basic check)...")
    try:
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print("✅ Basic Chat Completion worked.")
    except Exception as e:
        print(f"❌ Chat Completion failed. Error: {e}")

if __name__ == "__main__":
    try:
        check_access()
    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
