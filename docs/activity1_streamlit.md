# Activity 1: Build the Streamlit Interface

In this activity, you'll convert the paper analyzer CLI into a Streamlit web app. The workflow code stays the same from A7 — you're building a new **interface** on top of it.

## Background

In A7, you built a LangGraph workflow that analyzes academic papers via the command line. Now you'll create a web interface using Streamlit that:

- Lets users enter a paper URL or DOI in a text input
- Runs the same LangGraph workflow when they click "Analyze"
- Shows real-time progress as each workflow node executes
- Displays the results: summary, metadata, links, and warnings

**Key Streamlit concepts** (from the slides):

| Concept | What it does | Example |
|---------|-------------|---------|
| `st.text_input()` | Creates a text field | `url = st.text_input("URL")` |
| `st.button()` | Creates a clickable button | `if st.button("Go"):` |
| `st.warning()` | Shows a yellow alert box | `st.warning("No URL entered")` |
| `st.status()` | Shows a collapsible progress container | `with st.status("Working..."):` |
| `st.write()` | Displays text or data | `st.write("Processing...")` |
| `st.subheader()` | Displays a sub-heading | `st.subheader("Results")` |
| `st.markdown()` | Renders markdown text | `st.markdown(summary)` |
| `st.expander()` | Creates a collapsible section | `with st.expander("Details"):` |
| `st.columns()` | Creates side-by-side columns | `c1, c2 = st.columns(2)` |
| `st.metric()` | Shows a label + value pair | `st.metric("Year", 2017)` |
| `pipeline.stream()` | Streams workflow updates | `for event in pipeline.stream(state):` |

## Before You Start

Make sure your A7 workflow still works:

```bash
# Verify the workflow runs
python -m ai_in_loop.cli analyze "https://arxiv.org/abs/1706.03762"

# Run the A7 tests to confirm
pytest tests/test_paper_starter.py tests/test_paper_full.py -q
```

## Implementation Steps

Open `app.py` and fill in the 7 gaps marked with `YOUR CODE HERE`.

**Tip:** The Links section in `app.py` is provided as a completed example. Study it to see how to get values from `final_state` and conditionally display them — Steps 5 and 6 follow a similar pattern.

### Step 1: Text Input (1 line)

Create a `st.text_input()` widget for the user to enter a paper URL or DOI. Use a placeholder showing an example arXiv URL. Store the result in the variable `url`.

**Slides reference:** Look for the `st.text_input()` example in the Streamlit slides.

### Step 2: Analyze Button (1 line)

Create a `st.button()` labeled "Analyze" and store the result in `analyze_clicked`.

**Slides reference:** Look for the `st.button()` example.

### Step 3: Empty URL Warning (1 line)

When the user clicks Analyze with an empty URL, show a warning using `st.warning()` with a helpful message.

**Slides reference:** Look for the `st.warning()` example.

### Checkpoint

After completing Steps 1-3, run the starter tests:

```bash
pytest tests/test_app_starter.py -v
```

All 5 tests should pass. If they don't, check that:
- Your `st.text_input()` is creating a widget (not just a string)
- Your `st.button()` returns a boolean
- Your `st.warning()` is inside the `if not url.strip():` block

### Step 4: Streaming Workflow Progress (~7 lines)

This is the core step. You'll use `st.status()` to show a progress container and `pipeline.stream()` to run the workflow with real-time updates.

**Slides reference:** Find the "Streaming node progress" slide that combines `st.status()` with `pipeline.stream()`. Adapt that pattern here.

**One thing to change from the slides:** The slides display the raw node name (`f"Completed: **{node_name}**"`), but names like `fetch_metadata_apis` aren't user-friendly. The scaffolding provides a `NODE_LABELS` dict that maps node names to readable messages like "Fetching metadata from APIs...". Use `NODE_LABELS.get(node_name, node_name)` in place of the formatted string — the second argument is a fallback in case a node isn't in the dict.

### Step 5: Summary Display (~4 lines)

Display the paper summary with a "Summary" heading using `st.subheader()` and the summary text using `st.markdown()`. Get the summary from `final_state` and only display it if the value exists. The general pattern for conditionally displaying a result looks like:

```python
value = final_state.get("some_key")
if value:
    # display it
```

`st.subheader("Some Heading")` works like `st.markdown("## Some Heading")` — it creates a section heading. See also the completed Links section in `app.py` for an example of this get-and-display pattern.

### Step 6: Metadata Expander with Metrics (~8-10 lines)

Show paper metadata inside an expandable section with column-based metrics. The scaffolding comments describe exactly which metrics to display and what data to show below them.

**Slides reference:** Look for the "Displaying structured results" slide that combines `st.expander()`, `st.columns()`, and `st.metric()`. The slides show columns and metrics outside the expander — here you'll put them inside it. The slides also show 2 columns; you'll need 3.

### Step 7: Warning Display (~3 lines)

Loop over any workflow warnings from `final_state` and display each one using `st.warning()`. The general pattern for displaying a list of items looks like:

```python
for item in final_state.get("some_list", []):
    # display item
```

### Final Checkpoint

Run all tests:

```bash
# Starter tests (Steps 1-3)
pytest tests/test_app_starter.py -v

# Full tests (Steps 1-7)
pytest tests/test_app.py -v
```

All tests should pass. You can also run the app to see it working:

```bash
streamlit run app.py
```

---

## Your Implementation Notes

### What Streamlit widgets did you use for each step?

st.text_input
st.button
st.warning 
st.write
st.subheader
st.markdown
st.expeander
st.columns

### How does streaming with pipeline.stream() differ from pipeline.invoke()?

pipeline.stream will return each node as we are processing pipleline.invoke will just return everything at the end instead.

### What happens in the UI when you enter an invalid URL? Describe the user experience.

three text bar poped out to tell what is causing error to user.

### Were there any steps you found particularly challenging? Why?

Not really, most of them can find reference from the slides

---

## Verification

```bash
# All Streamlit tests
pytest tests/test_app_starter.py tests/test_app.py -v

# Submission check
python tests/verify_submission.py
```
