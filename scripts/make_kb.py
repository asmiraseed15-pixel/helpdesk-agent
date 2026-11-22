
from pathlib import Path
import re

KB_DIR = Path("data/kb")  # ingest reads from this folder

# (title, category, keywords, severity, symptoms, steps, tool_actions, escalate)
P = [
("VPN not connecting", "Network", "vpn, connect aagala, remote access", "Medium",
 "VPN client shows an error or keeps loading.",
 ["Check that normal internet works.", "Quit the VPN client and sign in again.",
  "Switch the protocol to TCP in settings.", "Restart the laptop and retry."],
 ['check_service_status("vpn")', 'reset_vpn_profile(user_id)'],
 ["Still failing after restart.", "The same issue affects multiple users."]),

("Forgot password", "Account", "forgot password, password marandhuten, reset", "Low",
 "User cannot remember the password.",
 ["Open the self-service reset page.", "Verify with the code sent to your phone.",
  "Choose a new password with 12+ characters.", "Sign in again on all devices."],
 ['reset_password_request(user_id)'],
 ["User has no access to the registered phone or email.", "Reset link is not received after 15 minutes."]),

("Laptop running slow", "Hardware", "slow, laptop slow, hang, romba slow", "Low",
 "Apps open slowly and the fan is loud.",
 ["Close unused apps and browser tabs.", "End high-CPU tasks in Task Manager.",
  "Free disk space until usage is below 85%.", "Restart and install pending updates."],
 ['run_cleanup_script(user_id)'],
 ["Still slow even after cleanup."]),

("Outlook not opening", "Email", "outlook, mail open aagala, email", "Medium",
 "Outlook crashes or stays on the loading screen.",
 ["Start Outlook in safe mode.", "Disable add-ins one by one.",
  "Repair the Office installation.", "Create a new mail profile."],
 ['repair_office(user_id)'],
 ["Mailbox data is corrupted or emails are missing.", "Outlook still fails after a new profile."]),

("Wi-Fi connected but no internet", "Network", "wifi, no internet, internet illa", "Medium",
 "Wi-Fi shows connected but pages do not load.",
 ["Toggle Wi-Fi off and on.", "Forget the network and reconnect.",
  "Run: ipconfig /release then ipconfig /renew.", "Restart the router or try another network."],
 ['check_service_status("wifi")'],
 ["Other devices also cannot connect (router or access point issue)."]),

("Printer not printing", "Hardware", "printer, print aagala, print stuck", "Low",
 "Print jobs stay in the queue.",
 ["Check power, paper and cable or Wi-Fi.", "Clear the print queue.",
  "Restart the Print Spooler service.", "Remove and re-add the printer."],
 ['check_service_status("print_spooler")', 'clear_print_queue(printer_id)'],
 ["Printer shows a hardware error (paper jam, toner, display error).", "Nobody in the office can print."]),

("Account locked out", "Account", "locked, account lock, too many attempts", "Medium",
 "Sign-in fails with an account locked message.",
 ["Wait 15 minutes for auto-unlock.", "Use self-service unlock if available.",
  "Confirm caps lock is off and retry.", "Reset the password if still locked."],
 ['unlock_account(user_id)'],
 ["Repeated lockouts without user attempts (possible attack)."]),

("Blue screen error (BSOD)", "Hardware", "blue screen, bsod, crash, restart", "High",
 "Laptop shows a blue screen and restarts.",
 ["Note the stop code on the screen.", "Remove newly connected USB devices.",
  "Boot into safe mode and uninstall recent updates or drivers.", "Run: sfc /scannow."],
 ['collect_crash_logs(device_id)'],
 ["Blue screen repeats more than twice."]),

("Software installation request", "Software", "install, software request, need app", "Low",
 "User needs an approved application installed.",
 ["Check the approved software list.", "Open the company software portal.",
  "Request the app and wait for approval.", "Install it from the portal."],
 ['create_install_request(user_id, app_name)'],
 ["Software is not on the approved list (needs security approval).", "Admin rights or a paid license is required."]),

("No audio or microphone in meetings", "Software", "mic, no sound, teams audio, zoom audio", "Low",
 "Others cannot hear you or you cannot hear them.",
 ["Select the right mic and speaker in the meeting app.", "Check Windows sound settings and unmute.",
  "Allow microphone access in Privacy settings.", "Restart the app or reconnect the headset."],
 ['run_audio_check(device_id)'],
 ["The audio device is not detected at all."]),

("Disk space full", "Hardware", "disk full, storage full, c drive", "Low",
 "Low disk space warning or failed saves.",
 ["Empty the Recycle Bin.", "Run Disk Cleanup.",
  "Uninstall unused programs.", "Move large files to cloud storage."],
 ['run_cleanup_script(user_id)'],
 ["Space is still low after cleanup."]),

("Email not syncing on phone", "Email", "phone mail, sync, mobile email", "Low",
 "New mails do not appear on the phone.",
 ["Check mobile data or Wi-Fi.", "Confirm sync is turned on for mail.",
  "Remove and add the account again.", "Update the mail app."],
 ['reenable_mail_sync(user_id)'],
 ["Password was changed recently and sync still fails."]),

("Shared drive access denied", "Access", "shared drive, access denied, permission, folder", "Medium",
 "Access denied when opening a network folder.",
 ["Confirm you are on the company network or VPN.", "Re-map the network drive.",
  "Sign out and sign in again.", "Request access from the folder owner."],
 ['create_access_request(user_id, folder)'],
 ["Owner approved but access is still denied."]),

("Monitor flickering or no display", "Hardware", "monitor, display, screen flicker, no signal", "Low",
 "Screen flickers or shows no signal.",
 ["Check cable connections at both ends.", "Try another cable or port.",
  "Lower the refresh rate in display settings.", "Update the graphics driver."],
 ['open_driver_update(device_id)'],
 ["Flicker continues on another monitor."]),

("Keyboard or mouse not working", "Hardware", "keyboard, mouse, not working, usb", "Low",
 "Keys or cursor do not respond.",
 ["Replace batteries or recharge wireless devices.", "Unplug and reconnect, or try another USB port.",
  "Restart the laptop.", "Test on another computer."],
 ['create_replacement_request(user_id, device)'],
 ["The built-in laptop keyboard fails."]),

("Suspicious or phishing email", "Security", "phishing, suspicious email, spam, scam", "High",
 "Email asks for passwords or contains odd links.",
 ["Do not click links or open attachments.", "Report it using the Report Phishing button.",
  "Delete the email.", "If you clicked, change your password immediately."],
 ['quarantine_email(message_id)'],
 ["User entered credentials or opened a file."]),

("Browser slow or crashing", "Software", "browser, chrome, slow browser, crash", "Low",
 "Pages load slowly or the browser closes.",
 ["Close extra tabs.", "Clear cache and cookies.",
  "Disable extensions.", "Update or reinstall the browser."],
 ['clear_browser_data(user_id)'],
 ["The problem happens in every browser."]),

("Two-factor code not received", "Security", "otp, 2fa, mfa, code not coming", "Medium",
 "SMS or app code does not arrive.",
 ["Check phone signal and the correct number.", "Wait 60 seconds and request a new code.",
  "Check the time on your phone is set to automatic.", "Use a backup code or another method."],
 ['reset_mfa_method(user_id)'],
 ["Phone is lost or the number has changed."]),

("Laptop battery draining fast", "Hardware", "battery, drain, charging, battery low", "Low",
 "Battery drops quickly or does not charge.",
 ["Check the charger and cable.", "Lower screen brightness and enable battery saver.",
  "Check which apps use the most battery in Settings.", "Run: powercfg /batteryreport."],
 ['generate_battery_report(device_id)'],
 ["Battery health is below 60%."]),

("Windows update stuck", "Software", "update stuck, windows update, installing updates", "Medium",
 "Update is stuck at a percentage.",
 ["Wait at least 30 minutes.", "Restart the laptop.",
  "Run the Windows Update troubleshooter.", "Free disk space and retry."],
 ['run_update_troubleshooter(device_id)'],
 ["Update fails again with the same error code."]),
]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def main():
    KB_DIR.mkdir(parents=True, exist_ok=True)
    for title, cat, kw, sev, sym, steps, actions, esc in P:
        actions = actions + [f'create_ticket(category="{cat}")']
        body = (
            f"# {title}\n"
            f"Category: {cat}\n"
            f"Keywords: {kw}\n"
            f"Severity: {sev}\n\n"
            f"## Symptoms\n{sym}\n\n"
            f"## Troubleshooting Steps\n"
            + "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
            + "\n\n## Permitted Actions\n"
            + "\n".join(f"- {a}" for a in actions)
            + "\n\n## When to Escalate\n"
            + "\n".join(f"- {e}" for e in esc)
            + "\n"
        )
        (KB_DIR / f"{slug(title)}.md").write_text(body, encoding="utf-8")
    print(f"Created {len(P)} articles in {KB_DIR}")


if __name__ == "__main__":
    main()