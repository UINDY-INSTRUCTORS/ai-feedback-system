import os
from google.cloud import aiplatform_v1
from google.api_core.exceptions import NotFound

# Setup
PROJECT_ID = "gen-lang-client-0318362096"
REGION = "us-central1"

print(f"--- Scanning for Active Gemini Models in {REGION} ---")

# Initialize the client pointing specifically to your region
client = aiplatform_v1.ModelGardenServiceClient(
    client_options={"api_endpoint": f"{REGION}-aiplatform.googleapis.com"}
)

# The base families we want to track over the summer
families = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3.1-flash",
    "gemini-3.1-pro"
]

# The version suffixes Google typically uses
versions = ["", "-001", "-002", "-preview"]

print(f"{'MODEL ID FOR MODELS.JSON':<50} | {'STATUS'}")
print("-" * 65)

for family in families:
    for version in versions:
        model_id = f"{family}{version}"
        target_name = f"publishers/google/models/{model_id}"
        
        try:
            # We use GET because LIST doesn't exist!
            # If the model exists in the region, this succeeds.
            client.get_publisher_model(name=target_name)
            print(f"{target_name:<50} | ✅ ACTIVE")
            
        except NotFound:
            # Model doesn't exist, isn't released yet, or was removed
            pass
        except Exception as e:
            # Catching quota issues or other unexpected errors
            print(f"{target_name:<50} | ⚠️ ERROR ({type(e).__name__})")

print("\nTip: In August, choose IDs ending in '-001' or '-002' for your syllabus.")