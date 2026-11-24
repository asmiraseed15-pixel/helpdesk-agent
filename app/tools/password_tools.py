from pathlib import Path

KB_DIR = Path("data/kb")

FALLBACK = """Password reset guide:
1. Click 'Forgot password' on the login page.
2. Enter your company email ID to get a reset link.
3. Set a new strong password (12+ characters).
4. If the link does not arrive, check the spam folder, or create a ticket."""


def reset_password_guide() -> dict:
    """Return the password reset steps. This only gives guidance; it never resets a password itself."""
    f = KB_DIR / "forgot-password.md"
    text = f.read_text(encoding="utf-8-sig") if f.exists() else FALLBACK
    return {
        "guide": text,
        "note": "Identity verification (OTP) is required before any real password reset.",
    }
