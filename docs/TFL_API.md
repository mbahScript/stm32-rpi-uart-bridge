
---

# 📄 docs/TFL_API.md

```markdown
# TfL API Reference (v0.4.0)

Base URL:
https://api.tfl.gov.uk

Authentication:
Use `app_key` query parameter.

Example:
https://api.tfl.gov.uk/Line/Mode/tube/Status?app_key=YOUR_KEY

Endpoints Used:

## Tube Status
GET /Line/Mode/tube/Status

## StopPoint Arrivals
GET /StopPoint/{id}/Arrivals

Note:
StopPoint arrivals work for individual stops only.