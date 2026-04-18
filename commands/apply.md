---
description: Help apply to a job — provide the direct URL, show profile details for copy-paste, or draft an email application
allowed-tools: Read, Write, Glob
---

Help the user apply to a job: $ARGUMENTS

The argument should be a tracker job ID or a direct URL.

**Step 1: Look up the job**

If the argument is a job ID, read `job_tracker.json` and find the matching job to get its URL, company, and title.

If the argument is a URL, use it directly.

**Step 2: Determine the application method**

Check the URL domain:
- **LinkedIn** (`linkedin.com`) or **Indeed** (`indeed.com`): These platforms block automated applications. Give the user the direct link and tell them to apply manually.
- **Greenhouse** (`greenhouse.io`): Tell the user to visit the link and apply directly. Greenhouse has its own application form.
- **Company career page** or **other ATS**: Give the user the direct link.
- **Email** (`mailto:` URL or user provides an email): Draft an email for the user (see below).

**Step 3: For all web-based applications**

1. Provide the direct application URL to the user
2. If a cached profile exists (`.cache/<persona>/profile.json`), offer to show the user their key details for copy-pasting:
   - Name, email, phone, location, LinkedIn URL
3. Suggest they use `/tailor-resume` and `/cover-letter` for this specific role before applying

**Step 4: For email applications**

If the user wants to apply via email:
1. Ask for: recipient email, their name, email, phone, and resume path
2. Draft the email body as a text file saved to `application_drafts/<company>-<role>.txt`
3. Include: greeting, role they're applying for, brief pitch, closing
4. Tell the user to send it themselves with their resume attached
5. NEVER send emails — only create local drafts

**Step 5: Update the tracker**

After the user confirms they've applied:
1. Read `job_tracker.json`
2. Update the job's status to "Applied"
3. Set `date_applied` to today
4. Add notes about how they applied
5. Write back to `job_tracker.json`

**Rules:**
- NEVER submit applications on behalf of the user
- NEVER auto-apply to LinkedIn or Indeed
- Email applications create local draft files only
- Always confirm with the user before updating the tracker status
