# Definición de consultas
QUERIES = {
    "last_10_scrobblings": """
        SELECT TOP 10 *
        FROM Clean_LastfmData
    """,
    
    "top_artists": """
        SELECT TOP 10 Artist, COUNT(*) as Scrobblings
        FROM Clean_LastfmData
        GROUP BY Artist
        ORDER BY Scrobblings DESC
    """,
}
