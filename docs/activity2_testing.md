# Activity 2: Testing and Comparison

In this activity, you'll test your Streamlit app with different paper types and compare the web interface with the CLI.

**Before you start:** Make sure Gemini is configured in your `.env` (see README step 3). Without it, every paper will produce the same placeholder summary, making the comparisons below meaningless.

## Test Results

### Test 1: arXiv Paper

Run the app and enter an arXiv URL:
```
https://arxiv.org/abs/1706.03762
```

**What did the streaming progress show? List the workflow steps you saw:**

parsing input URL
fetching metadata from APIs
Searching for open_acess full text
Downloading and extracting PDF text
Generating summary

**Did the summary, metadata, and links all display correctly?**

Yes

### Test 2: DOI Paper

Enter a DOI (try a paper you know has open access):
```
10.1038/nature12373
```

**Did the workflow find open-access full text via Unpaywall?**

Yes

**How did the results compare to the arXiv paper?**

By using doi, the doi was added to the links

### Test 3: Invalid Input

Enter something that isn't a valid URL or DOI:
```
hello world
```

**What warnings appeared? Were they helpful?**

Yes, it tells the user inpout can not be parsed and can not retreieve paper metadata for full text

### Test 4: Empty Input

Click Analyze without entering anything.

**What happened? Was the message clear?**

The message is clear, it tells user to enter a valid input.

---

## CLI vs Web Comparison

Run the same paper through both interfaces:

```bash
# CLI
python -m ai_in_loop.cli analyze "https://arxiv.org/abs/1706.03762" --format json

# Web
streamlit run app.py
# Then enter the same URL in the browser
```

**What information is shown in the web app that isn't in the CLI output?**

analysis workflow details

**What information is in the CLI output that isn't in the web app?**

full_text pdf file link

**Which interface do you prefer for this task? Why?**

I prefer streamlit user interface, the inferface is neat with clear error messages.

---

## Reflection

### What was the most useful Streamlit feature for this project?

APIs for ui design

### How does streaming improve the user experience compared to waiting for the full result?

user can be aware of the process workflow. 

### If you were to add one more feature to the web interface, what would it be?

A analysis history, it store all the url and corresponding summary.
