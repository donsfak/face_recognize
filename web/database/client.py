import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Charge les variables depuis le fichier .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Les identifiants Supabase sont manquants dans le fichier .env")

# Initialisation du client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

