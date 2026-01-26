# CSV Data Summarizer - Resources

---

## 🌟 Connect & Learn More

<div align="center">

### 🚀 **Join Our Community**
[![Join AI Community](https://img.shields.io/badge/Join-AI%20Community%20(FREE)-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgM2MxLjY2IDAgMyAxLjM0IDMgM3MtMS4zNCAzLTMgMy0zLTEuMzQtMy0zIDEuMzQtMyAzLTN6bTAgMTQuMmMtMi41IDAtNC43MS0xLjI4LTYtMy4yMi4wMy0xLjk5IDQtMy4wOCA2LTMuMDggMS45OSAwIDUuOTcgMS4wOSA2IDMuMDgtMS4yOSAxLjk0LTMuNSAzLjIyLTYgMy4yMnoiLz48L3N2Zz4=)](https://www.skool.com/ai-for-your-business/about)

### 🔗 **All My Links**
[![Link Tree](https://img.shields.io/badge/Linktree-Everything-green?style=for-the-badge&logo=linktree&logoColor=white)](https://linktr.ee/corbin_brown)

### 🛠️ **Become a Builder**
[![YouTube Membership](https://img.shields.io/badge/YouTube-Become%20a%20Builder-red?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/channel/UCJFMlSxcvlZg5yZUYJT0Pug/join)

### 🐦 **Follow on Twitter**
[![Twitter Follow](https://img.shields.io/badge/Twitter-Follow%20@corbin__braun-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/corbin_braun)

</div>

---

## Sample Data

The `sample.csv` file contains example sales data with the following columns:

- **date**: Transaction date
- **product**: Product name (Widget A, B, or C)
- **quantity**: Number of items sold
- **revenue**: Total revenue from the transaction
- **customer_id**: Unique customer identifier
- **region**: Geographic region (North, South, East, West)

## Usage Examples

### Basic Summary
```
Analyze sample.csv
```

### With Custom CSV
```
Here's my sales_data.csv file. Can you summarize it?
```

### Focus on Specific Insights
```
What are the revenue trends in this dataset?
```

## Testing the Skill

You can test the skill locally before uploading to Claude:

```bash
# Install dependencies
pip install -r ../requirements.txt

# Run the analysis
python ../analyze.py sample.csv
```

## Expected Output

The analysis will provide:

1. **Dataset dimensions** - Row and column counts
2. **Column information** - Names and data types
3. **Summary statistics** - Mean, median, std dev, min/max for numeric columns
4. **Data quality** - Missing value detection and counts
5. **Visualizations** - Time-series plots when date columns are present

## Customization

To adapt this skill for your specific use case:

1. Modify `analyze.py` to include domain-specific calculations
2. Add custom visualization types in the plotting section
3. Include validation rules specific to your data
4. Add more sample datasets to test different scenarios

