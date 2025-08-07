# Definición de consultas
QUERIES = {
# Default queries
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
# Monthly Queries (Not for aggregations)
    "scrobblings_by_month": """
        SELECT Year_Month, COUNT(*) as Scrobblings
        FROM Clean_LastfmData
        GROUP BY Year_Month
    """,

    "artists_by_month": """
        SELECT Year_Month, COUNT(DISTINCT(Artist)) as Artists
        FROM Clean_LastfmData
        GROUP BY Year_Month
    """,

    "albums_by_month": """
        SELECT Year_Month, COUNT(DISTINCT(Album)) as Albums
        FROM Clean_LastfmData
        GROUP BY Year_Month
    """
}

# Pendiente agregar consultas con funciones de agregación (promedios de las variables)