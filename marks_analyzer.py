import pandas as pd

def process_and_analyze_marks(marks_data: list, criteria: dict, max_marks_per_subject: int):
    df = pd.DataFrame(marks_data)
    
    subject_cols = list(criteria.keys())
    for col in subject_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Total'] = df[subject_cols].sum(axis=1)
    df['Percentage'] = (df['Total'] / (len(subject_cols) * max_marks_per_subject)) * 100

    is_eligible = pd.Series([True] * len(df), index=df.index)
    for subject, min_mark in criteria.items():
        if subject in df.columns:
            is_eligible &= (df[subject] >= min_mark)
    
    df['Eligible'] = is_eligible.map({True: 'Yes', False: 'No'})
    df['Rank'] = df['Percentage'].rank(method='min', ascending=False).astype(int)
    df = df.sort_values('Rank')

    return {
        "eligible_students": df[df['Eligible'] == 'Yes'].to_dict('records'),
        "non_eligible_students": df[df['Eligible'] == 'No'].to_dict('records'),
        "top_5_students": df.head(5).to_dict('records'),
        "bottom_5_students": df.tail(5).sort_values('Rank').to_dict('records'),
        "full_ranked_list": df.to_dict('records'),
    }