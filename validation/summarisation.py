import csv
import os
from textblob import TextBlob

# Function to calculate lexical density
def lexical_density(text):
    blob = TextBlob(text)
    # Extracting content words (NOUN, VERB, ADJ, ADV) using POS tags
    content_words = [word for word, pos in blob.tags if pos in ['NN', 'VB', 'JJ', 'RB']]
    return len(content_words) / len(blob.words) if len(blob.words) > 0 else 0

# Function to calculate the length of the summary
def length_score(summary):
    return len(summary.split())

# Function to calculate the compression ratio
def compression_ratio(summary, original_length=250):
    return length_score(summary) / original_length if original_length > 0 else 0

# Function to get the previous average score from CSV
def get_previous_avg(CSV_FILE):
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        return None
    with open(CSV_FILE, "r", newline='', encoding="utf-8") as f:
        last = list(csv.DictReader(f))[-1]
        return float(last["Average_Score"])

# Function to evaluate the summary
def evaluate_summary(iteration, command, summary, CSV_FILE="results/summary_eval.csv", ORIGINAL_LENGTH=250):
    lex_density = lexical_density(summary)
    length = length_score(summary)
    comp_ratio = compression_ratio(summary, ORIGINAL_LENGTH)

    avg_score = lex_density

    prev_avg = get_previous_avg(CSV_FILE)
    gain = avg_score - prev_avg if prev_avg is not None else 0.0

    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline='', encoding="utf-8") as csvfile:
        fieldnames = [
            "Iteration", "Command", "Summary",
            "Lexical_Density", "Length", "Compression_Ratio",
            "Average_Score", "Gain"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists or os.stat(CSV_FILE).st_size == 0:
            writer.writeheader()
        writer.writerow({
            "Iteration": iteration,
            "Command": command,
            "Summary": summary,
            "Lexical_Density": round(lex_density, 4),
            "Length": length,
            "Compression_Ratio": round(comp_ratio, 4),
            "Average_Score": round(avg_score, 4),
            "Gain": round(gain, 4)
        })

    print(f"Iteration {iteration} evaluated. Gain: {gain:.4f}")


