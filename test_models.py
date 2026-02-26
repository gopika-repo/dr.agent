import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ No GEMINI_API_KEY found in environment variables")
    print("Please set GEMINI_API_KEY in your .env file")
    exit(1)

# Configure Gemini
genai.configure(api_key=api_key)

print("=" * 60)
print("🤖 CHECKING AVAILABLE GEMINI MODELS")
print("=" * 60)

# List all available models
try:
    print("\n📋 Fetching all models...")
    models = list(genai.list_models())  # Convert generator to list
    
    print(f"\n✅ Found {len(models)} total models")
    
    # Filter and display only generative models
    print("\n" + "=" * 60)
    print("🎯 GENERATIVE MODELS (can generate content):")
    print("=" * 60)
    
    generative_models = []
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            generative_models.append(model)
            
    print(f"\nFound {len(generative_models)} generative models:")
    print("-" * 40)
    
    for i, model in enumerate(generative_models, 1):
        print(f"\n{i}. {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        print(f"   Input Token Limit: {model.input_token_limit}")
        print(f"   Output Token Limit: {model.output_token_limit}")
        print(f"   Supported Methods: {', '.join(model.supported_generation_methods)}")
    
    # Also show popular models to try
    print("\n" + "=" * 60)
    print("🔧 POPULAR MODELS TO TRY (based on naming patterns):")
    print("=" * 60)
    
    popular_models = [
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-2.0-pro",
        "gemini-1.0-pro",
        "gemini-1.0-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-pro",
        "gemini-pro-vision",
        "models/gemini-1.5-pro",
        "models/gemini-1.5-flash",
    ]
    
    print("\nTry these model names in your app:")
    for model_name in popular_models:
        print(f"  • '{model_name}'")
    
    # Test a specific model
    print("\n" + "=" * 60)
    print("🧪 TESTING MODEL CONNECTIONS:")
    print("=" * 60)
    
    test_models = [
        "models/gemini-1.5-flash",
        "gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "gemini-1.5-pro",
        "gemini-pro",
        "models/gemini-pro",
        "gemini-1.0-pro",
        "models/gemini-1.0-pro",
        "gemini-1.0-flash",
        "models/gemini-1.0-flash",
        "gemini-2.0-pro",
        "models/gemini-2.0-pro",
        "gemini-2.0-flash",
        "models/gemini-2.0-flash",
        "gemini-2.5-pro",
        "models/gemini-2.5-pro",
        "gemini-2.5-flash",
        "models/gemini-2.5-flash",
    ]
    
    for test_model in test_models:
        try:
            print(f"\nTesting '{test_model}'...")
            model = genai.GenerativeModel(test_model)
            # Just test if we can create the model object
            print(f"  ✅ Model object created successfully")
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower() or "404" in error_msg:
                print(f"  ❌ Model not found")
            else:
                print(f"  ❌ Error: {error_msg[:100]}")
    
    # Quick generation test with the first working model
    print("\n" + "=" * 60)
    print("🚀 QUICK GENERATION TEST:")
    print("=" * 60)
    
    # Try to generate content with first generative model
    if generative_models:
        first_model = generative_models[0]
        print(f"\nTrying to generate content with: {first_model.name}")
        try:
            model = genai.GenerativeModel(first_model.name)
            response = model.generate_content("Say 'Hello, Gemini is working!'")
            print(f"  ✅ Generation successful!")
            print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  ❌ Generation failed: {str(e)[:100]}")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    print("\n⚠️ Possible issues:")
    print("1. Invalid API key")
    print("2. API key doesn't have access to Gemini")
    print("3. Network issues")
    print("4. Region restrictions")
    print("\n🔍 Debug info:")
    print(f"   API Key starts with: {api_key[:10]}...")
    print(f"   Error type: {type(e).__name__}")