from geo_codex_logic.core.llm_client import LLMClient

def main():
    print("--- Initializing LLMClient ---")
    # We don't need to pass an API key because the class will load it from our .env file
    try:
        client = LLMClient()
    except ValueError as e:
        print(e)
        return

    print("\n--- Testing Connection ---")
    success, message = client.test_connection()
    print(f"Result: {success}, Message: {message}")

    if success:
        print("\n--- Testing Streaming Generation ---")
        prompt = "Write a simple Python function that adds two numbers."
        print(f"Prompt: {prompt}\nResponse: ", end="")
        
        full_response = ""
        for chunk in client.generate_stream(prompt):
            print(chunk, end="", flush=True)
            full_response += chunk
        
        print("\n\n--- Streaming Complete ---")

if __name__ == "__main__":
    main()