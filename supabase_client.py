from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("https://qtpjctlrxoeeqchifyiz.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF0cGpjdGxyeG9lZXFjaGlmeWl6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc2MzU1MDYsImV4cCI6MjA2MzIxMTUwNn0.jaVyzrfo88VQZoSdHj0yGWtMxJdhRuUX5I_RqO5Y8CU")

def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)
