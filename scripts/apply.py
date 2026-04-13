#!/usr/bin/env python3
"""Application helper with confirmation gating and source restrictions.

Usage:
    python scripts/apply.py inspect <job_id_or_url> [--email-to hr@example.com]
    python scripts/apply.py apply <job_id_or_url> --name "Jane Doe" --email jane@example.com \
        --phone "+49..." --resume /path/resume.pdf [--cover-letter /path/cover_letter.pdf] \
        [--location "Berlin, Germany"] [--linkedin https://...] [--website https://...] \
        [--email-to hr@example.com] [--subject "..."] [--body "..."] [--message "..."] \
        [--consent] [--confirm]
"""

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import uuid
import webbrowser
from dataclasses import dataclass, field
from email.message import EmailMessage
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen

from tracker import get_job_record, update_job_status

BLOCKED_DOMAINS = {
    "linkedin.com",
    "www.linkedin.com",
    "indeed.com",
    "www.indeed.com",
    "indeed.co.in",
    "www.indeed.co.in",
}

GREENHOUSE_HOST_TOKENS = ("greenhouse.io",)
USER_AGENT = "job-search-mcp/apply.py (+https://local.codex)"
DRAFTS_DIR = Path(os.environ.get("APPLICATION_DRAFTS_DIR", "./application_drafts"))
CACHE_SCRIPT = Path(__file__).parent / "cache.py"


def _open_in_browser(url: str) -> bool:
    """Open a URL in the user's default browser. Returns True on success."""
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def _copy_to_clipboard(text: str) -> bool:
    """Copy text to the system clipboard. Returns True on success."""
    try:
        if sys.platform == "darwin":
            subprocess.run(
                ["pbcopy"],
                input=text.encode(),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        elif sys.platform.startswith("linux"):
            for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard"]):
                try:
                    subprocess.run(
                        cmd,
                        input=text.encode(),
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
                except FileNotFoundError:
                    continue
        elif sys.platform == "win32":
            subprocess.run(
                ["clip"],
                input=text.encode(),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
    except Exception:
        pass
    return False


def _load_cached_profile() -> Optional[dict]:
    """Load the active persona's cached profile, if available."""
    if not CACHE_SCRIPT.exists():
        return None
    try:
        out = subprocess.check_output(
            [sys.executable, str(CACHE_SCRIPT), "load", "profile"],
            stderr=subprocess.DEVNULL,
        )
        d = json.loads(out)
        return d.get("data") if d.get("cached") else None
    except Exception:
        return None


def _build_clipboard_text(profile: Optional[dict]) -> str:
    """Build a paste-ready text block from the candidate's cached profile."""
    if not profile:
        return ""
    parts = []
    if profile.get("name"):
        parts.append(f"Name: {profile['name']}")
    if profile.get("email"):
        parts.append(f"Email: {profile['email']}")
    if profile.get("phone"):
        parts.append(f"Phone: {profile['phone']}")
    if profile.get("location"):
        parts.append(f"Location: {profile['location']}")
    if profile.get("linkedin"):
        parts.append(f"LinkedIn: {profile['linkedin']}")
    if profile.get("github"):
        parts.append(f"GitHub: {profile['github']}")
    if profile.get("summary"):
        parts.append(f"\n{profile['summary']}")
    return "\n".join(parts)


@dataclass
class JobTarget:
    target: str
    url: str
    source: str
    job_id: str = ""
    company: str = ""
    title: str = ""
    location: str = ""
    tracker_notes: str = ""


@dataclass
class FormField:
    name: str
    tag: str
    input_type: str = ""
    required: bool = False
    value: str = ""
    options: List[str] = field(default_factory=list)


@dataclass
class HtmlForm:
    action: str
    method: str
    enctype: str
    fields: List[FormField] = field(default_factory=list)


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms: List[HtmlForm] = []
        self._current_form: Optional[HtmlForm] = None
        self._current_select: Optional[FormField] = None

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        if tag == "form":
            self._current_form = HtmlForm(
                action=attr_map.get("action", ""),
                method=attr_map.get("method", "post").lower(),
                enctype=attr_map.get("enctype", "application/x-www-form-urlencoded"),
            )
            self.forms.append(self._current_form)
            return

        if self._current_form is None:
            return

        required = "required" in attr_map or attr_map.get("aria-required") == "true"
        if tag == "input":
            self._current_form.fields.append(
                FormField(
                    name=attr_map.get("name", ""),
                    tag=tag,
                    input_type=attr_map.get("type", "text").lower(),
                    required=required,
                    value=attr_map.get("value", ""),
                )
            )
        elif tag == "textarea":
            self._current_form.fields.append(
                FormField(
                    name=attr_map.get("name", ""),
                    tag=tag,
                    required=required,
                )
            )
        elif tag == "select":
            self._current_select = FormField(
                name=attr_map.get("name", ""),
                tag=tag,
                required=required,
            )
            self._current_form.fields.append(self._current_select)
        elif tag == "option" and self._current_select is not None:
            self._current_select.options.append(attr_map.get("value", ""))

    def handle_endtag(self, tag):
        if tag == "form":
            self._current_form = None
        elif tag == "select":
            self._current_select = None


def json_print(payload, exit_code=0):
    print(json.dumps(payload, indent=2))
    if exit_code:
        sys.exit(exit_code)


def basename_field(name):
    if not name:
        return ""
    match = re.search(r"\[([^\]]+)\]$", name)
    return match.group(1) if match else name


def is_url(value):
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "mailto"}


def domain_for(url):
    return urlparse(url).netloc.lower()


def is_blocked_url(url):
    host = domain_for(url)
    return any(
        host == blocked or host.endswith(f".{blocked}") for blocked in BLOCKED_DOMAINS
    )


def is_greenhouse_url(url):
    if "gh_jid=" in url:
        return True
    host = domain_for(url)
    return any(token in host for token in GREENHOUSE_HOST_TOKENS)


def classify_target(url, email_to=""):
    if email_to or url.startswith("mailto:"):
        return "email"
    if is_blocked_url(url):
        return "blocked"
    if is_greenhouse_url(url):
        return "greenhouse"
    return "unsupported"


def resolve_target(raw_target, email_to=""):
    if is_url(raw_target):
        return JobTarget(
            target=raw_target,
            url=raw_target,
            source=classify_target(raw_target, email_to),
        )

    record = get_job_record(raw_target)
    if record is None:
        raise ValueError(
            f"Could not resolve '{raw_target}' as a URL or tracker job ID."
        )

    return JobTarget(
        target=raw_target,
        job_id=raw_target,
        url=str(record.get("URL", "") or ""),
        source=classify_target(str(record.get("URL", "") or ""), email_to),
        company=str(record.get("Company", "") or ""),
        title=str(record.get("Title", "") or ""),
        location=str(record.get("Location", "") or ""),
        tracker_notes=str(record.get("Notes", "") or ""),
    )


def split_name(full_name):
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def candidate_value(field_name, args):
    key = basename_field(field_name).lower()
    first_name, last_name = split_name(args.name)
    mapping = {
        "first_name": first_name,
        "last_name": last_name,
        "name": args.name,
        "full_name": args.name,
        "email": args.email,
        "phone": args.phone,
        "location": args.location,
        "city": args.location,
        "linkedin": args.linkedin,
        "website": args.website,
        "portfolio": args.website,
        "github": args.website,
        "current_company": args.current_company,
    }
    return mapping.get(key, "")


def parse_mailto(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return {
        "to": parsed.path,
        "subject": params.get("subject", [""])[0],
        "body": params.get("body", [""])[0],
    }


def default_email_subject(target, args):
    if args.subject:
        return args.subject
    if target.title and target.company:
        return f"Application for {target.title} - {args.name}"
    return f"Job application - {args.name}"


def default_email_body(target, args):
    if args.body:
        return args.body
    role = target.title or "the role"
    company = target.company or "your"
    lines = [
        f"Hello {company} team,",
        "",
        f"I am applying for {role}. My resume is attached for review.",
    ]
    if args.message:
        lines.extend(["", args.message.strip()])
    lines.extend(["", "Best regards,", args.name])
    return "\n".join(lines)


def _safe_resolve(file_path):
    """Resolve a file path and block sensitive system paths."""
    path = Path(file_path).expanduser().resolve()
    blocked = (
        "/etc",
        "/private/etc",
        "/var",
        "/private/var",
        "/sys",
        "/proc",
        "/dev",
    )
    if any(str(path).startswith(b) for b in blocked):
        raise ValueError(f"Access to system path blocked: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file or does not exist: {path}")
    return path


def add_attachment(message, file_path):
    path = _safe_resolve(file_path)
    mime_type, _ = mimetypes.guess_type(path.name)
    maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
    with path.open("rb") as handle:
        message.add_attachment(
            handle.read(), maintype=maintype, subtype=subtype, filename=path.name
        )


def _sanitize_header_value(value):
    """Remove characters that could inject MIME headers."""
    return re.sub(r'[\r\n"\\]', "", str(value))


def encode_multipart(fields, files):
    boundary = f"----jobsearch{uuid.uuid4().hex}"
    parts = []
    for name, value in fields:
        safe_name = _sanitize_header_value(name)
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{safe_name}"\r\n\r\n'.encode()
        )
        parts.append(str(value).encode())
        parts.append(b"\r\n")
    for field_name, file_name, content_type, data in files:
        safe_field = _sanitize_header_value(field_name)
        safe_file = _sanitize_header_value(file_name)
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{safe_field}"; filename="{safe_file}"\r\n'.encode()
        )
        parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        parts.append(data)
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return boundary, b"".join(parts)


def fetch_url(url):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        final_url = response.geturl()
        if urlparse(final_url).scheme not in {"http", "https"}:
            raise ValueError(f"Refusing redirect to non-HTTP URL: {final_url}")
        return response.read().decode("utf-8", errors="replace"), final_url


def select_form(forms):
    for form in forms:
        field_names = {
            basename_field(field.name) for field in form.fields if field.name
        }
        if {"first_name", "email"} & field_names:
            return form
    for form in forms:
        if "/applications" in form.action:
            return form
    return None


def locate_greenhouse_form(url):
    html, final_url = fetch_url(url)
    parser = FormParser()
    parser.feed(html)
    form = select_form(parser.forms)
    if form is not None:
        return form, final_url

    embed_match = re.search(
        r'(https://boards\.greenhouse\.io/embed/job_app\?for=[^"\']+|/embed/job_app\?for=[^"\']+)',
        html,
    )
    if embed_match:
        embed_url = urljoin(final_url, embed_match.group(1))
        html, final_url = fetch_url(embed_url)
        parser = FormParser()
        parser.feed(html)
        form = select_form(parser.forms)
        if form is not None:
            return form, final_url

    raise ValueError("Could not locate a Greenhouse application form on that page.")


def load_file_bytes(path_str):
    path = _safe_resolve(path_str)
    mime_type, _ = mimetypes.guess_type(path.name)
    with path.open("rb") as handle:
        return path.name, mime_type or "application/octet-stream", handle.read()


def prepare_greenhouse_payload(form, args):
    fields = []
    files = []
    unsupported = []

    for field in form.fields:
        if not field.name:
            continue

        key = basename_field(field.name).lower()
        if field.tag == "input" and field.input_type == "hidden":
            fields.append((field.name, field.value))
            continue

        if field.tag == "input" and field.input_type == "file":
            if key == "resume":
                files.append((field.name, *load_file_bytes(args.resume)))
            elif key == "cover_letter" and args.cover_letter:
                files.append((field.name, *load_file_bytes(args.cover_letter)))
            elif field.required:
                unsupported.append(field.name)
            continue

        if field.tag == "input" and field.input_type in {"checkbox", "radio"}:
            if args.consent and any(
                token in key for token in ("consent", "privacy", "terms", "gdpr")
            ):
                fields.append((field.name, field.value or "1"))
            elif field.required:
                unsupported.append(field.name)
            continue

        if field.tag == "textarea":
            if key in {"cover_letter", "message"} and args.message:
                fields.append((field.name, args.message))
            elif field.required:
                unsupported.append(field.name)
            continue

        if field.tag == "select":
            if field.required:
                unsupported.append(field.name)
            continue

        value = candidate_value(field.name, args)
        if value:
            fields.append((field.name, value))
        elif field.required:
            unsupported.append(field.name)

    return fields, files, sorted(set(unsupported))


def tracker_note(prefix, target, detail):
    source = f"{prefix}: {detail}"
    if target.url:
        return f"{source} ({target.url})"
    return source


def slugify(value):
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "application"


def inspect_target(target, args):
    result = {
        "target": target.target,
        "job_id": target.job_id,
        "company": target.company,
        "title": target.title,
        "url": target.url,
        "source": target.source,
        "supported": target.source in {"email", "greenhouse"},
        "blocked": target.source == "blocked",
    }

    if target.source == "blocked":
        result["reason"] = "Auto-apply is blocked for LinkedIn and Indeed."
        result["action"] = "Opening in browser so you can apply manually."
        # Load profile and pre-fill clipboard
        profile = _load_cached_profile()
        clip_text = _build_clipboard_text(profile)
        result["browser_opened"] = _open_in_browser(target.url)
        if clip_text:
            result["clipboard_copied"] = _copy_to_clipboard(clip_text)
            result["clipboard_content"] = clip_text
        return result

    if target.source == "unsupported":
        result["reason"] = "Only email-based applications and Greenhouse are supported."
        result["action"] = "Opening in browser so you can apply manually."
        profile = _load_cached_profile()
        clip_text = _build_clipboard_text(profile)
        result["browser_opened"] = _open_in_browser(target.url)
        if clip_text:
            result["clipboard_copied"] = _copy_to_clipboard(clip_text)
            result["clipboard_content"] = clip_text
        return result

    if target.source == "email":
        mailto = parse_mailto(target.url) if target.url.startswith("mailto:") else {}
        result["mode"] = "email_draft"
        result["to"] = args.email_to or mailto.get("to", "")
        result["draft_only"] = True
        result["requires_confirmation"] = False
        return result

    form, final_url = locate_greenhouse_form(target.url)
    field_names = [basename_field(field.name) for field in form.fields if field.name]
    result["mode"] = "greenhouse"
    result["form_url"] = final_url
    result["form_action"] = urljoin(final_url, form.action or final_url)
    result["fields"] = field_names
    result["requires_confirmation"] = True
    return result


def draft_output_path(target):
    label = target.job_id or f"{target.company}-{target.title}" or target.target
    filename = f"{slugify(label)}-{uuid.uuid4().hex[:8]}.eml"
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    return DRAFTS_DIR / filename


def build_email_message(target, recipient, args):
    message = EmailMessage()
    message["To"] = recipient
    message["From"] = args.email
    message["Subject"] = default_email_subject(target, args)
    message.set_content(default_email_body(target, args))
    add_attachment(message, args.resume)
    if args.cover_letter:
        add_attachment(message, args.cover_letter)
    return message


def run_email_apply(target, args):
    mailto = parse_mailto(target.url) if target.url.startswith("mailto:") else {}
    recipient = args.email_to or mailto.get("to", "")
    if not recipient:
        raise ValueError("Email target requires --email-to or a mailto: URL.")

    message = build_email_message(target, recipient, args)
    output_path = draft_output_path(target)
    output_path.write_bytes(message.as_bytes())

    return {
        "mode": "email_draft",
        "status": "drafted",
        "to": recipient,
        "subject": message["Subject"],
        "body": default_email_body(target, args),
        "attachments": [args.resume]
        + ([args.cover_letter] if args.cover_letter else []),
        "draft_path": str(output_path),
        "submitted": False,
        "requires_confirmation": False,
    }


def run_greenhouse_apply(target, args):
    if not args.resume:
        raise ValueError("Greenhouse applications require --resume.")

    form, final_url = locate_greenhouse_form(target.url)
    fields, files, unsupported = prepare_greenhouse_payload(form, args)
    form_action = urljoin(final_url, form.action or final_url)
    preview = {
        "mode": "greenhouse",
        "form_url": final_url,
        "form_action": form_action,
        "field_count": len(fields),
        "file_fields": [name for name, _, _, _ in files],
        "unsupported_required_fields": unsupported,
        "requires_confirmation": True,
    }

    if unsupported:
        preview["status"] = "blocked"
        preview["reason"] = (
            "The Greenhouse form has required fields this script cannot fill automatically."
        )
        return preview

    if not args.confirm:
        preview["status"] = "preview"
        return preview

    if not args.consent:
        raise ValueError(
            "Greenhouse submission requires --consent because privacy checkboxes may be mandatory."
        )

    boundary, body = encode_multipart(fields, files)
    request = Request(
        form_action,
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Referer": final_url,
        },
        method=form.method.upper() or "POST",
    )
    with urlopen(request, timeout=30) as response:
        response_body = response.read().decode("utf-8", errors="replace")
        response_url = response.geturl()
        status_code = getattr(response, "status", response.getcode())

    tracker_result = None
    if target.job_id:
        tracker_result = update_job_status(
            target.job_id,
            "Applied",
            tracker_note(
                "Applied via Greenhouse helper", target, f"HTTP {status_code}"
            ),
        )

    return {
        "mode": "greenhouse",
        "status": "submitted",
        "http_status": status_code,
        "response_url": response_url,
        "response_excerpt": response_body[:300],
        "tracker_update": tracker_result,
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Job application helper")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("inspect", "apply"):
        subparser = sub.add_parser(name, help=f"{name.title()} a job target")
        subparser.add_argument(
            "target", help="Tracker job ID, job URL, or mailto target"
        )
        subparser.add_argument(
            "--email-to", default="", help="Recipient for email-based applications"
        )
        subparser.add_argument("--name", default="", help="Candidate full name")
        subparser.add_argument("--email", default="", help="Candidate email address")
        subparser.add_argument("--phone", default="", help="Candidate phone number")
        subparser.add_argument("--location", default="", help="Candidate location")
        subparser.add_argument("--linkedin", default="", help="Candidate LinkedIn URL")
        subparser.add_argument(
            "--website", default="", help="Candidate website or portfolio"
        )
        subparser.add_argument(
            "--current-company",
            default="",
            help="Current company if the form asks for it",
        )
        subparser.add_argument("--resume", default="", help="Path to resume file")
        subparser.add_argument(
            "--cover-letter", default="", help="Path to cover letter file"
        )
        subparser.add_argument("--subject", default="", help="Email subject override")
        subparser.add_argument("--body", default="", help="Email body override")
        subparser.add_argument(
            "--message", default="", help="Extra application message"
        )
        subparser.add_argument(
            "--consent", action="store_true", help="Confirm privacy/consent checkboxes"
        )
        subparser.add_argument(
            "--confirm",
            action="store_true",
            help="Required only for real submissions such as Greenhouse. Email targets generate local drafts.",
        )
    return parser


def validate_args(args, target):
    if args.command == "inspect":
        return
    if target.source in {"blocked", "unsupported"}:
        return
    if not args.resume:
        raise ValueError("--resume is required for apply.")
    if not args.name:
        raise ValueError("--name is required for apply.")
    if not args.email:
        raise ValueError("--email is required for apply.")
    if target.source == "greenhouse" and not args.phone:
        raise ValueError("--phone is required for Greenhouse applications.")


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        target = resolve_target(args.target, args.email_to)
        validate_args(args, target)

        if args.command == "inspect":
            json_print(inspect_target(target, args))
            return

        if target.source == "blocked":
            profile = _load_cached_profile()
            clip_text = _build_clipboard_text(profile)
            result = {
                "error": "Auto-apply is blocked for LinkedIn and Indeed.",
                "url": target.url,
                "action": "Opening in browser so you can apply manually.",
                "browser_opened": _open_in_browser(target.url),
            }
            if clip_text:
                result["clipboard_copied"] = _copy_to_clipboard(clip_text)
                result["clipboard_content"] = clip_text
            json_print(result, exit_code=1)
            return
        if target.source == "unsupported":
            profile = _load_cached_profile()
            clip_text = _build_clipboard_text(profile)
            result = {
                "error": "Only email-based applications and Greenhouse are supported.",
                "url": target.url,
                "action": "Opening in browser so you can apply manually.",
                "browser_opened": _open_in_browser(target.url),
            }
            if clip_text:
                result["clipboard_copied"] = _copy_to_clipboard(clip_text)
                result["clipboard_content"] = clip_text
            json_print(result, exit_code=1)
            return

        if target.source == "email":
            json_print(run_email_apply(target, args))
            return

        if target.source == "greenhouse":
            json_print(run_greenhouse_apply(target, args))
            return

        json_print({"error": f"Unhandled target source: {target.source}"}, exit_code=1)
    except (ValueError, KeyError) as exc:
        json_print({"error": str(exc)}, exit_code=1)
    except HTTPError as exc:
        json_print({"error": f"HTTP error {exc.code}: {exc.reason}"}, exit_code=1)
    except URLError as exc:
        json_print({"error": f"Network error: {exc.reason}"}, exit_code=1)


if __name__ == "__main__":
    main()
