import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer


# 🔹 Step 1: Clean text (FIXED)
def normalize_text(text):
    text = text.replace('\r', '\n')  # handle PDF weirdness
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()



def chunk_text(text, chunk_size=1000):

    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks





# 🔹 Step 2: Detect headings (multi-pattern)
def detect_headings(text):
    caps = re.findall(r'\n([A-Z][A-Z\s]{5,})\n', text)
    numbered = re.findall(r'\n(\d+\.\s+[A-Za-z ].+)', text)
    title = re.findall(r'\n([A-Z][a-z]+(?:\s(?:[A-Z][a-z]+|and|of|the)){1,6})\n', text)
    all_headings = caps + numbered + title

    seen = set()
    ordered_headings = []

    for h in all_headings:
        if h not in seen:
            seen.add(h)
            ordered_headings.append(h)

    if not ordered_headings:
        ordered_headings = re.findall(r'([A-Z][A-Z\s]{5,})', text)

    # 🔥 ADD THIS LINE
    ordered_headings.sort(key=lambda h: text.find(h))

    return ordered_headings





# 🔹 Step 3: Split text into sections (FIXED ORDER ISSUE)
def split_by_headings(text, headings):
    positions = []

    for heading in headings:
        # find ALL occurrences (not just first)
        for match in re.finditer(re.escape(heading), text):
            positions.append((match.start(), heading))

    # remove duplicates by position
    positions = sorted(set(positions), key=lambda x: x[0])

    # sort by position
    positions.sort()

    sections = []

    for i in range(len(positions)):
        start = positions[i][0]

        if i + 1 < len(positions):
            end = positions[i + 1][0]
        else:
            end = len(text)

        section_text = text[start:end]
        section_heading = positions[i][1]

        # skip very small/noisy sections
        if len(section_text.strip()) > 50:
            sections.append((section_heading, section_text))

    return sections







# 🔹 Step 4: Summarize a section using LSA
def summarize_section(section, sentence_count=2):

    # 🔹 chunk very large sections
    if len(section.split()) > 1200:

        chunks = chunk_text(section, 500)

        chunk_summaries = []

        for chunk in chunks:

            parser = PlaintextParser.from_string(
                chunk,
                Tokenizer("english")
            )

            summarizer = LsaSummarizer()

            summary_sentences = summarizer(
                parser.document,
                2
            )

            for sentence in summary_sentences:
                chunk_summaries.append("• " + str(sentence))

        return "\n".join(chunk_summaries)

    # 🔹 normal summarization
    parser = PlaintextParser.from_string(
        section,
        Tokenizer("english")
    )

    summarizer = LsaSummarizer()

    length = len(section.split())

    if length < 100:
        sentence_count = 1
    elif length < 300:
        sentence_count = 2
    else:
        sentence_count = 3

    summary_sentences = summarizer(
        parser.document,
        sentence_count
    )

    cleaned = []

    for sentence in summary_sentences:

        s = str(sentence).strip()

        if len(s) > 30:
            cleaned.append("• " + s)

    return "\n".join(cleaned)




def merge_summaries(section_summaries):

    seen = set()
    final_output = []

    for heading, summary in section_summaries:

        lines = summary.split("\n")

        cleaned_lines = []

        for line in lines:

            line = line.strip()

            # skip empty lines
            if not line:
                continue

            # remove duplicate points
            if line not in seen:
                seen.add(line)
                cleaned_lines.append(line)

        # skip empty summaries
        if cleaned_lines:

            # 🔹 format heading
            formatted_heading = format_heading(heading)

            # 🔹 classify category
            category = classify_heading(formatted_heading)

            formatted_section = (
                f"\n📂 {category} → {formatted_heading}\n"
                + "\n".join(cleaned_lines)
            )

            final_output.append(formatted_section)

    return "📑 LEGAL DOCUMENT SUMMARY\n" + "\n".join(final_output)








def summarize_without_headings(text):

    chunks = chunk_text(text)

    chunk_summaries = []

    for i, chunk in enumerate(chunks):

        summary = summarize_section(chunk, 2)

        chunk_summaries.append(
            (f"Section {i+1}", summary)
        )

    return merge_summaries(chunk_summaries)






def format_heading(heading):

    heading = heading.strip()

    # remove numbering
    heading = re.sub(r'^\d+\.\s*', '', heading)

    # remove extra spaces
    heading = re.sub(r'\s+', ' ', heading)

    # convert ALL CAPS to Title Case
    if heading.isupper():
        heading = heading.title()

    return heading




def classify_heading(heading):

    h = heading.lower()

    if any(word in h for word in [
        "payment",
        "salary",
        "compensation",
        "benefit"
    ]):
        return "Payment Terms"

    elif any(word in h for word in [
        "confidential",
        "privacy",
        "data"
    ]):
        return "Confidentiality"

    elif any(word in h for word in [
        "termination",
        "obligation",
        "condition",
        "agreement",
        "terms"
    ]):
        return "Obligations"

    else:
        return "General"






# 🔹 Step 5: Main function (FINAL PIPELINE)
def generate_summary(text):

    # 🔹 Step 1: Clean text
    text = normalize_text(text)

    # 🔹 Step 2: Detect headings
    headings = detect_headings(text)

    # 🔹 Fallback if no headings found
    if not headings:
        return summarize_without_headings(text)

    # 🔹 Step 3: Split into sections
    sections = split_by_headings(text, headings)

    # 🔹 Step 4: Summarize each section (MAP PHASE)
    section_summaries = []

    for heading, section in sections:

        # summarize current section
        section_summary = summarize_section(section)

        # store heading + summary
        section_summaries.append(
            (heading.strip(), section_summary)
        )

    # 🔹 Step 5: Merge summaries (REDUCE PHASE)
    final_summary = merge_summaries(section_summaries)

    return final_summary