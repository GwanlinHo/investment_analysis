# Investment Analysis Project Memories

## Workflow: Investment Analysis
- When the user types the phrase `investment analysis` (or similar trigger within this context), perform the following sequence:
  1. Execute `cd /home/pi/WorkDir/investment_analysis/report && python3 ../investment_analysis.py` to generate the HTML report in the report directory.
  2. Read the generated HTML file from `/home/pi/WorkDir/investment_analysis/report/`.
  3. Generate analysis using three distinct AI personas:
     - **Technical Analysis Master (ISTP):** Analyze volume/price, support/resistance, divergence, and "Sakata Goho" (酒田戰法) candlestick patterns. Warn of reversals. Be direct.
     - **Value Investing Master (ISTJ):** Evaluate financial history, intrinsic value, safety margin, and profit quality.
     - **Macro & Industry Master (INTJ):** Analyze interest rates, industry cycles, and geopolitical risks.
  4. Collect **15** important news items impacting US/Taiwan economy, FX, and rates. **Must include source links**.
  5. Append the analysis and news to the HTML file (replace the `#text-analysis-report` div).
  6. Execute `git add report/ && git commit -m "Update analysis report" && git push` to upload the changes to GitHub.
