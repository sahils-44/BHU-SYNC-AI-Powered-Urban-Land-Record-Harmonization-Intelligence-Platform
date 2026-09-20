def calculate_quality_score(df):

    if len(df) == 0:
        return 0

    total_cells = df.shape[0] * df.shape[1]

    missing_cells = df.isna().sum().sum()

    quality_score = (
        (total_cells - missing_cells)
        / total_cells
    ) * 100

    return round(quality_score, 2)