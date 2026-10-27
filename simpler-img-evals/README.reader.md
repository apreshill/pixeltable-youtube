# Reader brief: Image Evals Are Simpler Than You Think

Covers the video, `README.md`, and `demo.ipynb`. From `profiles/pixeltable/users.md`.

## 1. Reader

**The small team shipping an AI product on media.** Their product generates or edits images (ads, mockups, product shots, try-ons), and a coding agent writes much of the code. Grading the outputs isn't the reason they picked a backend. This video is the first time they see that it fits in the one they already have.

## 2. Their moment

Frame it with OpenAI's [image evals cookbook](https://developers.openai.com/cookbook/examples/multimodal/image_evals), a real source the reader can check. Never use an invented story: nobody resonates with one, and it's easy to wave off ("that's not us").

- OpenAI wrote down how they grade generated and edited images: hard gates first, then 0 to 5 scores, then failure tags. The method is sound, and the reader agrees with it.
- To run it, OpenAI built a custom harness: three packages that call the image model, save the images, and run the judge. That is the reader's moment: to use the method, you'd build and keep a second system next to your app, one that pulls the images out, grades them, and stores the scores somewhere else.
- One thing is true of the work and hard to argue with: image models fail quietly. A bad image looks like a good one until someone reads it.

The cookbook is the frame, not the subject. Open on what it means for the reader ("OpenAI published how they grade images, and running it means building their harness next to your app"), not on what the cookbook or the notebook contains (reader-POV finding 2).

From users.md: "Nothing errors. The results just quietly get worse." (context) and "You add a new step, and now you need a backfill script for every file you already have." (T6). The judge is that new step, and grading every image you already have is the backfill.

## 3. What they stop doing

The usual answer is an eval script that lives outside the app. It pulls the images out, calls a judge model on each one, saves the scores somewhere else, and has to be kept in step with the app every time the app changes. To re-grade after a rubric change, people often rerun the generation too.

What goes away:
- the separate eval script, and the second place the scores live
- keeping that script in step with the app
- paying for new images to get a new grade

Where Pixeltable enters, after the moment: the grade is one more step in the table the images already live in. It runs on every new image, and it fills in for every image already there. Change the rubric, and only the grade reruns.

**Takeaway: T6,** "Add a new AI result, and every row you already have gets it." The payoff is the positioning's maintain line: one schema you keep, not a stack you assemble. Say it as what's there and what goes away ("the grade sits next to the image"; "no eval script to keep in step with the app"). Don't write it as "not another thing bolted on, not another system": that is the not-X contrast the humanizer review flags.

**Don't name customers.** If the draft says others already work this way, it's "teams building on Pixeltable already grade their outputs this way", nothing more specific.

## 4. The comment it hopes for

- The line they'd quote back: "the grade is just another column next to the image."
- Their own case: "Can I add a second judge model and compare it against the first on the images I already have?"
- The experience they'd add: "We have an eval notebook that nobody reruns after the model changes."
- Who they'd send it to: the teammate who owns the eval script, or the person who picks the image model.
- Reaction: Insightful.

## 5. Words

**Theirs, for this topic:** outputs, the images, a grade or score, the judge (LLM-as-judge), the rubric, pass/fail, the eval script, rerun, backfill, model calls, the bill, the model swap.

**Pixeltable terms the draft keeps, only where the reader acts on them:**

| Term | Where |
|---|---|
| table, `generations`, `edits` | code and `schema.py` |
| computed column | `schema.py`, and the docs link line. Outside code: "a step that runs on every new image and saves its grade next to it" |
| view (`gen_evals`, `edit_evals`) | code. Outside code: "the graded images" |
| `eval_ready` | code. In prose: "mark an image ready, and only then does the judge run, and only then do you pay for it" |
| `recompute_columns` | code. In prose: "re-grade" |

**Words that lose them, outside code:** computed column, view, harness, runner, multimodal backend, declarative, incremental, UDF, lineage.

## What this means for the draft

- Open the README and the notebook on the moment, not on the cookbook, a category, or "the slow part is the runner."
- Show the T6 moment on screen: images that already exist get their grades when the judge column is added or the rows are marked ready, with no new image calls.
- Show a rubric change and a re-grade that makes no image calls (review finding 3).
- To compare models, keep both results, as a second column or new rows. Don't promise "change a constant" (finding 5).
