import pandas as pd

df = pd.read_csv('notes/mtsamples.csv')
df.columns = [c.lower().strip() for c in df.columns]

picks = [320, 168, 43, 12, 1757, 19, 3200, 62, 174, 179]

with open('notes/mtsamples_10.txt', 'w', encoding='utf-8') as f:
    for i, idx in enumerate(picks, 1):
        row = df.iloc[idx]
        f.write(f'--- Note {i} ---\n')
        f.write(row['transcription'].strip())
        f.write('\n\n')

print('Done. notes/mtsamples_10.txt written.')
