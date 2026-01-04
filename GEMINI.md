# Investment Analysis Project Memories

## Workflow: Investment Analysis
- When the user types the phrase `investment analysis` (or similar trigger within this context), perform the following sequence:
  1. Execute `mkdir -p /home/pi/WorkDir/investment_analysis/report && cd /home/pi/WorkDir/investment_analysis/report && python3 ../investment_analysis.py` to generate the HTML report in the report directory.
  2. Read the generated HTML file from `/home/pi/WorkDir/investment_analysis/report/`.
  3. Generate technical analysis based on the indicators in the file.
  4. Collect 20 important global economic news items (verified) with titles and summaries.
  5. Append the technical analysis and news to the HTML file (same font size, left-aligned).
  6. Execute `git add report/ && git commit -m "Update analysis report" && git push` to upload the changes to GitHub.
