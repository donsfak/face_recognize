from database.client import supabase

def log_attendance(user_name: str, liveness_status: str, confidence_score: float):
    """Enregistre un nouveau passage dans la base de données."""
    data = {
        "user_name": user_name,
        "liveness_status": liveness_status,
        "confidence_score": confidence_score
    }
    # Supabase s'occupe de générer l'ID et le timestamp automatiquement
    response = supabase.table("attendance_logs").insert(data).execute()
    return response.data

def get_recent_logs(limit: int = 10):
    """Récupère les derniers logs pour alimenter le Dashboard."""
    response = supabase.table("attendance_logs").select("*").order("timestamp", desc=True).limit(limit).execute()
    return response.data
