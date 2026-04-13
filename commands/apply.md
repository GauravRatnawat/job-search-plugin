Apply to a job: $ARGUMENTS

The argument should be a tracker job ID or a direct URL.

**Step 1: Inspect the target**
```bash
job-apply inspect <job_id_or_url>
```

Show the user the inspection result: whether it's supported, what mode (email draft vs Greenhouse), what fields are needed.

**Step 2: Confirm with the user**

If the target is an email application:
- Tell the user an `.eml` draft will be created locally (NOT sent). No confirmation needed.
- Ask if they want to proceed.

If the target is a Greenhouse application:
- Show the form fields that will be filled.
- List any unsupported required fields.
- Tell the user this will make a REAL submission. Ask for explicit confirmation.

If the target is blocked (LinkedIn/Indeed) or unsupported:
- Tell the user auto-apply is not available for this platform.
- The script automatically opens the job URL in the user's default browser.
- The candidate's cached profile (name, email, phone, location) is copied to the clipboard so they can paste it into the application form.
- Let the user know their info is on the clipboard and the page is open.

**Step 3: Execute (only after user confirms)**

For email:
```bash
job-apply apply <target> --name "<name>" --email "<email>" --phone "<phone>" --resume <path>
```

For Greenhouse (requires explicit confirmation):
```bash
job-apply apply <target> --name "<name>" --email "<email>" --phone "<phone>" --resume <path> --consent --confirm
```

The user must provide their name, email, phone, and resume path. If any are missing, ask for them. NEVER guess contact information.

**Rules:**
- NEVER submit without explicit user confirmation
- NEVER auto-apply to LinkedIn or Indeed
- Email targets create local `.eml` drafts only
- On successful Greenhouse submission, update the tracker to Applied
