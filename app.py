from flask import Flask, render_template, request
import subprocess
import re
import time

app = Flask(__name__)


# Friendly names for popular services
SERVICE_NAMES = {
    "spotify.com": "Spotify",
    "twitter.com": "Twitter",
    "x.com": "X",
    "github.com": "GitHub",
    "wordpress.com": "WordPress",
    "eventbrite.com": "Eventbrite",
    "office365.com": "Microsoft 365",
    "microsoft.com": "Microsoft",
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "linkedin.com": "LinkedIn",
    "reddit.com": "Reddit",
    "pinterest.com": "Pinterest",
    "tiktok.com": "TikTok",
    "snapchat.com": "Snapchat",
    "telegram.org": "Telegram",
    "discord.com": "Discord",
}


def get_service_name(domain):
    domain = domain.lower().strip()

    if domain in SERVICE_NAMES:
        return SERVICE_NAMES[domain]

    # Convert example.com → Example
    name = domain.split(".")[0]
    return name.replace("-", " ").replace("_", " ").title()


def parse_holehe_output(output):
    results = []

    for line in output.splitlines():

        line = line.strip()

        # Found
        match = re.match(r"^\[\+\]\s+(.+)$", line)

        if match:
            domain = match.group(1).strip()

            # Ignore non-domain informational lines
            if "." not in domain:
                continue

            results.append({
                "domain": domain,
                "name": get_service_name(domain),
                "status": "found"
            })

            continue

        # Not found
        match = re.match(r"^\[-\]\s+(.+)$", line)

        if match:
            domain = match.group(1).strip()

            if "." not in domain:
                continue

            results.append({
                "domain": domain,
                "name": get_service_name(domain),
                "status": "not_found"
            })

            continue

        # Rate limited
        match = re.match(r"^\[x\]\s+(.+)$", line)

        if match:
            domain = match.group(1).strip()

            if "." not in domain:
                continue

            results.append({
                "domain": domain,
                "name": get_service_name(domain),
                "status": "rate_limited"
            })

    return results


@app.route("/", methods=["GET", "POST"])
def index():

    results = []
    email = ""
    scan_time = None

    if request.method == "POST":

        email = request.form.get("email", "").strip()

        if email:

            start_time = time.time()

            try:

                process = subprocess.run(
                    [
                        "holehe",
                        email,
                        "--no-color",
                        "--no-clear"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                output = process.stdout

                results = parse_holehe_output(output)

                scan_time = round(time.time() - start_time, 1)

            except subprocess.TimeoutExpired:

                results = [{
                    "domain": "",
                    "name": "Scan timed out",
                    "status": "rate_limited"
                }]

            except Exception as e:

                results = [{
                    "domain": "",
                    "name": f"Error: {str(e)}",
                    "status": "rate_limited"
                }]

    found = [r for r in results if r["status"] == "found"]
    not_found = [r for r in results if r["status"] == "not_found"]
    rate_limited = [r for r in results if r["status"] == "rate_limited"]

    total_checked = len(results)

    return render_template(
        "index.html",
        email=email,
        results=results,
        found=found,
        not_found=not_found,
        rate_limited=rate_limited,
        total_checked=total_checked,
        scan_time=scan_time
    )


if __name__ == "__main__":
    app.run(debug=True)