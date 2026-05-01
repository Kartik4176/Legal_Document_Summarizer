from django.shortcuts import render
from .bert_model import generate_summary
import PyPDF2
import docx


def home(request):
    return render(request, "index.html")


def summarize(request):

    text = ""

    if request.method == "POST":

        text = request.POST.get("text", "")
        uploaded_file = request.FILES.get("pdf")

        if uploaded_file:

            filename = uploaded_file.name.lower()

            # -------- PDF --------
            if filename.endswith(".pdf"):

                reader = PyPDF2.PdfReader(uploaded_file)

                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted

            # -------- DOCX --------
            elif filename.endswith(".docx"):

                document = docx.Document(uploaded_file)

                for para in document.paragraphs:
                    text += para.text

        print("TEXT LENGTH:", len(text))

        if not text.strip():
            summary = "⚠ No readable text found in the document."
        else:
            summary = generate_summary(text)

        return render(request, "index.html", {"summary": summary})

    return render(request, "index.html")